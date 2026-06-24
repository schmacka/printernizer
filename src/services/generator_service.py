"""
Generator service.

Geometry is generated in the browser (JSCAD), so the server side is intentionally
small: it stores named parameter presets and accepts a finished STL to hand off to
the Library. No CAD engine runs on the server (this is what lets the feature work
on any architecture, including Raspberry Pi / aarch64).
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from src.database.repositories import GeneratorRepository
from src.models.generator import GeneratorStatus, Preset
from src.utils.config import get_settings
from src.utils.errors import GeneratorError

logger = structlog.get_logger(__name__)


class GeneratorService:
    """Stores presets and saves browser-generated STLs into the Library."""

    def __init__(self, database, event_service, library_service=None):
        self.database = database
        self.event_service = event_service
        self.library_service = library_service
        self.repo = GeneratorRepository(database._connection)

        settings = get_settings()
        self.staging_dir = Path(settings.generator_output_dir) / "staging"
        self._dirs_ready = False

    async def initialize(self) -> None:
        """Best-effort staging dir; never crash startup if it isn't writable."""
        try:
            self.staging_dir.mkdir(parents=True, exist_ok=True)
            self._dirs_ready = True
        except OSError as e:
            self._dirs_ready = False
            logger.warning("Generator staging dir not writable; save-to-library disabled",
                           staging_dir=str(self.staging_dir), error=str(e))
        logger.info("Generator service initialized (browser-side engine)",
                    staging_writable=self._dirs_ready)

    def get_status(self) -> GeneratorStatus:
        return GeneratorStatus(available=True, engine="jscad")

    # ---- Library hand-off --------------------------------------------------

    async def save_stl_to_library(self, stl_bytes: bytes, template_id: str,
                                  parameters: Dict[str, Any],
                                  display_name: Optional[str] = None,
                                  is_business: bool = False) -> Dict[str, Any]:
        """Persist a browser-generated STL into the Library."""
        if not self.library_service:
            raise GeneratorError("Library service unavailable")
        try:
            self.staging_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise GeneratorError(f"Generator storage is not available: {e}")

        # Server-generated name only — no request input reaches the filesystem path.
        staged = self.staging_dir / f"gen_{uuid.uuid4().hex}.stl"
        staged.write_bytes(stl_bytes)

        source_info: Dict[str, Any] = {
            "type": "upload",
            "generator": "jscad",
            "template_id": template_id,
            "parameters": parameters or {},
            "is_business": is_business,
        }
        if display_name:
            safe = _safe_filename(display_name)
            if safe:
                source_info["display_name"] = f"{safe}.stl"
        try:
            result = await self.library_service.add_file_to_library(
                source_path=staged, source_info=source_info,
                copy_file=True, calculate_hash=True,
            )
        finally:
            staged.unlink(missing_ok=True)

        # Tag the saved file with the library's built-in Business/Personal tag so
        # the flag is actually surfaced by library filtering and reporting.
        await self._tag_business(result, is_business)

        await self.event_service.emit_event("generator.generation.saved", {
            "template_id": template_id,
            "timestamp": datetime.now().isoformat(),
        })
        return result

    async def _tag_business(self, file_record: Dict[str, Any], is_business: bool) -> None:
        """Assign the built-in 'Business'/'Personal' library tag to a saved file.

        Best-effort: a tagging failure must never fail the save itself.
        """
        checksum = (file_record or {}).get("checksum")
        repo = getattr(self.library_service, "library_repo", None)
        if not checksum or repo is None:
            return
        tag_id = "tag_business" if is_business else "tag_personal"
        try:
            await repo.assign_tag_to_file(checksum, tag_id)
        except Exception as e:
            logger.warning("Could not tag generated file business/personal",
                           tag_id=tag_id, error=str(e))

    # ---- Presets -----------------------------------------------------------

    async def save_preset(self, template_id: str, name: str,
                          parameters: Dict[str, Any]) -> Preset:
        preset_id = uuid.uuid4().hex[:12]
        await self.repo.create_preset({
            "id": preset_id, "template_id": template_id,
            "name": name, "parameters": parameters,
        })
        return Preset(id=preset_id, template_id=template_id, name=name,
                      parameters=parameters, created_at=datetime.now().isoformat())

    async def list_presets(self, template_id: Optional[str] = None) -> List[Preset]:
        rows = await self.repo.list_presets(template_id)
        return [Preset(**row) for row in rows]

    async def delete_preset(self, preset_id: str) -> None:
        await self.repo.delete_preset(preset_id)


def _safe_filename(name: str) -> str:
    """Sanitize a string for use as a filename stem."""
    keep = [c if (c.isalnum() or c in (" ", "-", "_")) else "_" for c in name]
    return "".join(keep).strip().replace(" ", "_")[:80] or "model"
