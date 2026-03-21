"""Customer management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from src.models.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from src.services.order_service import OrderService
from src.utils.dependencies import get_order_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    service: OrderService = Depends(get_order_service)
):
    """List all customers with optional search."""
    customers = await service.list_customers(search=search)
    return customers


@router.post("", status_code=201)
async def create_customer(
    data: CustomerCreate,
    service: OrderService = Depends(get_order_service)
):
    """Create a new customer."""
    customer_id = await service.create_customer(data.model_dump())
    customer = await service.get_customer(customer_id)
    return customer


@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Get customer detail with order history."""
    customer = await service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return customer


@router.put("/{customer_id}")
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    service: OrderService = Depends(get_order_service)
):
    """Update customer."""
    success = await service.update_customer(customer_id, data.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    customer = await service.get_customer(customer_id)
    return customer


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Delete customer. Linked orders will have customer_id set to NULL."""
    success = await service.delete_customer(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
