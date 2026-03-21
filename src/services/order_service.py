"""Order service for managing customer orders."""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import structlog
from src.database.database import Database
from src.database.repositories.order_repository import OrderRepository
from src.database.repositories.customer_repository import CustomerRepository

logger = structlog.get_logger()


class OrderService:
    """Service for managing orders, customers, and order sources."""

    # Valid status transitions (forward-only)
    STATUS_TRANSITIONS = {
        'new': ['planned'],
        'planned': ['printed'],
        'printed': ['delivered'],
        'delivered': [],  # terminal
    }

    def __init__(self, database: Database):
        self.order_repo = OrderRepository(database._connection)
        self.customer_repo = CustomerRepository(database._connection)
        self.database = database

    # ===================== Customer methods =====================

    async def list_customers(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """List customers with optional search."""
        customers = await self.customer_repo.list(search=search)
        # Add order_count to each customer
        for c in customers:
            c['order_count'] = await self.customer_repo.get_order_count(c['id'])
        return customers

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer with order_count and orders list."""
        customer = await self.customer_repo.get(customer_id)
        if not customer:
            return None
        customer['order_count'] = await self.customer_repo.get_order_count(customer_id)
        customer['orders'] = await self.customer_repo.get_orders_for_customer(customer_id)
        return customer

    async def create_customer(self, data: Dict[str, Any]) -> str:
        """Create a customer. Returns new customer ID."""
        customer_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        db_data = {
            'id': customer_id,
            'name': data['name'],
            'email': data.get('email'),
            'phone': data.get('phone'),
            'address': data.get('address'),
            'notes': data.get('notes'),
            'created_at': now,
            'updated_at': now,
        }
        success = await self.customer_repo.create(db_data)
        if not success:
            raise Exception("Failed to create customer")
        logger.info("Customer created", customer_id=customer_id)
        return customer_id

    async def update_customer(self, customer_id: str, data: Dict[str, Any]) -> bool:
        """Update customer fields."""
        existing = await self.customer_repo.get(customer_id)
        if not existing:
            return False
        # Only pass non-None fields
        update_data = {k: v for k, v in data.items() if v is not None}
        return await self.customer_repo.update(customer_id, update_data)

    async def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer (orders.customer_id → NULL via FK)."""
        existing = await self.customer_repo.get(customer_id)
        if not existing:
            return False
        return await self.customer_repo.delete(customer_id)

    # ===================== Order source methods =====================

    async def list_sources(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        return await self.order_repo.list_sources(include_inactive=include_inactive)

    async def create_source(self, data: Dict[str, Any]) -> str:
        source_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        db_data = {'id': source_id, 'name': data['name'], 'is_active': 1, 'created_at': now, 'updated_at': now}
        success = await self.order_repo.create_source(db_data)
        if not success:
            raise Exception("Failed to create order source")
        return source_id

    async def update_source(self, source_id: str, data: Dict[str, Any]) -> bool:
        existing = await self.order_repo.get_source(source_id)
        if not existing:
            return False
        update_data = {}
        if data.get('name') is not None:
            update_data['name'] = data['name']
        if data.get('is_active') is not None:
            update_data['is_active'] = 1 if data['is_active'] else 0
        if not update_data:
            return True
        return await self.order_repo.update_source(source_id, update_data)

    async def delete_source(self, source_id: str) -> str:
        """Delete source. Returns 'not_found', 'in_use', or 'deleted'."""
        existing = await self.order_repo.get_source(source_id)
        if not existing:
            return 'not_found'
        if await self.order_repo.is_source_in_use(source_id):
            return 'in_use'
        await self.order_repo.delete_source(source_id)
        return 'deleted'

    # ===================== Order methods =====================

    def _validate_status_transition(self, current: str, new: str) -> None:
        """Raise ValueError if transition is not allowed."""
        allowed = self.STATUS_TRANSITIONS.get(current, [])
        if new not in allowed:
            raise ValueError(
                f"Invalid status transition: {current} → {new}. "
                f"Allowed: {allowed if allowed else 'none (terminal state)'}"
            )

    async def list_orders(self, status=None, customer_id=None, source_id=None,
                          due_before=None, due_after=None, limit=100, offset=0) -> tuple:
        """Returns (orders list, total count)."""
        orders = await self.order_repo.list_orders(
            status=status, customer_id=customer_id, source_id=source_id,
            due_before=due_before, due_after=due_after, limit=limit, offset=offset
        )
        total = await self.order_repo.count_orders(
            status=status, customer_id=customer_id, source_id=source_id
        )
        return orders, total

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get full order with nested customer, source, jobs, files, and computed costs."""
        order = await self.order_repo.get_order(order_id)
        if not order:
            return None

        # Nested customer
        if order.get('customer_id'):
            customer = await self.customer_repo.get(order['customer_id'])
            order['customer'] = customer
        else:
            order['customer'] = None

        # Nested source
        if order.get('source_id'):
            source = await self.order_repo.get_source(order['source_id'])
            order['source'] = source
        else:
            order['source'] = None

        # Linked jobs
        order['jobs'] = await self.order_repo.get_jobs_for_order(order_id)

        # Attached files
        order['files'] = await self.order_repo.get_files_for_order(order_id)

        # Computed costs
        costs = await self.order_repo.get_computed_costs(order_id)
        order['material_cost_eur'] = costs['material_cost_eur']
        order['energy_cost_eur'] = costs['energy_cost_eur']

        return order

    async def create_order(self, data: Dict[str, Any]) -> str:
        """Create order. If auto_create_job=True, also creates a linked draft job."""
        order_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        db_data = {
            'id': order_id,
            'title': data['title'],
            'customer_id': data.get('customer_id'),
            'source_id': data.get('source_id'),
            'status': 'new',
            'quoted_price': data.get('quoted_price'),
            'payment_status': data.get('payment_status', 'unpaid'),
            'notes': data.get('notes'),
            'due_date': data.get('due_date'),
            'created_at': now,
            'updated_at': now,
        }
        success = await self.order_repo.create_order(db_data)
        if not success:
            raise Exception("Failed to create order")

        # Auto-create draft job if requested
        if data.get('auto_create_job'):
            await self._create_draft_job(order_id, data['title'], data.get('printer_id'))

        logger.info("Order created", order_id=order_id)
        return order_id

    async def _create_draft_job(self, order_id: str, job_name: str, printer_id: Optional[str] = None) -> str:
        """Create a draft job linked to an order. Returns job_id."""
        job_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        job_data = {
            'id': job_id,
            'printer_id': printer_id or 'unknown',
            'printer_type': 'unknown',
            'job_name': job_name,
            'status': 'pending',
            'order_id': order_id,
            'is_business': True,  # orders are always business
            'created_at': now,
            'updated_at': now,
        }
        # Insert directly via connection to avoid JobService import cycle
        sql = """INSERT INTO jobs (id, printer_id, printer_type, job_name, status, order_id, is_business, created_at, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        await self._execute_write_on_jobs(sql, (
            job_data['id'], job_data['printer_id'], job_data['printer_type'],
            job_data['job_name'], job_data['status'], job_data['order_id'],
            1 if job_data['is_business'] else 0, job_data['created_at'], job_data['updated_at']
        ))
        logger.info("Draft job created for order", job_id=job_id, order_id=order_id)
        return job_id

    async def _execute_write_on_jobs(self, sql: str, params: tuple) -> None:
        """Execute a write on the jobs table via the shared database connection."""
        cursor = await self.database._connection.execute(sql, params)
        await self.database._connection.commit()

    async def update_order(self, order_id: str, data: Dict[str, Any]) -> bool:
        """Update order. Validates status transitions."""
        existing = await self.order_repo.get_order(order_id)
        if not existing:
            return False

        # Validate status transition if status is being updated
        if 'status' in data and data['status']:
            current_status = existing.get('status', 'new')
            new_status = data['status']
            if isinstance(new_status, str) and new_status != current_status:
                self._validate_status_transition(current_status, new_status)

        update_data = {k: v for k, v in data.items() if v is not None}
        return await self.order_repo.update_order(order_id, update_data)

    async def delete_order(self, order_id: str) -> bool:
        """Delete order (files cascade, jobs.order_id → NULL)."""
        existing = await self.order_repo.get_order(order_id)
        if not existing:
            return False
        return await self.order_repo.delete_order(order_id)

    # ===================== Job linking =====================

    async def link_job(self, order_id: str, job_id: str) -> str:
        """Link existing job to order. Returns 'ok', 'job_not_found', or 'already_assigned'."""
        # Check order exists
        order = await self.order_repo.get_order(order_id)
        if not order:
            return 'order_not_found'

        # Check if job already has an order_id
        existing_order_id = await self.order_repo.get_job_order_id(job_id)
        if existing_order_id is None:
            # Job not found
            return 'job_not_found'
        if existing_order_id:
            return 'already_assigned'

        success = await self.order_repo.link_job(order_id, job_id)
        return 'ok' if success else 'error'

    async def unlink_job(self, order_id: str, job_id: str) -> bool:
        """Unlink job from order (sets order_id=NULL)."""
        return await self.order_repo.unlink_job(job_id)

    async def create_and_link_job(self, order_id: str, printer_id: Optional[str] = None) -> Optional[str]:
        """Create a draft job and link to order. Returns job_id or None."""
        order = await self.order_repo.get_order(order_id)
        if not order:
            return None
        return await self._create_draft_job(order_id, order['title'], printer_id)

    # ===================== File attachment =====================

    async def attach_file(self, order_id: str, data: Dict[str, Any]) -> str:
        """Attach a file (library file or URL) to an order. Returns order_file_id."""
        file_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        db_data = {
            'id': file_id,
            'order_id': order_id,
            'file_id': data.get('file_id'),
            'url': data.get('url'),
            'filename': data.get('filename', data.get('file_id', data.get('url', 'unknown'))),
            'file_type': data.get('file_type'),
            'created_at': now,
        }
        success = await self.order_repo.add_file(db_data)
        if not success:
            raise Exception("Failed to attach file")
        return file_id

    async def detach_file(self, order_id: str, order_file_id: str) -> bool:
        """Detach file from order."""
        return await self.order_repo.remove_file(order_file_id)

    # ===================== Analytics =====================

    async def get_order_analytics(self) -> Dict[str, Any]:
        """Get order analytics summary."""
        # Get all orders to compute analytics
        all_orders, total = await self.list_orders(limit=10000, offset=0)

        orders_by_status = {'new': 0, 'planned': 0, 'printed': 0, 'delivered': 0}
        total_quoted = 0.0
        total_paid = 0.0
        source_stats: Dict[str, Dict] = {}
        fulfillment_days_list = []

        for order in all_orders:
            status = order.get('status', 'new')
            orders_by_status[status] = orders_by_status.get(status, 0) + 1

            quoted = order.get('quoted_price') or 0.0
            total_quoted += quoted

            payment = order.get('payment_status', 'unpaid')
            if payment == 'paid':
                total_paid += quoted
            elif payment == 'partial':
                total_paid += quoted / 2  # estimate

            # Source stats
            source_id = order.get('source_id')
            if source_id:
                if source_id not in source_stats:
                    source = await self.order_repo.get_source(source_id)
                    source_stats[source_id] = {
                        'source_name': source['name'] if source else source_id,
                        'order_count': 0,
                        'total_quoted_eur': 0.0
                    }
                source_stats[source_id]['order_count'] += 1
                source_stats[source_id]['total_quoted_eur'] += quoted

            # Fulfillment days for delivered orders
            if status == 'delivered':
                try:
                    created = datetime.fromisoformat(order['created_at'])
                    updated = datetime.fromisoformat(order['updated_at'])
                    days = (updated - created).days
                    fulfillment_days_list.append(days)
                except Exception:
                    pass

        avg_fulfillment = (sum(fulfillment_days_list) / len(fulfillment_days_list)) if fulfillment_days_list else 0.0

        return {
            'total_orders': total,
            'orders_by_status': orders_by_status,
            'total_quoted_eur': round(total_quoted, 2),
            'total_paid_eur': round(total_paid, 2),
            'outstanding_eur': round(total_quoted - total_paid, 2),
            'orders_by_source': list(source_stats.values()),
            'avg_fulfillment_days': round(avg_fulfillment, 2),
        }
