"""
Database service for managing watch folders.
Handles CRUD operations for persistent watch folder storage.
"""

import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

import structlog
from src.database.database import Database
from src.models.watch_folder import WatchFolder, WatchFolderSource

logger = structlog.get_logger()


class WatchFolderDbService:
    """Database service for watch folder operations."""
    
    def __init__(self, database: Database = None):
        """Initialize the database service."""
        self.database = database
    
    async def create_watch_folder(self, watch_folder: WatchFolder) -> int:
        """Create a new watch folder in database."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            async with conn.execute("""
                INSERT INTO watch_folders (
                    folder_path, is_active, recursive, folder_name, 
                    description, file_count, last_scan_at, is_valid,
                    validation_error, last_validation_at, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                watch_folder.folder_path,
                watch_folder.is_active,
                watch_folder.recursive,
                watch_folder.folder_name,
                watch_folder.description,
                watch_folder.file_count,
                watch_folder.last_scan_at.isoformat() if watch_folder.last_scan_at else None,
                watch_folder.is_valid,
                watch_folder.validation_error,
                watch_folder.last_validation_at.isoformat() if watch_folder.last_validation_at else None,
                watch_folder.source.value
            )) as cursor:
                folder_id = cursor.lastrowid
            
            await conn.commit()
            
            logger.info("Created watch folder in database", 
                      folder_id=folder_id, folder_path=watch_folder.folder_path)
            return folder_id
                
        except sqlite3.IntegrityError as e:
            logger.error("Watch folder already exists", 
                       folder_path=watch_folder.folder_path, error=str(e))
            raise ValueError(f"Watch folder already exists: {watch_folder.folder_path}")
        except Exception as e:
            logger.error("Failed to create watch folder", 
                       folder_path=watch_folder.folder_path, error=str(e))
            raise
    
    async def get_watch_folder_by_id(self, folder_id: int) -> Optional[WatchFolder]:
        """Get watch folder by ID."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            async with conn.execute("SELECT * FROM watch_folders WHERE id = ?", (folder_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return WatchFolder.from_db_row(row)
                return None
                
        except Exception as e:
            logger.error("Failed to get watch folder by id", folder_id=folder_id, error=str(e))
            raise
    
    async def get_watch_folder_by_path(self, folder_path: str) -> Optional[WatchFolder]:
        """Get watch folder by path."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            async with conn.execute("SELECT * FROM watch_folders WHERE folder_path = ?", (folder_path,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return WatchFolder.from_db_row(row)
                return None
                
        except Exception as e:
            logger.error("Failed to get watch folder by path", folder_path=folder_path, error=str(e))
            raise
    
    async def get_all_watch_folders(self, active_only: bool = False) -> List[WatchFolder]:
        """Get all watch folders."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            
            if active_only:
                query = "SELECT * FROM watch_folders WHERE is_active = 1 ORDER BY created_at"
            else:
                query = "SELECT * FROM watch_folders ORDER BY created_at"
            
            async with conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [WatchFolder.from_db_row(row) for row in rows]
                
        except Exception as e:
            logger.error("Failed to get watch folders", error=str(e))
            raise
    
    async def update_watch_folder(self, folder_id: int, updates: Dict[str, Any]) -> bool:
        """Update watch folder fields."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            if not updates:
                return True
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key in ['folder_path', 'folder_name', 'description', 'validation_error', 'source']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                elif key in ['is_active', 'recursive', 'is_valid']:
                    set_clauses.append(f"{key} = ?")
                    values.append(bool(value))
                elif key == 'file_count':
                    set_clauses.append(f"{key} = ?")
                    values.append(int(value))
                elif key in ['last_scan_at', 'last_validation_at']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value.isoformat() if isinstance(value, datetime) else value)
            
            if not set_clauses:
                return True
            
            values.append(folder_id)
            
            conn = self.database.get_connection()
            query = f"UPDATE watch_folders SET {', '.join(set_clauses)} WHERE id = ?"
            async with conn.execute(query, values) as cursor:
                updated = cursor.rowcount > 0
            
            await conn.commit()
            
            if updated:
                logger.info("Updated watch folder", folder_id=folder_id, updates=list(updates.keys()))
            
            return updated
                
        except Exception as e:
            logger.error("Failed to update watch folder", folder_id=folder_id, error=str(e))
            raise
    
    async def delete_watch_folder(self, folder_id: int) -> bool:
        """Delete watch folder from database."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            async with conn.execute("DELETE FROM watch_folders WHERE id = ?", (folder_id,)) as cursor:
                deleted = cursor.rowcount > 0
            
            await conn.commit()
            
            if deleted:
                logger.info("Deleted watch folder", folder_id=folder_id)
            
            return deleted
                
        except Exception as e:
            logger.error("Failed to delete watch folder", folder_id=folder_id, error=str(e))
            raise
    
    async def delete_watch_folder_by_path(self, folder_path: str) -> bool:
        """Delete watch folder by path."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            async with conn.execute("DELETE FROM watch_folders WHERE folder_path = ?", (folder_path,)) as cursor:
                deleted = cursor.rowcount > 0
            
            await conn.commit()
            
            if deleted:
                logger.info("Deleted watch folder by path", folder_path=folder_path)
            
            return deleted
                
        except Exception as e:
            logger.error("Failed to delete watch folder by path", folder_path=folder_path, error=str(e))
            raise
    
    async def get_active_folder_paths(self) -> List[str]:
        """Get list of active watch folder paths."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            async with conn.execute("SELECT folder_path FROM watch_folders WHERE is_active = 1 ORDER BY created_at") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
                
        except Exception as e:
            logger.error("Failed to get active folder paths", error=str(e))
            raise
    
    async def update_folder_statistics(self, folder_path: str, file_count: int) -> bool:
        """Update folder file count and last scan time."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            now = datetime.now()
            conn = self.database.get_connection()
            async with conn.execute("""
                UPDATE watch_folders 
                SET file_count = ?, last_scan_at = ?
                WHERE folder_path = ?
            """, (file_count, now.isoformat(), folder_path)) as cursor:
                updated = cursor.rowcount > 0
            
            await conn.commit()
            return updated
                
        except Exception as e:
            logger.error("Failed to update folder statistics", 
                       folder_path=folder_path, error=str(e))
            raise
    
    async def validate_and_update_folder(self, folder_path: str, is_valid: bool, 
                                       error_message: Optional[str] = None) -> bool:
        """Update folder validation status."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            now = datetime.now()
            conn = self.database.get_connection()
            async with conn.execute("""
                UPDATE watch_folders 
                SET is_valid = ?, validation_error = ?, last_validation_at = ?
                WHERE folder_path = ?
            """, (is_valid, error_message, now.isoformat(), folder_path)) as cursor:
                updated = cursor.rowcount > 0
            
            await conn.commit()
            return updated
                
        except Exception as e:
            logger.error("Failed to update folder validation", 
                       folder_path=folder_path, error=str(e))
            raise
    
    async def migrate_env_folders(self, folder_paths: List[str]) -> int:
        """Migrate folders from environment variables to database."""
        try:
            migrated_count = 0
            
            for folder_path in folder_paths:
                # Check if folder already exists
                existing = await self.get_watch_folder_by_path(folder_path)
                if existing:
                    logger.debug("Folder already exists in database", folder_path=folder_path)
                    continue
                
                # Create folder with migration source
                watch_folder = WatchFolder(
                    folder_path=folder_path,
                    source=WatchFolderSource.ENV_MIGRATION,
                    folder_name=Path(folder_path).name
                )
                
                try:
                    await self.create_watch_folder(watch_folder)
                    migrated_count += 1
                    logger.info("Migrated env folder to database", folder_path=folder_path)
                except ValueError:
                    # Folder already exists, skip
                    continue
            
            logger.info("Completed env folder migration", migrated_count=migrated_count)
            return migrated_count
            
        except Exception as e:
            logger.error("Failed to migrate env folders", error=str(e))
            raise