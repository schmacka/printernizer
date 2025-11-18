"""
Material management service for Printernizer.
Handles material inventory, consumption tracking, and cost calculations.
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

import aiofiles
import structlog

from src.database.database import Database
from src.models.material import (
    MaterialSpool,
    MaterialCreate,
    MaterialUpdate,
    MaterialConsumption,
    MaterialStats,
    MaterialReport,
    MaterialType,
    MaterialBrand,
    MaterialColor
)
from src.services.event_service import EventService


logger = structlog.get_logger(__name__)


class MaterialService:
    """Service for managing material inventory and consumption."""

    def __init__(self, db: Database, event_service: EventService):
        """Initialize material service."""
        self.db = db
        self.event_service = event_service
        self.materials_cache: Dict[str, MaterialSpool] = {}
        self._init_task = None

    async def initialize(self) -> None:
        """Initialize material service and create tables."""
        try:
            await self._create_tables()
            await self._load_materials()
            logger.info("Material service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize material service: {e}")
            raise

    async def _create_tables(self) -> None:
        """Create material-related database tables."""
        async with self.db.connection() as conn:
            # Materials table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS materials (
                    id TEXT PRIMARY KEY,
                    material_type TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    color TEXT NOT NULL,
                    diameter REAL NOT NULL,
                    weight REAL NOT NULL,
                    remaining_weight REAL NOT NULL,
                    cost_per_kg DECIMAL(10,2) DEFAULT 0,
                    purchase_date TIMESTAMP NOT NULL,
                    vendor TEXT NOT NULL,
                    batch_number TEXT,
                    notes TEXT,
                    printer_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE SET NULL
                )
            ''')

            # Material consumption table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS material_consumption (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    material_id TEXT NOT NULL,
                    weight_used REAL NOT NULL,
                    cost DECIMAL(10,2) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    printer_id TEXT NOT NULL,
                    file_name TEXT,
                    print_time_hours REAL,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
                    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE CASCADE
                )
            ''')

            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_materials_printer ON materials(printer_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_materials_type ON materials(material_type)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_consumption_job ON material_consumption(job_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_consumption_material ON material_consumption(material_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_consumption_timestamp ON material_consumption(timestamp)')

            await conn.commit()

    async def _load_materials(self) -> None:
        """Load materials from database into cache."""
        async with self.db.connection() as conn:
            cursor = await conn.execute('SELECT * FROM materials ORDER BY created_at DESC')
            rows = await cursor.fetchall()

            self.materials_cache.clear()
            for row in rows:
                material = self._row_to_material(row)
                self.materials_cache[material.id] = material

    def _row_to_material(self, row) -> MaterialSpool:
        """Convert database row to MaterialSpool."""
        return MaterialSpool(
            id=row['id'],
            material_type=MaterialType(row['material_type']),
            brand=MaterialBrand(row['brand']),
            color=MaterialColor(row['color']),
            diameter=row['diameter'],
            weight=row['weight'],
            remaining_weight=row['remaining_weight'],
            cost_per_kg=Decimal(str(row['cost_per_kg'])),
            purchase_date=datetime.fromisoformat(row['purchase_date']),
            vendor=row['vendor'],
            batch_number=row['batch_number'],
            notes=row['notes'],
            printer_id=row['printer_id'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    async def create_material(self, material_data: MaterialCreate) -> MaterialSpool:
        """Create a new material spool."""
        material_id = str(uuid4())
        now = datetime.now()

        material = MaterialSpool(
            id=material_id,
            material_type=material_data.material_type,
            brand=material_data.brand,
            color=material_data.color,
            diameter=material_data.diameter,
            weight=material_data.weight,
            remaining_weight=material_data.remaining_weight,
            cost_per_kg=material_data.cost_per_kg,
            purchase_date=now,
            vendor=material_data.vendor,
            batch_number=material_data.batch_number,
            notes=material_data.notes,
            printer_id=material_data.printer_id,
            created_at=now,
            updated_at=now
        )

        async with self.db.connection() as conn:
            await conn.execute('''
                INSERT INTO materials (
                    id, material_type, brand, color, diameter, weight,
                    remaining_weight, cost_per_kg, purchase_date, vendor,
                    batch_number, notes, printer_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                material.id, material.material_type.value, material.brand.value,
                material.color.value, material.diameter, material.weight,
                material.remaining_weight, str(material.cost_per_kg),
                material.purchase_date.isoformat(), material.vendor,
                material.batch_number, material.notes, material.printer_id,
                material.created_at.isoformat(), material.updated_at.isoformat()
            ))
            await conn.commit()

        self.materials_cache[material.id] = material
        await self.event_service.emit_event('material_created', {'material': material.__dict__})

        return material

    async def update_material(self, material_id: str, update_data: MaterialUpdate) -> Optional[MaterialSpool]:
        """Update material spool."""
        if material_id not in self.materials_cache:
            return None

        material = self.materials_cache[material_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            return material

        # Update fields
        for field, value in update_dict.items():
            if hasattr(material, field):
                setattr(material, field, value)

        material.updated_at = datetime.now()

        # Update database
        async with self.db.connection() as conn:
            set_clauses = []
            values = []
            for field, value in update_dict.items():
                set_clauses.append(f"{field} = ?")
                if isinstance(value, Decimal):
                    values.append(str(value))
                else:
                    values.append(value)

            set_clauses.append("updated_at = ?")
            values.append(material.updated_at.isoformat())
            values.append(material_id)

            query = f"UPDATE materials SET {', '.join(set_clauses)} WHERE id = ?"
            await conn.execute(query, values)
            await conn.commit()

        await self.event_service.emit_event('material_updated', {'material': material.__dict__})
        return material

    async def delete_material(self, material_id: str) -> bool:
        """Delete a material spool from inventory."""
        if material_id not in self.materials_cache:
            return False

        # Delete from database
        async with self.db.connection() as conn:
            await conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))
            await conn.commit()

        # Remove from cache
        material = self.materials_cache.pop(material_id)

        await self.event_service.emit_event('material_deleted', {'material_id': material_id})
        logger.info(f"Deleted material {material_id}")
        return True

    async def record_consumption(self, job_id: str, material_id: str,
                                weight_grams: float, printer_id: str,
                                file_name: Optional[str] = None,
                                print_time_hours: Optional[float] = None) -> MaterialConsumption:
        """Record material consumption for a job."""
        if material_id not in self.materials_cache:
            raise ValueError(f"Material {material_id} not found")

        material = self.materials_cache[material_id]
        weight_kg = weight_grams / 1000
        cost = Decimal(str(weight_kg)) * material.cost_per_kg

        consumption = MaterialConsumption(
            job_id=job_id,
            material_id=material_id,
            weight_used=weight_grams,
            cost=cost,
            printer_id=printer_id,
            file_name=file_name,
            print_time_hours=print_time_hours
        )

        # Update material remaining weight
        material.remaining_weight = max(0, material.remaining_weight - weight_kg)
        material.updated_at = datetime.now()

        async with self.db.connection() as conn:
            # Insert consumption record
            consumption_id = str(uuid4())
            await conn.execute('''
                INSERT INTO material_consumption (
                    id, job_id, material_id, weight_used, cost, timestamp,
                    printer_id, file_name, print_time_hours
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                consumption_id, consumption.job_id, consumption.material_id,
                consumption.weight_used, str(consumption.cost),
                consumption.timestamp.isoformat(), consumption.printer_id,
                consumption.file_name, consumption.print_time_hours
            ))

            # Update material remaining weight
            await conn.execute('''
                UPDATE materials
                SET remaining_weight = ?, updated_at = ?
                WHERE id = ?
            ''', (material.remaining_weight, material.updated_at.isoformat(), material_id))

            await conn.commit()

        # Check for low stock
        if material.remaining_percentage < 20:
            await self.event_service.emit_event('material_low_stock', {
                'material_id': material_id,
                'remaining_percentage': material.remaining_percentage,
                'remaining_weight': material.remaining_weight
            })

        return consumption

    async def get_material(self, material_id: str) -> Optional[MaterialSpool]:
        """Get material by ID."""
        return self.materials_cache.get(material_id)

    async def get_all_materials(self) -> List[MaterialSpool]:
        """Get all materials."""
        return list(self.materials_cache.values())

    async def get_materials_by_type(self, material_type: MaterialType) -> List[MaterialSpool]:
        """Get materials by type."""
        return [m for m in self.materials_cache.values() if m.material_type == material_type]

    async def get_materials_by_printer(self, printer_id: str) -> List[MaterialSpool]:
        """Get materials loaded in a specific printer."""
        return [m for m in self.materials_cache.values() if m.printer_id == printer_id]

    async def get_low_stock_materials(self, threshold: float = 20.0) -> List[MaterialSpool]:
        """Get materials below stock threshold percentage."""
        return [m for m in self.materials_cache.values() if m.remaining_percentage < threshold]

    async def get_statistics(self) -> MaterialStats:
        """Get material statistics."""
        materials = list(self.materials_cache.values())

        if not materials:
            return MaterialStats(
                total_spools=0,
                total_weight=0,
                total_remaining=0,
                total_value=Decimal(0),
                remaining_value=Decimal(0),
                by_type={},
                by_brand={},
                by_color={},
                low_stock=[],
                consumption_30d=0,
                consumption_rate=0
            )

        # Calculate basic stats
        total_weight = sum(m.weight for m in materials)
        total_remaining = sum(m.remaining_weight for m in materials)
        total_value = sum(m.total_cost for m in materials)
        remaining_value = sum(m.remaining_value for m in materials)

        # Group by type
        by_type = {}
        for material in materials:
            type_key = material.material_type.value
            if type_key not in by_type:
                by_type[type_key] = {
                    'count': 0,
                    'total_weight': 0,
                    'remaining_weight': 0,
                    'value': Decimal(0)
                }
            by_type[type_key]['count'] += 1
            by_type[type_key]['total_weight'] += material.weight
            by_type[type_key]['remaining_weight'] += material.remaining_weight
            by_type[type_key]['value'] += material.remaining_value

        # Group by brand
        by_brand = {}
        for material in materials:
            brand_key = material.brand.value
            if brand_key not in by_brand:
                by_brand[brand_key] = {
                    'count': 0,
                    'total_weight': 0,
                    'remaining_weight': 0
                }
            by_brand[brand_key]['count'] += 1
            by_brand[brand_key]['total_weight'] += material.weight
            by_brand[brand_key]['remaining_weight'] += material.remaining_weight

        # Count by color
        by_color = {}
        for material in materials:
            color_key = material.color.value
            by_color[color_key] = by_color.get(color_key, 0) + 1

        # Get low stock materials
        low_stock = [m.id for m in materials if m.remaining_percentage < 20]

        # Calculate consumption rate (last 30 days)
        consumption_30d = await self._calculate_consumption_period(30)
        consumption_rate = consumption_30d / 30 if consumption_30d > 0 else 0

        return MaterialStats(
            total_spools=len(materials),
            total_weight=total_weight,
            total_remaining=total_remaining,
            total_value=total_value,
            remaining_value=remaining_value,
            by_type=by_type,
            by_brand=by_brand,
            by_color=by_color,
            low_stock=low_stock,
            consumption_30d=consumption_30d,
            consumption_rate=consumption_rate
        )

    async def _calculate_consumption_period(self, days: int) -> float:
        """Calculate total consumption in kg for a period."""
        since = datetime.now() - timedelta(days=days)

        async with self.db.connection() as conn:
            cursor = await conn.execute('''
                SELECT SUM(weight_used) as total
                FROM material_consumption
                WHERE timestamp >= ?
            ''', (since.isoformat(),))

            row = await cursor.fetchone()
            if row and row['total']:
                return row['total'] / 1000  # Convert grams to kg
            return 0

    async def generate_report(self, start_date: datetime, end_date: datetime) -> MaterialReport:
        """Generate material consumption report for a period."""
        async with self.db.connection() as conn:
            # Get consumption data for period
            cursor = await conn.execute('''
                SELECT mc.*, m.material_type, m.brand, m.color, j.is_business
                FROM material_consumption mc
                JOIN materials m ON mc.material_id = m.id
                LEFT JOIN jobs j ON mc.job_id = j.id
                WHERE mc.timestamp BETWEEN ? AND ?
                ORDER BY mc.timestamp DESC
            ''', (start_date.isoformat(), end_date.isoformat()))

            consumptions = await cursor.fetchall()

        if not consumptions:
            return MaterialReport(
                period_start=start_date,
                period_end=end_date,
                total_consumed=0,
                total_cost=Decimal(0),
                by_material={},
                by_printer={},
                by_job_type={},
                top_consumers=[],
                efficiency_metrics={}
            )

        # Calculate totals
        total_consumed = sum(c['weight_used'] for c in consumptions) / 1000  # to kg
        total_cost = sum(Decimal(str(c['cost'])) for c in consumptions)

        # Group by material type
        by_material = {}
        for c in consumptions:
            key = f"{c['material_type']}_{c['color']}"
            if key not in by_material:
                by_material[key] = {
                    'weight_kg': 0,
                    'cost': Decimal(0),
                    'jobs': 0
                }
            by_material[key]['weight_kg'] += c['weight_used'] / 1000
            by_material[key]['cost'] += Decimal(str(c['cost']))
            by_material[key]['jobs'] += 1

        # Group by printer
        by_printer = {}
        for c in consumptions:
            printer_id = c['printer_id']
            if printer_id not in by_printer:
                by_printer[printer_id] = {
                    'weight_kg': 0,
                    'cost': Decimal(0),
                    'jobs': 0
                }
            by_printer[printer_id]['weight_kg'] += c['weight_used'] / 1000
            by_printer[printer_id]['cost'] += Decimal(str(c['cost']))
            by_printer[printer_id]['jobs'] += 1

        # Group by job type
        by_job_type = {'business': {'weight_kg': 0, 'cost': Decimal(0), 'count': 0},
                      'private': {'weight_kg': 0, 'cost': Decimal(0), 'count': 0}}

        for c in consumptions:
            job_type = 'business' if c.get('is_business') else 'private'
            by_job_type[job_type]['weight_kg'] += c['weight_used'] / 1000
            by_job_type[job_type]['cost'] += Decimal(str(c['cost']))
            by_job_type[job_type]['count'] += 1

        # Get top consuming jobs
        job_totals = {}
        for c in consumptions:
            job_id = c['job_id']
            if job_id not in job_totals:
                job_totals[job_id] = {
                    'job_id': job_id,
                    'file_name': c.get('file_name', 'Unknown'),
                    'weight_kg': 0,
                    'cost': Decimal(0)
                }
            job_totals[job_id]['weight_kg'] += c['weight_used'] / 1000
            job_totals[job_id]['cost'] += Decimal(str(c['cost']))

        top_consumers = sorted(job_totals.values(),
                              key=lambda x: x['weight_kg'],
                              reverse=True)[:10]

        # Calculate efficiency metrics
        total_print_time = sum(c['print_time_hours'] for c in consumptions
                             if c['print_time_hours'])
        avg_consumption_per_hour = total_consumed / total_print_time if total_print_time > 0 else 0

        efficiency_metrics = {
            'avg_consumption_per_hour': avg_consumption_per_hour,
            'avg_cost_per_job': float(total_cost / len(set(c['job_id'] for c in consumptions))),
            'material_utilization': 0.95  # Placeholder - would need waste tracking
        }

        return MaterialReport(
            period_start=start_date,
            period_end=end_date,
            total_consumed=total_consumed,
            total_cost=total_cost,
            by_material=by_material,
            by_printer=by_printer,
            by_job_type=by_job_type,
            top_consumers=top_consumers,
            efficiency_metrics=efficiency_metrics
        )

    async def export_inventory(self, file_path: Path) -> bool:
        """Export material inventory to CSV."""
        try:
            materials = list(self.materials_cache.values())

            csv_lines = [
                "ID,Type,Brand,Color,Diameter,Weight,Remaining,Cost/kg,Value,Vendor,Batch,Notes"
            ]

            for m in materials:
                csv_lines.append(
                    f"{m.id},{m.material_type.value},{m.brand.value},{m.color.value},"
                    f"{m.diameter},{m.weight},{m.remaining_weight},{m.cost_per_kg},"
                    f"{m.remaining_value},{m.vendor},{m.batch_number or ''},{m.notes or ''}"
                )

            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write('\n'.join(csv_lines))

            logger.info(f"Exported {len(materials)} materials to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export inventory: {e}")
            return False

    async def cleanup(self):
        """Clean up material service resources."""
        self.materials_cache.clear()
        logger.info("Material service cleaned up")