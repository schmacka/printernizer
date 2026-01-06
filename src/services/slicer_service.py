"""
Slicer service for managing slicer configurations and profiles.

Handles slicer detection, profile import, and slicing operations.
"""
import sqlite3
import uuid
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import structlog

from src.database.database import Database
from src.services.base_service import BaseService
from src.services.event_service import EventService
from src.services.slicer_detector import SlicerDetector
from src.models.slicer import (
    SlicerType,
    SlicerConfig,
    SlicerProfile,
    ProfileType,
)
from src.utils.exceptions import NotFoundError
from src.utils.config import get_settings

logger = structlog.get_logger()


class SlicerService(BaseService):
    """
    Service for managing slicer configurations and profiles.

    Responsibilities:
    - Detect slicer installations
    - Manage slicer configurations
    - Import and manage profiles
    - Validate slicer availability
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService
    ):
        """
        Initialize slicer service.

        Args:
            database: Database instance
            event_service: Event service for notifications
        """
        super().__init__(database)
        self.event_service = event_service
        self.detector = SlicerDetector()
        self.settings = get_settings()

    async def initialize(self) -> None:
        """Initialize service and detect slicers."""
        await super().initialize()
        
        logger.info("Initializing slicer service")
        
        # Auto-detect slicers if enabled
        auto_detect = await self._get_setting("slicing.auto_detect", True)
        if auto_detect:
            await self.detect_and_register_slicers()

    async def detect_and_register_slicers(self) -> List[SlicerConfig]:
        """
        Detect and register available slicers.

        Returns:
            List of registered slicer configurations
        """
        logger.info("Detecting slicers")
        detected = self.detector.detect_all()
        
        registered = []
        for slicer_data in detected:
            try:
                slicer = await self.register_slicer(slicer_data)
                registered.append(slicer)
            except Exception as e:
                logger.error(
                    "Failed to register slicer",
                    slicer_type=slicer_data.get("slicer_type"),
                    error=str(e)
                )

        logger.info("Slicer detection completed", count=len(registered))
        await self.event_service.emit_event("slicer.detected", {"count": len(registered)})
        
        return registered

    async def register_slicer(self, slicer_data: Dict) -> SlicerConfig:
        """
        Register a slicer configuration.

        Args:
            slicer_data: Slicer configuration data

        Returns:
            Registered slicer configuration
        """
        slicer_id = str(uuid.uuid4())
        now = datetime.now()

        async with self.db.connection() as conn:
            await conn.execute(
                """
                INSERT INTO slicer_configs (
                    id, name, slicer_type, executable_path, version, config_dir,
                    is_available, last_verified, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slicer_id,
                    slicer_data["name"],
                    slicer_data["slicer_type"],
                    slicer_data["executable_path"],
                    slicer_data.get("version"),
                    slicer_data.get("config_dir"),
                    True,
                    now,
                    now,
                    now,
                ),
            )
            await conn.commit()

        logger.info(
            "Registered slicer",
            slicer_id=slicer_id,
            name=slicer_data["name"],
            version=slicer_data.get("version")
        )

        return await self.get_slicer(slicer_id)

    async def get_slicer(self, slicer_id: str) -> SlicerConfig:
        """
        Get slicer configuration by ID.

        Args:
            slicer_id: Slicer configuration ID

        Returns:
            Slicer configuration

        Raises:
            NotFoundError: If slicer not found
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM slicer_configs WHERE id = ?",
                (slicer_id,)
            )
            row = await cursor.fetchone()

        if not row:
            raise NotFoundError("Slicer", slicer_id)

        return self._row_to_slicer_config(row)

    async def list_slicers(self, available_only: bool = False) -> List[SlicerConfig]:
        """
        List all slicer configurations.

        Args:
            available_only: Only return available slicers

        Returns:
            List of slicer configurations
        """
        query = "SELECT * FROM slicer_configs"
        if available_only:
            query += " WHERE is_available = 1"
        query += " ORDER BY name"

        async with self.db.connection() as conn:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()

        return [self._row_to_slicer_config(row) for row in rows]

    async def update_slicer(self, slicer_id: str, updates: Dict[str, Any]) -> SlicerConfig:
        """
        Update slicer configuration.

        Args:
            slicer_id: Slicer configuration ID
            updates: Fields to update

        Returns:
            Updated slicer configuration
        """
        allowed_fields = {"name", "executable_path", "version", "config_dir", "is_available"}
        updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not updates:
            return await self.get_slicer(slicer_id)

        updates["updated_at"] = datetime.now()
        
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values())
        values.append(slicer_id)

        async with self.db.connection() as conn:
            await conn.execute(
                f"UPDATE slicer_configs SET {set_clause} WHERE id = ?",
                values
            )
            await conn.commit()

        logger.info("Updated slicer", slicer_id=slicer_id, updates=list(updates.keys()))
        return await self.get_slicer(slicer_id)

    async def delete_slicer(self, slicer_id: str) -> bool:
        """
        Delete slicer configuration.

        Args:
            slicer_id: Slicer configuration ID

        Returns:
            True if deleted
        """
        async with self.db.connection() as conn:
            await conn.execute(
                "DELETE FROM slicer_configs WHERE id = ?",
                (slicer_id,)
            )
            await conn.commit()

        logger.info("Deleted slicer", slicer_id=slicer_id)
        return True

    async def import_profiles(self, slicer_id: str) -> List[SlicerProfile]:
        """
        Import profiles from slicer config directory.

        Args:
            slicer_id: Slicer configuration ID

        Returns:
            List of imported profiles
        """
        slicer = await self.get_slicer(slicer_id)
        
        if not slicer.config_dir:
            logger.warning("No config directory for slicer", slicer_id=slicer_id)
            return []

        config_path = Path(slicer.config_dir)
        if not config_path.exists():
            logger.warning(
                "Config directory not found",
                slicer_id=slicer_id,
                path=str(config_path)
            )
            return []

        imported = []
        
        # Import print profiles
        print_profiles = self._scan_profiles(config_path, ProfileType.PRINT)
        for profile_data in print_profiles:
            try:
                profile = await self.create_profile(slicer_id, profile_data)
                imported.append(profile)
            except Exception as e:
                logger.error(
                    "Failed to import profile",
                    profile=profile_data.get("profile_name"),
                    error=str(e)
                )

        logger.info(
            "Imported profiles",
            slicer_id=slicer_id,
            count=len(imported)
        )
        
        return imported

    def _scan_profiles(self, config_path: Path, profile_type: ProfileType) -> List[Dict]:
        """
        Scan config directory for profiles.

        Args:
            config_path: Path to slicer config directory
            profile_type: Type of profiles to scan

        Returns:
            List of profile data dictionaries
        """
        profiles = []
        
        # Look for .ini files in print, filament, printer directories
        profile_dir = config_path / profile_type.value
        if not profile_dir.exists():
            return profiles

        for profile_file in profile_dir.glob("*.ini"):
            profiles.append({
                "profile_name": profile_file.stem,
                "profile_type": profile_type.value,
                "profile_path": str(profile_file),
            })

        return profiles

    async def create_profile(self, slicer_id: str, profile_data: Dict) -> SlicerProfile:
        """
        Create a slicer profile.

        Args:
            slicer_id: Slicer configuration ID
            profile_data: Profile data

        Returns:
            Created profile
        """
        profile_id = str(uuid.uuid4())
        now = datetime.now()

        async with self.db.connection() as conn:
            await conn.execute(
                """
                INSERT INTO slicer_profiles (
                    id, slicer_id, profile_name, profile_type, profile_path,
                    settings_json, compatible_printers, is_default, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    slicer_id,
                    profile_data["profile_name"],
                    profile_data["profile_type"],
                    profile_data.get("profile_path"),
                    profile_data.get("settings_json"),
                    profile_data.get("compatible_printers"),
                    profile_data.get("is_default", False),
                    now,
                    now,
                ),
            )
            await conn.commit()

        return await self.get_profile(profile_id)

    async def get_profile(self, profile_id: str) -> SlicerProfile:
        """
        Get profile by ID.

        Args:
            profile_id: Profile ID

        Returns:
            Profile configuration

        Raises:
            NotFoundError: If profile not found
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM slicer_profiles WHERE id = ?",
                (profile_id,)
            )
            row = await cursor.fetchone()

        if not row:
            raise NotFoundError("Profile", profile_id)

        return self._row_to_profile(row)

    async def list_profiles(
        self,
        slicer_id: Optional[str] = None,
        profile_type: Optional[ProfileType] = None
    ) -> List[SlicerProfile]:
        """
        List profiles.

        Args:
            slicer_id: Filter by slicer ID
            profile_type: Filter by profile type

        Returns:
            List of profiles
        """
        query = "SELECT * FROM slicer_profiles WHERE 1=1"
        params = []

        if slicer_id:
            query += " AND slicer_id = ?"
            params.append(slicer_id)

        if profile_type:
            query += " AND profile_type = ?"
            params.append(profile_type.value)

        query += " ORDER BY profile_name"

        async with self.db.connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        return [self._row_to_profile(row) for row in rows]

    async def delete_profile(self, profile_id: str) -> bool:
        """
        Delete profile.

        Args:
            profile_id: Profile ID

        Returns:
            True if deleted
        """
        async with self.db.connection() as conn:
            await conn.execute(
                "DELETE FROM slicer_profiles WHERE id = ?",
                (profile_id,)
            )
            await conn.commit()

        logger.info("Deleted profile", profile_id=profile_id)
        return True

    async def verify_slicer_availability(self, slicer_id: str) -> bool:
        """
        Verify slicer is still available.

        Args:
            slicer_id: Slicer configuration ID

        Returns:
            True if available
        """
        slicer = await self.get_slicer(slicer_id)
        is_valid, error = self.detector.verify_slicer(slicer.executable_path)
        
        if is_valid != slicer.is_available:
            await self.update_slicer(
                slicer_id,
                {
                    "is_available": is_valid,
                    "last_verified": datetime.now()
                }
            )

        if not is_valid:
            logger.warning(
                "Slicer not available",
                slicer_id=slicer_id,
                error=error
            )

        return is_valid

    async def _get_setting(self, key: str, default: Any) -> Any:
        """Get setting from database or return default."""
        try:
            async with self.db.connection() as conn:
                cursor = await conn.execute(
                    "SELECT value, value_type FROM configuration WHERE key = ?",
                    (key,)
                )
                row = await cursor.fetchone()
        except (sqlite3.OperationalError, Exception) as e:
            if "no such table" in str(e).lower():
                logger.debug(f"Configuration table not found, using default for {key}")
                return default
            # Log unexpected errors but don't crash - use default
            logger.warning(f"Error reading setting {key}: {e}, using default")
            return default

        if not row:
            return default

        value, value_type = row

        if value_type == "boolean":
            return value.lower() in ("true", "1", "yes")
        elif value_type == "integer":
            return int(value)
        elif value_type == "float":
            return float(value)
        else:
            return value

    def _row_to_slicer_config(self, row) -> SlicerConfig:
        """Convert database row to SlicerConfig."""
        return SlicerConfig(
            id=row[0],
            name=row[1],
            slicer_type=row[2],
            executable_path=row[3],
            version=row[4],
            config_dir=row[5],
            is_available=bool(row[6]),
            last_verified=datetime.fromisoformat(row[7]) if row[7] else None,
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9]),
        )

    def _row_to_profile(self, row) -> SlicerProfile:
        """Convert database row to SlicerProfile."""
        return SlicerProfile(
            id=row[0],
            slicer_id=row[1],
            profile_name=row[2],
            profile_type=row[3],
            profile_path=row[4],
            settings_json=row[5],
            compatible_printers=row[6],
            is_default=bool(row[7]),
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9]),
        )
