"""
Generator service for the build123d model generator.

Coordinates the bundled build123d templates: exposes their parameter schemas,
renders them to STL (with a best-effort PNG thumbnail) via Build123dService,
tracks render artifacts, hands finished models off to the Library, and stores
named parameter presets.

Only bundled templates are supported. Unlike the previous OpenSCAD integration
there is no template upload, because build123d templates are executable Python —
running uploaded templates would be arbitrary code execution.
"""
import importlib
import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

from src.database.repositories import GeneratorRepository
from src.models.generator import (
    GeneratorStatus,
    ModelTemplate,
    ParameterType,
    Preset,
    RenderResult,
    TemplateParameter,
)
from src.services.build123d_service import Build123dService
from src.utils.config import get_settings
from src.utils.errors import GeneratorRenderError, GeneratorTemplateNotFoundError

logger = structlog.get_logger(__name__)

# Template ids are derived from filenames we ship; restrict the character set so
# they can never influence the dynamic import path.
_SAFE_ID_RE = re.compile(r"[a-z0-9_]{1,64}")
# Render ids are server-generated uuid hex tokens.
_SAFE_TOKEN_RE = re.compile(r"[A-Za-z0-9]{1,64}")


def _is_safe_id(value: Optional[str]) -> bool:
    return bool(value) and _SAFE_ID_RE.fullmatch(value) is not None


def _is_safe_token(value: Optional[str]) -> bool:
    return bool(value) and _SAFE_TOKEN_RE.fullmatch(value) is not None


