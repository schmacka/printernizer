"""
OpenSCAD Generator API router.

Endpoints for the parametric model generator: query availability, list/inspect
bundled templates, upload and parse arbitrary .scad files, render to STL/PNG,
serve render artifacts, save results to the Library, and manage presets.
"""
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.models.generator import (
    GeneratorStatus,
    Preset,
    PresetRequest,
    RenderRequest,
    RenderResult,
    ScadParameter,
    ScadTemplate,
)
from src.services.generator_service import GeneratorService
from src.utils.errors import NotFoundError, OpenSCADNotAvailableError, ValidationError

logger = structlog.get_logger(__name__)

router = APIRouter()

MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB is plenty for a .scad source file


async def get_generator_service(request: Request) -> GeneratorService:
    """Get generator service instance from app state."""
    return request.app.state.generator_service


class ParseRequest(BaseModel):
    """Request to parse parameters from raw OpenSCAD source."""
    source: str


class SaveRequest(BaseModel):
    """Request to save a render into the Library."""
    display_name: Optional[str] = None


@router.get("/status", response_model=GeneratorStatus)
async def get_status(service: GeneratorService = Depends(get_generator_service)):
    """Report whether OpenSCAD is available (drives conditional UI)."""
    return service.get_status()


@router.get("/templates", response_model=List[ScadTemplate])
async def list_templates(service: GeneratorService = Depends(get_generator_service)):
    """List bundled generator templates with their parameter schemas."""
    return service.list_templates()


@router.get("/templates/{template_id}", response_model=ScadTemplate)
async def get_template(template_id: str,
                       service: GeneratorService = Depends(get_generator_service)):
    """Get a single template including its OpenSCAD source."""
    return service.get_template(template_id)


@router.post("/parse", response_model=List[ScadParameter])
async def parse_source(body: ParseRequest,
                       service: GeneratorService = Depends(get_generator_service)):
    """Parse parameters from pasted OpenSCAD source."""
    return service.parse_source(body.source)


@router.post("/upload", response_model=ScadTemplate)
async def upload_scad(file: UploadFile = File(...),
                      service: GeneratorService = Depends(get_generator_service)):
    """Upload an arbitrary .scad file and auto-discover its parameters."""
    filename = file.filename or "uploaded.scad"
    if not filename.lower().endswith(".scad"):
        raise ValidationError("file", "Only .scad files are accepted")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValidationError("file", "File exceeds the 2 MB limit")
    try:
        source = content.decode("utf-8")
    except UnicodeDecodeError:
        raise ValidationError("file", "File is not valid UTF-8 text")
    return service.store_upload(source, filename=filename)


@router.post("/render", response_model=RenderResult)
async def render(body: RenderRequest,
                 service: GeneratorService = Depends(get_generator_service)):
    """Render a template/upload to STL or PNG with parameter overrides."""
    if not service.openscad.available:
        raise OpenSCADNotAvailableError()
    return await service.render(body.source_ref, body.parameters, fmt=body.format.value)


@router.get("/render/{render_id}/model.stl")
async def get_render_model(render_id: str,
                           service: GeneratorService = Depends(get_generator_service)):
    """Serve the STL artifact for a render."""
    path = await service.get_artifact_path(render_id, "model")
    if not path:
        raise NotFoundError("render artifact", render_id)
    return FileResponse(path, media_type="model/stl", filename=f"{render_id}.stl")


@router.get("/render/{render_id}/preview.png")
async def get_render_preview(render_id: str,
                             service: GeneratorService = Depends(get_generator_service)):
    """Serve the PNG preview for a render."""
    path = await service.get_artifact_path(render_id, "preview")
    if not path:
        raise NotFoundError("render artifact", render_id)
    return FileResponse(path, media_type="image/png")


@router.post("/render/{render_id}/save")
async def save_render_to_library(render_id: str, body: SaveRequest,
                                 service: GeneratorService = Depends(get_generator_service)):
    """Save a completed STL render into the Library for slicing/printing."""
    result = await service.save_to_library(render_id, display_name=body.display_name)
    return {"status": "success", "data": result}


@router.get("/presets", response_model=List[Preset])
async def list_presets(template_id: Optional[str] = Query(None),
                       service: GeneratorService = Depends(get_generator_service)):
    """List saved parameter presets, optionally filtered by template."""
    return await service.list_presets(template_id)


@router.post("/presets", response_model=Preset)
async def create_preset(body: PresetRequest,
                        service: GeneratorService = Depends(get_generator_service)):
    """Save a named parameter preset for a template."""
    return await service.save_preset(body.template_id, body.name, body.parameters)


@router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: str,
                        service: GeneratorService = Depends(get_generator_service)):
    """Delete a saved preset."""
    await service.delete_preset(preset_id)
    return {"status": "success"}
