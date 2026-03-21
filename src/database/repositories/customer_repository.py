"""Customer repository for database operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
from .base_repository import BaseRepository

logger = structlog.get_logger()


class CustomerRepository(BaseRepository):
    """Repository for customer CRUD operations."""

    async def create(self, data: Dict[str, Any]) -> bool:
        """Create a new customer."""
        sql = """
            INSERT INTO customers
            (id, name, email, phone, address, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()
        params = (
            data['id'],
            data['name'],
            data.get('email'),
            data.get('phone'),
            data.get('address'),
            data.get('notes'),
            data.get('created_at', now),
            data.get('updated_at', now),
        )
        try:
            await self._execute_write(sql, params)
            logger.info("Created customer", customer_id=data['id'], name=data['name'])
            return True
        except Exception as e:
            logger.error("Failed to create customer", error=str(e), customer_id=data.get('id'))
            return False

    async def get(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID."""
        sql = "SELECT * FROM customers WHERE id = ?"
        return await self._fetch_one(sql, [customer_id])

    async def list(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all customers, optionally filtered by search term (name/email/phone)."""
        if search:
            like = f"%{search}%"
            sql = """
                SELECT * FROM customers
                WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
                ORDER BY name ASC
            """
            return await self._fetch_all(sql, [like, like, like])
        else:
            sql = "SELECT * FROM customers ORDER BY name ASC"
            return await self._fetch_all(sql)

    async def update(self, customer_id: str, data: Dict[str, Any]) -> bool:
        """Update customer fields. Always sets updated_at = CURRENT_TIMESTAMP."""
        if not data:
            return False

        allowed_fields = ('name', 'email', 'phone', 'address', 'notes')
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
        params.append(customer_id)

        sql = f"UPDATE customers SET {', '.join(set_clauses)} WHERE id = ?"
        try:
            await self._execute_write(sql, tuple(params))
            logger.info("Updated customer", customer_id=customer_id, fields=list(data.keys()))
            return True
        except Exception as e:
            logger.error("Failed to update customer", error=str(e), customer_id=customer_id)
            return False

    async def delete(self, customer_id: str) -> bool:
        """Delete a customer. ON DELETE SET NULL on orders.customer_id handles FK."""
        sql = "DELETE FROM customers WHERE id = ?"
        try:
            await self._execute_write(sql, (customer_id,))
            logger.info("Deleted customer", customer_id=customer_id)
            return True
        except Exception as e:
            logger.error("Failed to delete customer", error=str(e), customer_id=customer_id)
            return False

    async def get_order_count(self, customer_id: str) -> int:
        """Get count of orders for a customer."""
        sql = "SELECT COUNT(*) as count FROM orders WHERE customer_id = ?"
        result = await self._fetch_one(sql, [customer_id])
        return result['count'] if result else 0

    async def get_orders_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get summary of orders for a customer (id, title, status, quoted_price, created_at)."""
        sql = """
            SELECT id, title, status, quoted_price, created_at
            FROM orders
            WHERE customer_id = ?
            ORDER BY created_at DESC
        """
        return await self._fetch_all(sql, [customer_id])
