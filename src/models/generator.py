"""
Data models for the model generator.

Geometry is generated **client-side** (in the browser, via JSCAD), so the server
only persists named parameter presets and accepts the finished STL to store in
the Library. There are no server-side render/template models.
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GeneratorStatus(BaseModel):
    """Runtime status of the generator. Always available (browser-side engine)."""
    available: bool = True
    engine: str = "jscad"


class PresetRequest(BaseModel):
    """Request to save a named parameter preset for a template."""
    template_id: str
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class Preset(BaseModel):
    """A saved named parameter set for a template."""
    id: str
    template_id: str
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
