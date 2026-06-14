"""
Generator service for the OpenSCAD module.

Coordinates bundled/curated generator templates and arbitrary uploaded ``.scad``
files: discovers their parameters, renders them to STL/PNG via OpenSCADService,
tracks render artifacts, hands finished models off to the Library, and stores
named parameter presets.
"""
import json
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from src.database.repositories import OpenSCADRepository
from src.models.generator import (
    GeneratorStatus,
    Preset,
    RenderResult,
    ScadParameter,
    ScadTemplate,
)
from src.services.openscad_service import OpenSCADService
from src.services.scad_parser import parse_parameters
from src.utils.config import get_settings
from src.utils.errors import GeneratorTemplateNotFoundError, OpenSCADRenderError

logger = structlog.get_logger(__name__)

UPLOAD_PREFIX = "upload:"

# Render/upload ids are server-generated uuid hex tokens. Validating the
# character set up front prevents any path traversal via these identifiers.
_SAFE_TOKEN_RE = re.compile(r"[A-Za-z0-9]{1,64}")


def _is_safe_token(value: Optional[str]) -> bool:
    """Return True if value is a safe identifier (alphanumeric, no separators)."""
    return bool(value) and _SAFE_TOKEN_RE.fullmatch(value) is not None


class GeneratorService:
    """Coordinator for OpenSCAD template rendering and management."""

    def __init__(self, database, event_service, openscad_service: OpenSCADService,
                 library_service=None):
        self.database = database
        self.event_service = event_service
        self.openscad = openscad_service
        self.library_service = library_service
        self.repo = OpenSCADRepository(database._connection)

        settings = get_settings()
        self.output_dir = Path(settings.generator_output_dir)
        self.uploads_dir = self.output_dir / "uploads"
        self.renders_dir = self.output_dir / "renders"
        self.templates_dir = Path(__file__).parent.parent / "scad_templates"

        self._templates: Dict[str, ScadTemplate] = {}
        self._dirs_ready = False

    async def initialize(self) -> None:
        """
        Load bundled templates and prepare working directories.

        Directory creation is best-effort: the generator is an optional feature,
        so a non-writable output directory must never crash application startup.
        Directories are (re)created lazily when a render or upload runs.
        """
        self._ensure_dirs()
        self._load_templates()
        logger.info("Generator service initialized",
                    templates=len(self._templates),
                    output_dir=str(self.output_dir),
                    output_writable=self._dirs_ready,
                    openscad_available=self.openscad.available)

    def _ensure_dirs(self) -> bool:
        """Create the working directories if possible. Returns success."""
        try:
            for folder in (self.output_dir, self.uploads_dir, self.renders_dir):
                folder.mkdir(parents=True, exist_ok=True)
            self._dirs_ready = True
        except OSError as e:
            self._dirs_ready = False
            logger.warning("Generator output directory is not writable; "
                           "rendering/upload will be unavailable",
                           output_dir=str(self.output_dir), error=str(e))
        return self._dirs_ready

    # ---- Status ------------------------------------------------------------

    def get_status(self) -> GeneratorStatus:
        return GeneratorStatus(**self.openscad.get_status())

    # ---- Templates ---------------------------------------------------------

    def _load_templates(self) -> None:
        """Load bundled .scad templates and their optional .json metadata."""
        self._templates.clear()
        if not self.templates_dir.exists():
            return
        for scad_file in sorted(self.templates_dir.glob("*.scad")):
            template_id = scad_file.stem
            source = scad_file.read_text(encoding="utf-8")
            meta: Dict[str, Any] = {}
            meta_file = scad_file.with_suffix(".json")
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    logger.warning("Invalid template metadata", file=str(meta_file), error=str(e))
            self._templates[template_id] = ScadTemplate(
                id=template_id,
                name=meta.get("name", template_id.replace("_", " ").title()),
                description=meta.get("description"),
                category=meta.get("category"),
                bundled=True,
                parameters=parse_parameters(source),
                default_camera=meta.get("default_camera"),
                source=source,
            )

    def list_templates(self) -> List[ScadTemplate]:
        """Return all bundled templates (with parameters, without source)."""
        return [t.model_copy(update={"source": None}) for t in self._templates.values()]

    def get_template(self, template_id: str) -> ScadTemplate:
        template = self._templates.get(template_id)
        if not template:
            raise GeneratorTemplateNotFoundError(template_id)
        return template

    def parse_source(self, source: str) -> List[ScadParameter]:
        """Parse parameters from arbitrary OpenSCAD source."""
        return parse_parameters(source)

    # ---- Uploads -----------------------------------------------------------

    def store_upload(self, source: str, filename: Optional[str] = None) -> ScadTemplate:
        """Persist an uploaded .scad source and return it as a template."""
        if not self._ensure_dirs():
            raise OpenSCADRenderError("Generator storage is not available")
        upload_id = uuid.uuid4().hex[:12]
        path = self.uploads_dir / f"{upload_id}.scad"
        path.write_text(source, encoding="utf-8")
        return ScadTemplate(
            id=f"{UPLOAD_PREFIX}{upload_id}",
            name=filename or f"Uploaded {upload_id}",
            description="Uploaded OpenSCAD file",
            category="Uploads",
            bundled=False,
            parameters=parse_parameters(source),
            source=source,
        )

    def _resolve_source(self, source_ref: str) -> tuple[str, Optional[str]]:
        """Return (source, default_camera) for a template id or upload ref."""
        if source_ref.startswith(UPLOAD_PREFIX):
            # basename strips any directory components and the alphanumeric check
            # rejects traversal, so the request value cannot escape uploads_dir.
            upload_id = os.path.basename(source_ref[len(UPLOAD_PREFIX):])
            if not re.fullmatch(r"[A-Za-z0-9]+", upload_id):
                raise GeneratorTemplateNotFoundError(source_ref)
            path = self.uploads_dir / f"{upload_id}.scad"
            if not path.exists():
                raise GeneratorTemplateNotFoundError(source_ref)
            return path.read_text(encoding="utf-8"), None
        template = self.get_template(source_ref)
        return template.source or "", template.default_camera

    # ---- Rendering ---------------------------------------------------------

    async def render(self, source_ref: str, parameters: Dict[str, Any],
                     fmt: str = "stl") -> RenderResult:
        """Render a template/upload to STL or PNG and record the artifact."""
        if not self._ensure_dirs():
            raise OpenSCADRenderError("Generator storage is not available")
        source, default_camera = self._resolve_source(source_ref)
        render_id = uuid.uuid4().hex[:16]
        work_dir = self.renders_dir / render_id
        work_dir.mkdir(parents=True, exist_ok=True)

        await self.repo.create_render({
            "id": render_id,
            "source_ref": source_ref,
            "parameters": parameters,
            "format": fmt,
            "status": "running",
            "work_dir": str(work_dir),
        })
        await self._emit("started", render_id, source_ref)

        try:
            scad_path = work_dir / "model.scad"
            scad_path.write_text(source, encoding="utf-8")
            output_path = work_dir / f"model.{fmt}"
            await self.openscad.render(
                scad_path, output_path, params=parameters, fmt=fmt, camera=default_camera
            )
        except OpenSCADRenderError as e:
            await self.repo.update_render(render_id, {"status": "failed", "error": e.message})
            await self._emit("failed", render_id, source_ref, error=e.message)
            raise

        field = "model_path" if fmt == "stl" else "preview_path"
        await self.repo.update_render(render_id, {"status": "completed", field: str(output_path)})
        await self._emit("completed", render_id, source_ref)

        return RenderResult(
            render_id=render_id,
            source_ref=source_ref,
            format=fmt,
            status="completed",
            model_url=f"/api/v1/generator/render/{render_id}/model.stl" if fmt == "stl" else None,
            preview_url=f"/api/v1/generator/render/{render_id}/preview.png" if fmt == "png" else None,
        )

    def _confined_artifact(self, path_str: Optional[str]) -> Optional[Path]:
        """
        Return the stored artifact path if it lies within the renders directory.

        ``path_str`` is read from the render's database record (server-written
        at render time), never from request input. The containment check is
        defence-in-depth so a path can never point outside the renders root.
        """
        if not path_str:
            return None
        path = Path(path_str)
        try:
            path.resolve().relative_to(self.renders_dir.resolve())
        except ValueError:
            return None
        return path if path.exists() else None

    async def get_artifact_path(self, render_id: str, kind: str) -> Optional[Path]:
        """Return the filesystem path to a render artifact ('model' or 'preview')."""
        if not _is_safe_token(render_id):
            return None
        render = await self.repo.get_render(render_id)
        if not render:
            return None
        key = "model_path" if kind == "model" else "preview_path"
        return self._confined_artifact(render.get(key))

    # ---- Library hand-off --------------------------------------------------

    async def save_to_library(self, render_id: str,
                              display_name: Optional[str] = None) -> Dict[str, Any]:
        """Copy a completed STL render into the Library so it can be sliced."""
        if not self.library_service:
            raise OpenSCADRenderError("Library service unavailable")
        if not _is_safe_token(render_id):
            raise GeneratorTemplateNotFoundError(render_id)
        render = await self.repo.get_render(render_id)
        if not render:
            raise GeneratorTemplateNotFoundError(render_id)
        # Source path comes from the stored render record (server-written).
        artifact = self._confined_artifact(render.get("model_path"))
        if artifact is None:
            raise OpenSCADRenderError("No STL artifact to save", details={"render_id": render_id})

        # Stage a copy with a generated name so no user input reaches the path.
        staged = self.renders_dir / f"library_{uuid.uuid4().hex}.stl"
        shutil.copy2(artifact, staged)

        source_info = {
            "type": "upload",
            "generator": "openscad",
            "source_ref": render["source_ref"],
            "parameters": render.get("parameters", {}),
        }
        # The user's chosen name is recorded as library metadata only - it never
        # touches a filesystem path.
        if display_name:
            safe_label = _safe_filename(display_name)
            if safe_label:
                source_info["display_name"] = f"{safe_label}.stl"
        try:
            return await self.library_service.add_file_to_library(
                source_path=staged, source_info=source_info,
                copy_file=True, calculate_hash=True,
            )
        finally:
            staged.unlink(missing_ok=True)

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

    # ---- Events ------------------------------------------------------------

    async def _emit(self, phase: str, render_id: str, source_ref: str,
                    error: Optional[str] = None) -> None:
        payload = {
            "render_id": render_id,
            "source_ref": source_ref,
            "timestamp": datetime.now().isoformat(),
        }
        if error:
            payload["error"] = error
        await self.event_service.emit_event(f"openscad.generation.{phase}", payload)


def _safe_filename(name: str) -> str:
    """Sanitize a string for use as a filename stem."""
    keep = [c if (c.isalnum() or c in (" ", "-", "_")) else "_" for c in name]
    return "".join(keep).strip().replace(" ", "_")[:80] or "model"
