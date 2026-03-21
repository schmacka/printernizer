"""Order source management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from src.models.order import OrderSourceCreate, OrderSourceUpdate, OrderSourceResponse
from src.services.order_service import OrderService
from src.utils.dependencies import get_order_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=List[OrderSourceResponse])
async def list_sources(
    all: bool = Query(False, description="Include inactive sources"),
    service: OrderService = Depends(get_order_service)
):
    """List order sources. By default, only active ones."""
    return await service.list_sources(include_inactive=all)


@router.post("", status_code=201)
async def create_source(
    data: OrderSourceCreate,
    service: OrderService = Depends(get_order_service)
):
    """Create a new order source."""
    source_id = await service.create_source(data.model_dump())
    source = await service.order_repo.get_source(source_id)
    return source


@router.put("/{source_id}")
async def update_source(
    source_id: str,
    data: OrderSourceUpdate,
    service: OrderService = Depends(get_order_service)
):
    """Rename or toggle active status of an order source."""
    success = await service.update_source(source_id, data.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return await service.order_repo.get_source(source_id)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Delete order source. Returns 409 if referenced by orders."""
    result = await service.delete_source(source_id)
    if result == 'not_found':
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    if result == 'in_use':
        raise HTTPException(status_code=409, detail="Cannot delete source: referenced by existing orders")
