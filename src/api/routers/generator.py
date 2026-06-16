"""
Model Generator API router (build123d).

Endpoints for the parametric model generator: query availability, list/inspect
bundled templates, render to STL (with a best-effort PNG preview), serve render
artifacts, save results to the Library, and manage parameter presets.

Only bundled templates are supported — there is no template upload, because
build123d templates are executable Python and running uploaded code would be a
remote code execution risk.
"""
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.models.generator import (
    GeneratorStatus,
    ModelTemplate,
    Preset,
    PresetRequest,
    RenderRequest,
    RenderResult,
)
from src.services.generator_service import GeneratorService
from src.utils.errors import GeneratorNotAvailableError, NotFoundError

logger = structlog.get_logger(__name__)

router = APIRouter()


async def get_generator_service(request: Request) -> GeneratorService:
    """Get generator service instance from app state."""
    return request.app.state.generator_service


class SaveRequest(BaseModel):
    """Request to save a render into the Library."""
    display_name: Optional[str] = None


@router.get("/status", response_model=GeneratorStatus)
async def get_status(service: GeneratorService = Depends(get_generator_service)):
    """Report whether the build123d engine is available (drives conditional UI)."""
    return service.get_status()


@router.get("/templates", response_model=List[ModelTemplate])
async def list_templates(service: GeneratorService = Depends(get_generator_service)):
    """List bundled generator templates with their parameter schemas."""
    return service.list_templates()


@router.get("/templates/{template_id}", response_model=ModelTemplate)
async def get_template(template_id: str,
                       service: GeneratorService = Depends(get_generator_service)):
    """Get a single template with its parameter schema."""
    return service.get_template(template_id)


@router.post("/render", response_model=RenderResult)
async def render(body: RenderRequest,
                 service: GeneratorService = Depends(get_generator_service)):
    """Render a template to STL (with a best-effort PNG preview)."""
    if not service.engine.available:
        raise GeneratorNotAvailableError()
    return await service.render(body.template_id, body.parameters, fmt=body.format.value)


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