class GeneratorService:
    """Coordinator for build123d template rendering and management."""

    def __init__(self, database, event_service, engine: Build123dService,
                 library_service=None):
        self.database = database
        self.event_service = event_service
        self.engine = engine
        self.library_service = library_service
        self.repo = GeneratorRepository(database._connection)

        settings = get_settings()
        self.output_dir = Path(settings.generator_output_dir)
        self.renders_dir = self.output_dir / "renders"
        self.templates_dir = Path(__file__).parent.parent / "build123d_templates"

        self._templates: Dict[str, ModelTemplate] = {}
        self._dirs_ready = False

    async def initialize(self) -> None:
        """
        Load bundled templates and prepare working directories.

        Directory creation is best-effort: the generator is an optional feature,
        so a non-writable output directory must never crash application startup.
        """
        self._ensure_dirs()
        self._load_templates()
        logger.info("Generator service initialized",
                    templates=len(self._templates),
                    output_dir=str(self.output_dir),
                    output_writable=self._dirs_ready,
                    build123d_available=self.engine.available)

    def _ensure_dirs(self) -> bool:
        """Create the working directories if possible. Returns success."""
        try:
            for folder in (self.output_dir, self.renders_dir):
                folder.mkdir(parents=True, exist_ok=True)
            self._dirs_ready = True
        except OSError as e:
            self._dirs_ready = False
            logger.warning("Generator output directory is not writable; "
                           "rendering will be unavailable",
                           output_dir=str(self.output_dir), error=str(e))
        return self._dirs_ready

    # ---- Status ------------------------------------------------------------

    def get_status(self) -> GeneratorStatus:
        return GeneratorStatus(**self.engine.get_status())

    # ---- Templates ---------------------------------------------------------

    def _load_templates(self) -> None:
        """Discover bundled templates (a <id>.py module + <id>.json sidecar)."""
        self._templates.clear()
        if not self.templates_dir.exists():
            return
        for py_file in sorted(self.templates_dir.glob("*.py")):
            template_id = py_file.stem
            if template_id.startswith("_") or not _is_safe_id(template_id):
                continue
            meta_file = py_file.with_suffix(".json")
            if not meta_file.exists():
                continue
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                logger.warning("Invalid template metadata", file=str(meta_file), error=str(e))
                continue
            parameters = [TemplateParameter(**p) for p in meta.get("parameters", [])]
            self._templates[template_id] = ModelTemplate(
                id=template_id,
                name=meta.get("name", template_id.replace("_", " ").title()),
                description=meta.get("description"),
                category=meta.get("category"),
                parameters=parameters,
            )

    def list_templates(self) -> List[ModelTemplate]:
        return list(self._templates.values())

    def get_template(self, template_id: str) -> ModelTemplate:
        template = self._templates.get(template_id)
        if not template:
            raise GeneratorTemplateNotFoundError(template_id)
        return template

    def _resolve_build_fn(self, template_id: str) -> Callable[..., Any]:
        """Import a bundled template module and return its build() callable."""
        if template_id not in self._templates or not _is_safe_id(template_id):
            raise GeneratorTemplateNotFoundError(template_id)
        module = importlib.import_module(f"src.build123d_templates.{template_id}")
        build_fn = getattr(module, "build", None)
        if not callable(build_fn):
            raise GeneratorTemplateNotFoundError(template_id)
        return build_fn

    def _coerce_params(self, template: ModelTemplate,
                       overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Build a clean parameter dict from defaults + validated overrides."""
        clean: Dict[str, Any] = {}
        for param in template.parameters:
            value = overrides.get(param.name, param.default)
            if param.type == ParameterType.NUMBER:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    value = float(param.default if param.default is not None else 0)
                if param.min is not None:
                    value = max(param.min, value)
                if param.max is not None:
                    value = min(param.max, value)
            elif param.type == ParameterType.BOOLEAN:
                if isinstance(value, str):
                    value = value.strip().lower() in ("1", "true", "yes", "on")
                else:
                    value = bool(value)
            elif param.type == ParameterType.ENUM:
                if param.options and value not in param.options:
                    value = param.default
            clean[param.name] = value
        return clean

    # ---- Rendering ---------------------------------------------------------

    async def render(self, template_id: str, parameters: Dict[str, Any],
                     fmt: str = "stl") -> RenderResult:
        """Render a template to STL (with a best-effort PNG preview)."""
        if not self._ensure_dirs():
            raise GeneratorRenderError("Generator storage is not available")
        template = self.get_template(template_id)
        build_fn = self._resolve_build_fn(template_id)
        clean_params = self._coerce_params(template, parameters)

        render_id = uuid.uuid4().hex[:16]
        work_dir = self.renders_dir / render_id
        work_dir.mkdir(parents=True, exist_ok=True)

        await self.repo.create_render({
            "id": render_id,
            "template_id": template_id,
            "parameters": clean_params,
            "format": fmt,
            "status": "running",
            "work_dir": str(work_dir),
        })
        await self._emit("started", render_id, template_id)

        stl_path = work_dir / "model.stl"
        try:
            await self.engine.render_stl(build_fn, clean_params, stl_path)
        except GeneratorRenderError as e:
            await self.repo.update_render(render_id, {"status": "failed", "error": e.message})
            await self._emit("failed", render_id, template_id, error=e.message)
            raise

        # Best-effort PNG thumbnail (degrades gracefully when matplotlib absent).
        preview_path = work_dir / "preview.png"
        preview_url = None
        try:
            if await self.engine.render_preview(stl_path, preview_path):
                preview_url = f"/api/v1/generator/render/{render_id}/preview.png"
        except Exception as e:  # noqa: BLE001 - preview must never fail a render
            logger.warning("Preview thumbnail generation failed",
                           render_id=render_id, error=str(e))

        await self.repo.update_render(render_id, {
            "status": "completed",
            "model_path": str(stl_path),
            "preview_path": str(preview_path) if preview_url else None,
        })
        await self._emit("completed", render_id, template_id)

        return RenderResult(
            render_id=render_id,
            template_id=template_id,
            format="stl",
            status="completed",
            model_url=f"/api/v1/generator/render/{render_id}/model.stl",
            preview_url=preview_url,
        )

    def _confined_artifact(self, path_str: Optional[str]) -> Optional[Path]:
        """Return the stored artifact path only if it lies within renders_dir."""
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
            raise GeneratorRenderError("Library service unavailable")
        if not _is_safe_token(render_id):
            raise GeneratorTemplateNotFoundError(render_id)
        render = await self.repo.get_render(render_id)
        if not render:
            raise GeneratorTemplateNotFoundError(render_id)
        artifact = self._confined_artifact(render.get("model_path"))
        if artifact is None:
            raise GeneratorRenderError("No STL artifact to save", details={"render_id": render_id})

        # Stage a copy with a generated name so no user input reaches the path.
        staged = self.renders_dir / f"library_{uuid.uuid4().hex}.stl"
        shutil.copy2(artifact, staged)

        source_info = {
            "type": "upload",
            "generator": "build123d",
            "template_id": render["template_id"],
            "parameters": render.get("parameters", {}),
        }
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

    async def _emit(self, phase: str, render_id: str, template_id: str,
                    error: Optional[str] = None) -> None:
        payload = {
            "render_id": render_id,
            "template_id": template_id,
            "timestamp": datetime.now().isoformat(),
        }
        if error:
            payload["error"] = error
        await self.event_service.emit_event(f"generator.generation.{phase}", payload)


def _safe_filename(name: str) -> str:
    """Sanitize a string for use as a filename stem."""
    keep = [c if (c.isalnum() or c in (" ", "-", "_")) else "_" for c in name]
    return "".join(keep).strip().replace(" ", "_")[:80] or "model"
