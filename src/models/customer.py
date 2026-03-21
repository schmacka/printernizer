"""Customer models for Printernizer."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CustomerCreate(BaseModel):
    """Customer creation model."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        if len(v) > 200:
            raise ValueError("name max length is 200 characters")
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None and len(v) > 200:
            raise ValueError("email max length is 200 characters")
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError("phone max length is 50 characters")
        return v

    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError("address max length is 500 characters")
        return v

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError("notes max length is 1000 characters")
        return v


class CustomerUpdate(BaseModel):
    """Customer update model - all fields optional."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("name cannot be empty")
            if len(v) > 200:
                raise ValueError("name max length is 200 characters")
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None and len(v) > 200:
            raise ValueError("email max length is 200 characters")
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError("phone max length is 50 characters")
        return v

    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError("address max length is 500 characters")
        return v

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError("notes max length is 1000 characters")
        return v


class CustomerResponse(BaseModel):
    """Customer response model."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    order_count: int = 0  # computed field

    class Config:
        from_attributes = True
