"""
Model Generator API router.

Geometry is generated in the browser (JSCAD). The server only:
  - reports status (always available — there is no server engine),
  - accepts a finished STL and stores it in the Library,
  - manages named parameter presets.
"""
import json
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from src.models.generator import GeneratorStatus, Preset, PresetRequest
from src.services.generator_service import GeneratorService
from src.utils.errors import ValidationError

logger = structlog.get_logger(__name__)

router = APIRouter()

# Generated STLs are small; cap the upload defensively.
MAX_STL_BYTES = 50 * 1024 * 1024  # 50 MB


async def get_generator_service(request: Request) -> GeneratorService:
    """Get generator service instance from app state."""
    return request.app.state.generator_service


@router.get("/status", response_model=GeneratorStatus)
async def get_status(service: GeneratorService = Depends(get_generator_service)):
    """Generator availability (always true — geometry is generated client-side)."""
    return service.get_status()


@router.post("/save")
async def save_to_library(
    file: UploadFile = File(...),
    template_id: str = Form("custom"),
    parameters: str = Form("{}"),
    display_name: Optional[str] = Form(None),
    service: GeneratorService = Depends(get_generator_service),
):
    """Store a browser-generated STL in the Library for slicing/printing."""
    content = await file.read()
    if not content:
        raise ValidationError("file", "Empty STL upload")
    if len(content) > MAX_STL_BYTES:
        raise ValidationError("file", "STL exceeds the 50 MB limit")
    # Cheap STL sniff: ASCII starts with "solid", binary has an 84+ byte header.
    if not (content[:5].lower() == b"solid" or len(content) >= 84):
        raise ValidationError("file", "File does not look like an STL")

    try:
        params = json.loads(parameters) if parameters else {}
        if not isinstance(params, dict):
            params = {}
    except json.JSONDecodeError:
        params = {}

    result = await service.save_stl_to_library(
        content, template_id=template_id, parameters=params, display_name=display_name
    )
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
