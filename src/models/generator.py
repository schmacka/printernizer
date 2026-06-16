"""
Data models for the build123d parametric model generator.

Templates are Python modules built on the build123d CAD library. Each template
exposes a ``build(**params)`` function and ships a JSON sidecar describing its
parameters (name/type/constraints/default). These models describe the templates,
their parameter schemas, render requests/results, saved presets, and the runtime
availability of the build123d engine.
"""
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ParameterType(str, Enum):
    """Supported template parameter types (drive form rendering + validation)."""
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


class TemplateParameter(BaseModel):
    """A single parameter of a generator template (from its JSON sidecar)."""
    name: str
    type: ParameterType
    default: Any = None
    description: Optional[str] = None
    group: Optional[str] = None
    # Numeric constraints
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    # Enum/dropdown options
    options: Optional[List[Any]] = None


class ModelTemplate(BaseModel):
    """A bundled build123d generator template."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    parameters: List[TemplateParameter] = Field(default_factory=list)


class RenderRequest(BaseModel):
    """Request to render a template with parameter overrides."""
    template_id: str = Field(..., description="Bundled template id")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    format: RenderFormat = RenderFormat.STL


class RenderResult(BaseModel):
    """Result of a render operation."""
    render_id: str
    template_id: str
    format: RenderFormat
    status: RenderStatus
    preview_url: Optional[str] = None
    model_url: Optional[str] = None
    error: Optional[str] = None


class GeneratorStatus(BaseModel):
    """Runtime availability of the build123d generator engine."""
    available: bool
    engine: str = "build123d"
    version: Optional[str] = None


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
