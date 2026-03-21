"""Order models for Printernizer."""
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class OrderStatus(str, Enum):
    NEW = "new"
    PLANNED = "planned"
    PRINTED = "printed"
    DELIVERED = "delivered"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"


class OrderSourceCreate(BaseModel):
    """Order source creation model."""
    name: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        if len(v) > 100:
            raise ValueError("name max length is 100 characters")
        return v


class OrderSourceUpdate(BaseModel):
    """Order source update model."""
    name: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("name cannot be empty")
            if len(v) > 100:
                raise ValueError("name max length is 100 characters")
        return v


class OrderSourceResponse(BaseModel):
    """Order source response model."""
    id: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderFileResponse(BaseModel):
    """Order file response model."""
    id: str
    order_id: str
    file_id: Optional[str] = None
    url: Optional[str] = None
    filename: str
    file_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """Order creation model."""
    title: str
    customer_id: Optional[str] = None
    source_id: Optional[str] = None
    quoted_price: Optional[float] = None
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    notes: Optional[str] = None
    due_date: Optional[str] = None
    auto_create_job: bool = False
    printer_id: Optional[str] = None  # only used when auto_create_job=True

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty")
        if len(v) > 200:
            raise ValueError("title max length is 200 characters")
        return v

    @field_validator('quoted_price')
    @classmethod
    def validate_quoted_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("quoted_price must be >= 0")
        return v

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        if v is not None and len(v) > 2000:
            raise ValueError("notes max length is 2000 characters")
        return v


class OrderUpdate(BaseModel):
    """Order update model - all fields optional."""
    title: Optional[str] = None
    customer_id: Optional[str] = None
    source_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    quoted_price: Optional[float] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = None
    due_date: Optional[str] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("title cannot be empty")
            if len(v) > 200:
                raise ValueError("title max length is 200 characters")
        return v

    @field_validator('quoted_price')
    @classmethod
    def validate_quoted_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("quoted_price must be >= 0")
        return v

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        if v is not None and len(v) > 2000:
            raise ValueError("notes max length is 2000 characters")
        return v

    class Config:
        use_enum_values = True


class OrderResponse(BaseModel):
    """Order response model."""
    id: str
    title: str
    customer_id: Optional[str] = None
    source_id: Optional[str] = None
    status: OrderStatus
    quoted_price: Optional[float] = None
    payment_status: PaymentStatus
    notes: Optional[str] = None
    due_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Nested related objects (populated by service/router)
    customer: Optional[dict] = None  # CustomerResponse as dict
    source: Optional[OrderSourceResponse] = None
    jobs: List[dict] = []  # JobResponse as dicts
    files: List[OrderFileResponse] = []
    material_cost_eur: float = 0.0
    energy_cost_eur: float = 0.0

    class Config:
        from_attributes = True
        use_enum_values = True
