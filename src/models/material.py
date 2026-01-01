"""
Material tracking model for Printernizer.
Manages material inventory, costs, and consumption tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class MaterialType(str, Enum):
    """Supported material types."""
    PLA = "PLA"
    PLA_ECO = "PLA_ECO"
    PLA_MATTE = "PLA_MATTE"
    PLA_SILK = "PLA_SILK"
    PLA_TURBO = "PLA_TURBO"
    PETG = "PETG"
    TPU = "TPU"
    ABS = "ABS"
    ASA = "ASA"
    NYLON = "NYLON"
    PC = "PC"
    OTHER = "OTHER"


class MaterialBrand(str, Enum):
    """Common material brands."""
    OVERTURE = "OVERTURE"
    PRUSAMENT = "PRUSAMENT"
    BAMBU = "BAMBU"
    POLYMAKER = "POLYMAKER"
    ESUN = "ESUN"
    OTHER = "OTHER"


class MaterialColor(str, Enum):
    """Common material colors."""
    BLACK = "BLACK"
    WHITE = "WHITE"
    GREY = "GREY"
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    PURPLE = "PURPLE"
    PINK = "PINK"
    TRANSPARENT = "TRANSPARENT"
    NATURAL = "NATURAL"
    OTHER = "OTHER"


@dataclass
class MaterialSpool:
    """Represents a physical spool of material."""
    id: str
    material_type: MaterialType
    brand: MaterialBrand
    color: MaterialColor
    diameter: float  # mm (1.75, 2.85, etc.)
    weight: float  # kg (original spool weight)
    remaining_weight: float  # kg (current remaining)
    cost_per_kg: Decimal = Decimal('0')  # EUR per kg (optional, defaults to 0)
    purchase_date: datetime = field(default_factory=datetime.now)
    vendor: str = ""
    batch_number: Optional[str] = None
    notes: Optional[str] = None
    printer_id: Optional[str] = None  # Currently loaded in printer
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def used_weight(self) -> float:
        """Calculate used material weight."""
        return self.weight - self.remaining_weight

    @property
    def remaining_percentage(self) -> float:
        """Calculate remaining material percentage."""
        if self.weight <= 0:
            return 0
        return (self.remaining_weight / self.weight) * 100

    @property
    def total_cost(self) -> Decimal:
        """Calculate total spool cost."""
        return Decimal(str(self.weight)) * self.cost_per_kg

    @property
    def remaining_value(self) -> Decimal:
        """Calculate remaining material value."""
        return Decimal(str(self.remaining_weight)) * self.cost_per_kg


class MaterialCreate(BaseModel):
    """Schema for creating a new material spool."""
    model_config = ConfigDict(str_strip_whitespace=True)

    material_type: MaterialType
    brand: MaterialBrand
    color: MaterialColor
    diameter: float = Field(gt=0, le=10, description="Filament diameter in mm")
    weight: float = Field(gt=0, le=10, description="Spool weight in kg")
    remaining_weight: float = Field(ge=0, le=10, description="Remaining weight in kg")
    cost_per_kg: Optional[Decimal] = Field(default=Decimal('0'), ge=0, le=1000, description="Cost per kg in EUR (optional)")
    vendor: str = Field(min_length=1, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)
    printer_id: Optional[str] = None

    @field_validator('remaining_weight')
    def validate_remaining(cls, v, values):
        """Ensure remaining weight doesn't exceed total weight."""
        if 'weight' in values.data and v > values.data['weight']:
            raise ValueError('Remaining weight cannot exceed total weight')
        return v


class MaterialUpdate(BaseModel):
    """Schema for updating material spool."""
    model_config = ConfigDict(str_strip_whitespace=True)

    remaining_weight: Optional[float] = Field(None, ge=0, le=10)
    cost_per_kg: Optional[Decimal] = Field(None, ge=0, le=1000)
    printer_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)


class MaterialConsumption(BaseModel):
    """Track material consumption for a job."""
    model_config = ConfigDict(str_strip_whitespace=True)

    job_id: str
    material_id: str
    weight_used: float = Field(gt=0, le=10, description="Material used in grams")
    cost: Decimal = Field(description="Cost in EUR")
    timestamp: datetime = Field(default_factory=datetime.now)
    printer_id: str
    file_name: Optional[str] = None
    print_time_hours: Optional[float] = None

    @property
    def weight_used_kg(self) -> float:
        """Convert grams to kg."""
        return self.weight_used / 1000


class MaterialStats(BaseModel):
    """Material statistics and analytics."""
    model_config = ConfigDict(str_strip_whitespace=True)

    total_spools: int
    total_weight: float  # kg
    total_remaining: float  # kg
    total_value: Decimal  # EUR
    remaining_value: Decimal  # EUR
    by_type: Dict[str, Dict[str, Any]]
    by_brand: Dict[str, Dict[str, Any]]
    by_color: Dict[str, int]
    low_stock: list[str]  # Material IDs below 20% remaining
    consumption_30d: float  # kg consumed in last 30 days
    consumption_rate: float  # kg per day average


class MaterialReport(BaseModel):
    """Material consumption report."""
    model_config = ConfigDict(str_strip_whitespace=True)

    period_start: datetime
    period_end: datetime
    total_consumed: float  # kg
    total_cost: Decimal  # EUR
    by_material: Dict[str, Dict[str, Any]]
    by_printer: Dict[str, Dict[str, Any]]
    by_job_type: Dict[str, Dict[str, Any]]  # business vs private
    top_consumers: list[Dict[str, Any]]  # Top consuming jobs
    efficiency_metrics: Dict[str, float]


class ConsumptionHistoryItem(BaseModel):
    """Single consumption history record with material details."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str
    job_id: str
    material_id: str
    material_type: str
    brand: str
    color: str
    weight_used: float  # grams
    cost: Decimal
    timestamp: datetime
    printer_id: str
    file_name: Optional[str] = None
    print_time_hours: Optional[float] = None


class ConsumptionHistoryResponse(BaseModel):
    """Paginated consumption history response."""
    model_config = ConfigDict(str_strip_whitespace=True)

    items: list[ConsumptionHistoryItem]
    total_count: int
    page: int
    limit: int
    total_pages: int