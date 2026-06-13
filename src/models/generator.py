"""
Data models for the OpenSCAD generator module.

These models describe parametric OpenSCAD templates, their auto-discovered
parameters (via the OpenSCAD Customizer comment syntax), render requests and
results, and the runtime availability status of the OpenSCAD binary.
"""
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScadParameterType(str, Enum):
    """Supported OpenSCAD Customizer parameter types."""
    NUMBER = "number"
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"


class RenderFormat(str, Enum):
    """Supported render output formats."""
    STL = "stl"
    PNG = "png"


class RenderStatus(str, Enum):
    """Lifecycle status of a render job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScadParameter(BaseModel):
    """A single parameter discovered from an OpenSCAD script."""
    name: str
    type: ScadParameterType
    default: Any = None
    description: Optional[str] = None
    group: Optional[str] = None
    # Numeric constraints (Customizer: // [min:max] or // [min:step:max])
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    # Enum/dropdown options (Customizer: // [a, b, c])
    options: Optional[List[Any]] = None


class ScadTemplate(BaseModel):
    """A bundled or uploaded OpenSCAD template/source."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    # True for app-bundled generators, False for user uploads
    bundled: bool = True
    parameters: List[ScadParameter] = Field(default_factory=list)
    # Default camera string for PNG previews: "tx,ty,tz,rx,ry,rz,dist"
    default_camera: Optional[str] = None
    source: Optional[str] = None  # raw .scad source (omitted from list views)


class RenderRequest(BaseModel):
    """Request to render a template/source with parameter overrides."""
    source_ref: str = Field(..., description="Template id or uploaded source id")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    format: RenderFormat = RenderFormat.STL


class RenderResult(BaseModel):
    """Result of a render operation."""
    render_id: str
    source_ref: str
    format: RenderFormat
    status: RenderStatus
    preview_url: Optional[str] = None
    model_url: Optional[str] = None
    error: Optional[str] = None


class GeneratorStatus(BaseModel):
    """Runtime availability of the OpenSCAD generator."""
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None


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
