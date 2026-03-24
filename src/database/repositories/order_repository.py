"""Order repository for database operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
from .base_repository import BaseRepository

logger = structlog.get_logger()


class OrderRepository(BaseRepository):
    """Repository for order, order_file, and order_source CRUD operations."""

    # =========================================================================
    # Orders
    # =========================================================================

    async def create_order(self, data: Dict[str, Any]) -> bool:
        """Create a new order."""
        sql = """
            INSERT INTO orders
            (id, title, customer_id, source_id, status, quoted_price,
             payment_status, notes, due_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()
        params = (
            data['id'],
            data['title'],
            data.get('customer_id'),
            data.get('source_id'),
            data.get('status', 'new'),
            data.get('quoted_price'),
            data.get('payment_status', 'unpaid'),
            data.get('notes'),
            data.get('due_date'),
            data.get('created_at', now),
            data.get('updated_at', now),
        )
        try:
            await self._execute_write(sql, params)
            logger.info("Created order", order_id=data['id'], title=data['title'])
            return True
        except Exception as e:
            logger.error("Failed to create order", error=str(e), order_id=data.get('id'))
            return False

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        sql = "SELECT * FROM orders WHERE id = ?"
        return await self._fetch_one(sql, [order_id])

    async def list_orders(
        self,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        source_id: Optional[str] = None,
        due_before: Optional[str] = None,
        due_after: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List orders with optional filters. Ordered by created_at DESC."""
        conditions = []
        params: List[Any] = []

        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if customer_id is not None:
            conditions.append("customer_id = ?")
            params.append(customer_id)
        if source_id is not None:
            conditions.append("source_id = ?")
            params.append(source_id)
        if due_before is not None:
            conditions.append("due_date <= ?")
            params.append(due_before)
        if due_after is not None:
            conditions.append("due_date >= ?")
            params.append(due_after)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM orders
            {where}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        return await self._fetch_all(sql, params)

    async def count_orders(
        self,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> int:
        """Count orders matching filters."""
        conditions = []
        params: List[Any] = []

        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if customer_id is not None:
            conditions.append("customer_id = ?")
            params.append(customer_id)
        if source_id is not None:
            conditions.append("source_id = ?")
            params.append(source_id)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT COUNT(*) as count FROM orders {where}"
        result = await self._fetch_one(sql, params)
        return result['count'] if result else 0

    async def update_order(self, order_id: str, data: Dict[str, Any]) -> bool:
        """Update order fields. Always sets updated_at = CURRENT_TIMESTAMP."""
        if not data:
            return False

        allowed_fields = (
            'title', 'status', 'customer_id', 'source_id',
            'quoted_price', 'payment_status', 'due_date', 'notes',
        )
        set_clauses = []
        params = []

        for key, value in data.items():
            if key in allowed_fields:
                set_clauses.append(f"{key} = ?")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(order_id)

        sql = f"UPDATE orders SET {', '.join(set_clauses)} WHERE id = ?"
        try:
            await self._execute_write(sql, tuple(params))
            logger.info("Updated order", order_id=order_id, fields=list(data.keys()))
            return True
        except Exception as e:
            logger.error("Failed to update order", error=str(e), order_id=order_id)
            return False

    async def delete_order(self, order_id: str) -> bool:
        """Delete order. order_files cascade, jobs.order_id SET NULL."""
        sql = "DELETE FROM orders WHERE id = ?"
        try:
            await self._execute_write(sql, (order_id,))
            logger.info("Deleted order", order_id=order_id)
            return True
        except Exception as e:
            logger.error("Failed to delete order", error=str(e), order_id=order_id)
            return False

    # =========================================================================
    # Job linking
    # =========================================================================

    async def create_draft_job(self, job_data: Dict[str, Any]) -> bool:
        """Insert a draft job row linked to an order."""
        sql = """
            INSERT INTO jobs
            (id, printer_id, printer_type, job_name, status, order_id, is_business, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            job_data['id'],
            job_data['printer_id'],
            job_data['printer_type'],
            job_data['job_name'],
            job_data['status'],
            job_data['order_id'],
            1 if job_data.get('is_business') else 0,
            job_data['created_at'],
            job_data['updated_at'],
        )
        try:
            await self._execute_write(sql, params)
            logger.info("Draft job created for order", job_id=job_data['id'], order_id=job_data['order_id'])
            return True
        except Exception as e:
            logger.error("Failed to create draft job", error=str(e), order_id=job_data.get('order_id'))
            return False

    async def link_job(self, order_id: str, job_id: str) -> bool:
        """Set jobs.order_id = order_id for the given job_id."""
        sql = "UPDATE jobs SET order_id = ? WHERE id = ?"
        try:
            await self._execute_write(sql, (order_id, job_id))
            logger.info("Linked job to order", job_id=job_id, order_id=order_id)
            return True
        except Exception as e:
            logger.error("Failed to link job to order", error=str(e),
                         job_id=job_id, order_id=order_id)
            return False

    async def unlink_job(self, job_id: str) -> bool:
        """Set jobs.order_id = NULL for the given job_id."""
        sql = "UPDATE jobs SET order_id = NULL WHERE id = ?"
        try:
            await self._execute_write(sql, (job_id,))
            logger.info("Unlinked job from order", job_id=job_id)
            return True
        except Exception as e:
            logger.error("Failed to unlink job from order", error=str(e), job_id=job_id)
            return False

    async def get_jobs_for_order(self, order_id: str) -> List[Dict[str, Any]]:
        """Get all jobs linked to an order."""
        sql = "SELECT * FROM jobs WHERE order_id = ? ORDER BY created_at DESC"
        return await self._fetch_all(sql, [order_id])

    async def get_job_order_id(self, job_id: str) -> Optional[str]:
        """Get the order_id for a job (to check if already assigned)."""
        sql = "SELECT order_id FROM jobs WHERE id = ?"
        result = await self._fetch_one(sql, [job_id])
        if result is None:
            return None
        return result.get('order_id')

    # =========================================================================
    # Order files
    # =========================================================================

    async def add_file(self, data: Dict[str, Any]) -> bool:
        """Add a file to an order."""
        sql = """
            INSERT INTO order_files
            (id, order_id, file_id, url, filename, file_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()
        params = (
            data['id'],
            data['order_id'],
            data.get('file_id'),
            data.get('url'),
            data['filename'],
            data.get('file_type'),
            data.get('created_at', now),
        )
        try:
            await self._execute_write(sql, params)
            logger.info("Added file to order", order_file_id=data['id'],
                        order_id=data['order_id'], filename=data['filename'])
            return True
        except Exception as e:
            logger.error("Failed to add file to order", error=str(e),
                         order_id=data.get('order_id'))
            return False

    async def remove_file(self, order_file_id: str) -> bool:
        """Remove a file from an order by order_file id."""
        sql = "DELETE FROM order_files WHERE id = ?"
        try:
            await self._execute_write(sql, (order_file_id,))
            logger.info("Removed order file", order_file_id=order_file_id)
            return True
        except Exception as e:
            logger.error("Failed to remove order file", error=str(e),
                         order_file_id=order_file_id)
            return False

    async def get_files_for_order(self, order_id: str) -> List[Dict[str, Any]]:
        """Get all files for an order."""
        sql = "SELECT * FROM order_files WHERE order_id = ? ORDER BY created_at ASC"
        return await self._fetch_all(sql, [order_id])

    # =========================================================================
    # Order sources
    # =========================================================================

    async def create_source(self, data: Dict[str, Any]) -> bool:
        """Create a new order source."""
        sql = """
            INSERT INTO order_sources
            (id, name, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()
        params = (
            data['id'],
            data['name'],
            1 if data.get('is_active', True) else 0,
            data.get('created_at', now),
            data.get('updated_at', now),
        )
        try:
            await self._execute_write(sql, params)
            logger.info("Created order source", source_id=data['id'], name=data['name'])
            return True
        except Exception as e:
            logger.error("Failed to create order source", error=str(e),
                         source_id=data.get('id'))
            return False

    async def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get order source by ID."""
        sql = "SELECT * FROM order_sources WHERE id = ?"
        result = await self._fetch_one(sql, [source_id])
        if result:
            result['is_active'] = bool(result.get('is_active', 1))
        return result

    async def list_sources(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """List order sources. By default, only active ones."""
        if include_inactive:
            sql = "SELECT * FROM order_sources ORDER BY name ASC"
            results = await self._fetch_all(sql)
        else:
            sql = "SELECT * FROM order_sources WHERE is_active = 1 ORDER BY name ASC"
            results = await self._fetch_all(sql)

        for result in results:
            result['is_active'] = bool(result.get('is_active', 1))
        return results

    async def update_source(self, source_id: str, data: Dict[str, Any]) -> bool:
        """Update order source. Always sets updated_at = CURRENT_TIMESTAMP."""
        if not data:
            return False

        allowed_fields = ('name', 'is_active')
        set_clauses = []
        params = []

        for key, value in data.items():
            if key in allowed_fields:
                set_clauses.append(f"{key} = ?")
                if key == 'is_active':
                    params.append(1 if value else 0)
                else:
                    params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(source_id)

        sql = f"UPDATE order_sources SET {', '.join(set_clauses)} WHERE id = ?"
        try:
            await self._execute_write(sql, tuple(params))
            logger.info("Updated order source", source_id=source_id,
                        fields=list(data.keys()))
            return True
        except Exception as e:
            logger.error("Failed to update order source", error=str(e),
                         source_id=source_id)
            return False

    async def delete_source(self, source_id: str) -> bool:
        """Delete order source. Returns False if referenced by orders (RESTRICT)."""
        if await self.is_source_in_use(source_id):
            logger.warning("Cannot delete order source in use by orders",
                           source_id=source_id)
            return False

        sql = "DELETE FROM order_sources WHERE id = ?"
        try:
            await self._execute_write(sql, (source_id,))
            logger.info("Deleted order source", source_id=source_id)
            return True
        except Exception as e:
            logger.error("Failed to delete order source", error=str(e),
                         source_id=source_id)
            return False

    async def get_computed_costs(self, order_id: str) -> Dict[str, float]:
        """Compute material_cost_eur and energy_cost_eur by summing linked jobs."""
        sql = """
            SELECT
                COALESCE(SUM(material_cost), 0) AS material_cost_eur,
                COALESCE(SUM(power_cost), 0) AS energy_cost_eur
            FROM jobs
            WHERE order_id = ?
        """
        result = await self._fetch_one(sql, [order_id])
        if result:
            return {
                'material_cost_eur': float(result['material_cost_eur']),
                'energy_cost_eur': float(result['energy_cost_eur']),
            }
        return {'material_cost_eur': 0.0, 'energy_cost_eur': 0.0}

    async def is_source_in_use(self, source_id: str) -> bool:
        """Check if any order references this source."""
        sql = "SELECT COUNT(*) as count FROM orders WHERE source_id = ?"
        result = await self._fetch_one(sql, [source_id])
        return (result['count'] if result else 0) > 0
