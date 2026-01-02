"""
Material management API endpoints.
Provides REST API for material inventory and consumption tracking.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.models.material import (
    MaterialCreate,
    MaterialUpdate,
    MaterialSpool,
    MaterialStats,
    MaterialReport,
    MaterialConsumption,
    MaterialType,
    MaterialBrand,
    MaterialColor,
    ConsumptionHistoryItem,
    ConsumptionHistoryResponse
)
from src.services.material_service import MaterialService
from src.utils.dependencies import get_material_service
from src.utils.errors import (
    MaterialNotFoundError,
    ValidationError as PrinternizerValidationError,
    success_response
)


router = APIRouter(prefix="/materials", tags=["Materials"])


class MaterialResponse(BaseModel):
    """Response model for material operations."""
    id: str
    material_type: str
    brand: str
    color: str
    diameter: float
    weight: float
    remaining_weight: float
    remaining_percentage: float
    cost_per_kg: Decimal  # Can be 0 if not tracked
    remaining_value: Decimal
    vendor: str
    batch_number: Optional[str]
    notes: Optional[str]
    printer_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConsumptionRequest(BaseModel):
    """Request model for recording material consumption."""
    job_id: str
    material_id: str
    weight_grams: float = Field(gt=0, le=10000)
    printer_id: str
    file_name: Optional[str] = None
    print_time_hours: Optional[float] = Field(None, gt=0, le=1000)


@router.get("", response_model=List[MaterialResponse])
async def get_materials(
    material_type: Optional[MaterialType] = None,
    brand: Optional[MaterialBrand] = None,
    color: Optional[MaterialColor] = None,
    low_stock: bool = False,
    printer_id: Optional[str] = None,
    material_service: MaterialService = Depends(get_material_service)
):
    """Get all materials with optional filters."""
    materials = await material_service.get_all_materials()

    # Apply filters
    if material_type:
        materials = [m for m in materials if m.material_type == material_type]
    if brand:
        materials = [m for m in materials if m.brand == brand]
    if color:
        materials = [m for m in materials if m.color == color]
    if low_stock:
        materials = [m for m in materials if m.remaining_percentage < 20]
    if printer_id:
        materials = [m for m in materials if m.printer_id == printer_id]

    return [
        MaterialResponse(
            id=m.id,
            material_type=m.material_type.value,
            brand=m.brand.value,
            color=m.color.value,
            diameter=m.diameter,
            weight=m.weight,
            remaining_weight=m.remaining_weight,
            remaining_percentage=m.remaining_percentage,
            cost_per_kg=m.cost_per_kg,
            remaining_value=m.remaining_value,
            vendor=m.vendor,
            batch_number=m.batch_number,
            notes=m.notes,
            printer_id=m.printer_id,
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in materials
    ]


@router.get("/stats", response_model=MaterialStats)
async def get_material_stats(
    material_service: MaterialService = Depends(get_material_service)
):
    """Get material inventory statistics."""
    return await material_service.get_statistics()


@router.get("/types")
async def get_material_types():
    """Get available material types."""
    return {
        "types": [t.value for t in MaterialType],
        "brands": [b.value for b in MaterialBrand],
        "colors": [c.value for c in MaterialColor]
    }


@router.get("/report", response_model=MaterialReport)
async def get_consumption_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    material_service: MaterialService = Depends(get_material_service)
):
    """Generate material consumption report for a date range."""
    if end_date <= start_date:
        raise PrinternizerValidationError(
            field="end_date",
            error="End date must be after start date"
        )

    return await material_service.generate_report(start_date, end_date)


@router.get("/export")
async def export_inventory(
    format: str = Query("csv", pattern="^(csv|excel)$"),
    material_service: MaterialService = Depends(get_material_service)
):
    """Export material inventory to file."""
    export_path = Path(f"exports/materials_{datetime.now():%Y%m%d_%H%M%S}.{format}")
    export_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "csv":
        success = await material_service.export_inventory(export_path)
        if success:
            return FileResponse(
                path=str(export_path),
                media_type="text/csv",
                filename=export_path.name
            )
    else:
        # Excel export would go here
        raise HTTPException(501, "Excel export not yet implemented")

    raise HTTPException(500, "Export failed")


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    material_service: MaterialService = Depends(get_material_service)
):
    """Get a specific material by ID."""
    material = await material_service.get_material(material_id)
    if not material:
        raise MaterialNotFoundError(material_id)

    return MaterialResponse(
        id=material.id,
        material_type=material.material_type.value,
        brand=material.brand.value,
        color=material.color.value,
        diameter=material.diameter,
        weight=material.weight,
        remaining_weight=material.remaining_weight,
        remaining_percentage=material.remaining_percentage,
        cost_per_kg=material.cost_per_kg,
        remaining_value=material.remaining_value,
        vendor=material.vendor,
        batch_number=material.batch_number,
        notes=material.notes,
        printer_id=material.printer_id,
        created_at=material.created_at,
        updated_at=material.updated_at
    )


@router.post("", response_model=MaterialResponse, status_code=201)
async def create_material(
    material_data: MaterialCreate,
    material_service: MaterialService = Depends(get_material_service)
):
    """Create a new material spool."""
    try:
        material = await material_service.create_material(material_data)

        return MaterialResponse(
            id=material.id,
            material_type=material.material_type.value,
            brand=material.brand.value,
            color=material.color.value,
            diameter=material.diameter,
            weight=material.weight,
            remaining_weight=material.remaining_weight,
            remaining_percentage=material.remaining_percentage,
            cost_per_kg=material.cost_per_kg,
            remaining_value=material.remaining_value,
            vendor=material.vendor,
            batch_number=material.batch_number,
            notes=material.notes,
            printer_id=material.printer_id,
            created_at=material.created_at,
            updated_at=material.updated_at
        )
    except ValueError as e:
        raise PrinternizerValidationError(field="material_data", error=str(e))


@router.patch("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: str,
    update_data: MaterialUpdate,
    material_service: MaterialService = Depends(get_material_service)
):
    """Update material information."""
    material = await material_service.update_material(material_id, update_data)
    if not material:
        raise MaterialNotFoundError(material_id)

    return MaterialResponse(
        id=material.id,
        material_type=material.material_type.value,
        brand=material.brand.value,
        color=material.color.value,
        diameter=material.diameter,
        weight=material.weight,
        remaining_weight=material.remaining_weight,
        remaining_percentage=material.remaining_percentage,
        cost_per_kg=material.cost_per_kg,
        remaining_value=material.remaining_value,
        vendor=material.vendor,
        batch_number=material.batch_number,
        notes=material.notes,
        printer_id=material.printer_id,
        created_at=material.created_at,
        updated_at=material.updated_at
    )


@router.post("/consumption", response_model=dict, status_code=201)
async def record_consumption(
    consumption_data: ConsumptionRequest,
    material_service: MaterialService = Depends(get_material_service)
):
    """Record material consumption for a job."""
    try:
        consumption = await material_service.record_consumption(
            job_id=consumption_data.job_id,
            material_id=consumption_data.material_id,
            weight_grams=consumption_data.weight_grams,
            printer_id=consumption_data.printer_id,
            file_name=consumption_data.file_name,
            print_time_hours=consumption_data.print_time_hours
        )

        return success_response({
            "message": "Consumption recorded successfully",
            "consumption": {
                "job_id": consumption.job_id,
                "material_id": consumption.material_id,
                "weight_grams": consumption.weight_used,
                "weight_kg": consumption.weight_used_kg,
                "cost": float(consumption.cost),
                "timestamp": consumption.timestamp
            }
        })
    except ValueError as e:
        raise PrinternizerValidationError(field="consumption_data", error=str(e))


@router.delete("/{material_id}", status_code=204)
async def delete_material(
    material_id: str,
    material_service: MaterialService = Depends(get_material_service)
):
    """Delete a material spool from inventory."""
    success = await material_service.delete_material(material_id)
    if not success:
        raise MaterialNotFoundError(material_id)
    return Response(status_code=204)


@router.get("/consumption/history", response_model=ConsumptionHistoryResponse)
async def get_consumption_history(
    material_id: Optional[str] = Query(None, description="Filter by material ID"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    printer_id: Optional[str] = Query(None, description="Filter by printer ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=1000, description="Results per page"),
    page: int = Query(1, ge=1, description="Page number"),
    material_service: MaterialService = Depends(get_material_service)
) -> ConsumptionHistoryResponse:
    """Get material consumption history with optional filters and pagination."""
    items, total_count = await material_service.get_consumption_history(
        material_id=material_id,
        job_id=job_id,
        printer_id=printer_id,
        days=days,
        limit=limit,
        page=page
    )

    total_pages = max(1, (total_count + limit - 1) // limit)

    return ConsumptionHistoryResponse(
        items=[ConsumptionHistoryItem(**item) for item in items],
        total_count=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages
    )