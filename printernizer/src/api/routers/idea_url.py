"""
URL parsing endpoints for Ideas feature.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, List

from src.utils.dependencies import get_idea_service
from src.services.idea_service import IdeaService
from src.utils.errors import ValidationError as PrinternizerValidationError, success_response

router = APIRouter(prefix="/ideas/url", tags=["ideas-url"])


class UrlPreviewRequest(BaseModel):
    url: str


# URL parsing and validation endpoints
@router.get("/validate", response_model=Dict[str, Any])
async def validate_url(
    url: str,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Validate if URL is from a supported platform."""
    is_valid = idea_service.url_parser.validate_url(url)
    platform = idea_service.url_parser.detect_platform(url) if is_valid else None

    return {
        "valid": is_valid,
        "platform": platform,
        "supported_platforms": idea_service.url_parser.get_supported_platforms()
    }


@router.post("/preview", response_model=Dict[str, Any])
async def preview_url(
    url_data: UrlPreviewRequest,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Preview metadata that would be extracted from URL without saving."""
    metadata = await idea_service._extract_url_metadata(url_data.url)
    if not metadata:
        raise PrinternizerValidationError(
            field="url",
            error="Unable to extract metadata from URL"
        )

    return {
        "url": url_data.url,
        "metadata": metadata,
        "preview": {
            "title": metadata.get('title', 'Unknown Title'),
            "platform": metadata.get('platform', 'external'),
            "creator": metadata.get('creator'),
            "model_id": metadata.get('model_id')
        }
    }


@router.get("/platforms", response_model=List[Dict[str, Any]])
async def get_supported_platforms(
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get information about supported platforms."""
    platforms = idea_service.url_parser.get_supported_platforms()
    platform_info = []

    for platform in platforms:
        info = idea_service.url_parser.get_platform_info(platform)
        platform_info.append({
            "id": platform,
            **info
        })

    return platform_info