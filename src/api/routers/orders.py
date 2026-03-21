"""Order management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import structlog

from src.models.order import OrderCreate, OrderUpdate, OrderResponse
from src.services.order_service import OrderService
from src.utils.dependencies import get_order_service

logger = structlog.get_logger()
router = APIRouter()


class LinkJobRequest(BaseModel):
    job_id: Optional[str] = None
    auto_create: bool = False
    printer_id: Optional[str] = None


class AttachFileRequest(BaseModel):
    file_id: Optional[str] = None
    url: Optional[str] = None
    filename: Optional[str] = None
    file_type: Optional[str] = None


@router.get("")
async def list_orders(
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    source_id: Optional[str] = Query(None),
    due_before: Optional[str] = Query(None),
    due_after: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: OrderService = Depends(get_order_service)
):
    """List orders with optional filters."""
    orders, total = await service.list_orders(
        status=status, customer_id=customer_id, source_id=source_id,
        due_before=due_before, due_after=due_after, limit=limit, offset=offset
    )
    return {"orders": orders, "total_count": total}


@router.post("", status_code=201)
async def create_order(
    data: OrderCreate,
    service: OrderService = Depends(get_order_service)
):
    """Create a new order."""
    order_id = await service.create_order(data.model_dump())
    return await service.get_order(order_id)


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Get full order detail with nested customer, source, jobs, files, and costs."""
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@router.put("/{order_id}")
async def update_order(
    order_id: str,
    data: OrderUpdate,
    service: OrderService = Depends(get_order_service)
):
    """Update order. Status transitions are forward-only."""
    try:
        success = await service.update_order(order_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not success:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return await service.get_order(order_id)


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Delete order. Files cascade; linked jobs' order_id set to NULL."""
    success = await service.delete_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")


@router.post("/{order_id}/jobs", status_code=201)
async def link_job(
    order_id: str,
    data: LinkJobRequest,
    service: OrderService = Depends(get_order_service)
):
    """Link existing job to order, or create a draft job and link it."""
    if data.auto_create:
        job_id = await service.create_and_link_job(order_id, data.printer_id)
        if not job_id:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        return {"job_id": job_id, "message": "Draft job created and linked"}
    elif data.job_id:
        result = await service.link_job(order_id, data.job_id)
        if result == 'order_not_found':
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        if result == 'job_not_found':
            raise HTTPException(status_code=404, detail=f"Job {data.job_id} not found")
        if result == 'already_assigned':
            raise HTTPException(status_code=409, detail="Job is already assigned to an order")
        return {"message": "Job linked to order"}
    else:
        raise HTTPException(status_code=400, detail="Provide job_id or set auto_create=true")


@router.delete("/{order_id}/jobs/{job_id}", status_code=204)
async def unlink_job(
    order_id: str,
    job_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Unlink job from order (sets jobs.order_id = NULL)."""
    await service.unlink_job(order_id, job_id)


@router.post("/{order_id}/files", status_code=201)
async def attach_file(
    order_id: str,
    data: AttachFileRequest,
    service: OrderService = Depends(get_order_service)
):
    """Attach a library file or external URL to an order."""
    if not data.file_id and not data.url:
        raise HTTPException(status_code=400, detail="Provide file_id or url")

    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    # Default filename
    filename = data.filename or data.file_id or data.url or 'unknown'

    file_id = await service.attach_file(order_id, {
        'file_id': data.file_id,
        'url': data.url,
        'filename': filename,
        'file_type': data.file_type,
    })
    return {"order_file_id": file_id, "message": "File attached"}


@router.delete("/{order_id}/files/{order_file_id}", status_code=204)
async def detach_file(
    order_id: str,
    order_file_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Detach file from order."""
    await service.detach_file(order_id, order_file_id)
