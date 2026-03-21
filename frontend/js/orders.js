/**
 * Printernizer Orders Management Page
 * Handles customer orders, customer management, and order sources
 */

const ORDER_STATUS_COLORS = {
    'new': '#3b82f6',      // blue
    'planned': '#f59e0b',  // yellow
    'printed': '#10b981',  // green
    'delivered': '#6b7280' // gray
};

const PAYMENT_STATUS_LABELS = {
    'unpaid': '⬜ Unpaid',
    'partial': '🔶 Partial',
    'paid': '✅ Paid'
};

class OrdersManager {
    constructor() {
        this.orders = [];
        this.customers = [];
        this.sources = [];
        this.filters = {};
    }

    async init() {
        Logger.debug('Initializing orders management');
        await Promise.all([
            this.load(),
            this.loadCustomers(),
            this.loadSources()
        ]);
    }

    async load() {
        try {
            const status = document.getElementById('orderStatusFilter')?.value || '';
            const params = new URLSearchParams();
            if (status) params.set('status', status);
            params.set('limit', '100');

            const response = await fetch(`/api/v1/orders?${params}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            this.orders = data.orders || [];
            this.renderOrders();
        } catch (error) {
            Logger.error('Failed to load orders:', error);
            this.renderOrdersError();
        }
    }

    renderOrders() {
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) return;

        if (!this.orders.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No orders yet. Create your first order!</td></tr>';
            return;
        }

        tbody.innerHTML = this.orders.map(order => {
            const statusColor = ORDER_STATUS_COLORS[order.status] || '#6b7280';
            const customerName = order.customer?.name || order.customer_id || '—';
            const sourceName = order.source?.name || '—';
            const quoted = order.quoted_price != null ? `€${order.quoted_price.toFixed(2)}` : '—';
            const dueDate = order.due_date ? new Date(order.due_date).toLocaleDateString() : '—';

            return `<tr>
                <td><strong>${this._escapeHtml(order.title)}</strong></td>
                <td>${this._escapeHtml(customerName)}</td>
                <td><span class="status-badge">${this._escapeHtml(sourceName)}</span></td>
                <td><span class="status-badge" style="background:${statusColor};color:white;">${order.status}</span></td>
                <td>${quoted}</td>
                <td>${PAYMENT_STATUS_LABELS[order.payment_status] || order.payment_status}</td>
                <td>${dueDate}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="ordersManager.showOrderDetail('${order.id}')">View</button>
                    <button class="btn btn-danger btn-sm" onclick="ordersManager.deleteOrder('${order.id}')">Delete</button>
                </td>
            </tr>`;
        }).join('');
    }

    renderOrdersError() {
        const tbody = document.getElementById('ordersTableBody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Failed to load orders.</td></tr>';
    }

    applyFilters() {
        this.load();
    }

    async loadCustomers(search = '') {
        try {
            const params = new URLSearchParams();
            if (search) params.set('search', search);
            const response = await fetch(`/api/v1/customers?${params}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            this.customers = await response.json();
            this.renderCustomers();
        } catch (error) {
            Logger.error('Failed to load customers:', error);
        }
    }

    renderCustomers() {
        const tbody = document.getElementById('customersTableBody');
        if (!tbody) return;

        if (!this.customers.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No customers yet.</td></tr>';
            return;
        }

        tbody.innerHTML = this.customers.map(c => `
            <tr>
                <td><strong>${this._escapeHtml(c.name)}</strong></td>
                <td>${this._escapeHtml(c.email || '—')}</td>
                <td>${this._escapeHtml(c.phone || '—')}</td>
                <td>${c.order_count || 0}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="ordersManager.deleteCustomer('${c.id}')">Delete</button>
                </td>
            </tr>
        `).join('');
    }

    searchCustomers(query) {
        this.loadCustomers(query);
    }

    async loadSources() {
        try {
            const response = await fetch('/api/v1/order-sources?all=true');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            this.sources = await response.json();
            this.renderSources();
        } catch (error) {
            Logger.error('Failed to load order sources:', error);
        }
    }

    renderSources() {
        const container = document.getElementById('orderSourcesList');
        if (!container) return;

        if (!this.sources.length) {
            container.innerHTML = '<p class="text-muted">No sources configured.</p>';
            return;
        }

        container.innerHTML = this.sources.map(s => `
            <div class="settings-item" style="display:flex;align-items:center;gap:1rem;padding:0.5rem 0;border-bottom:1px solid var(--border-color);">
                <span style="flex:1;">${this._escapeHtml(s.name)}</span>
                <span class="status-badge" style="background:${s.is_active ? '#10b981' : '#6b7280'};color:white;">${s.is_active ? 'Active' : 'Inactive'}</span>
                <button class="btn btn-secondary btn-sm" onclick="ordersManager.toggleSource('${s.id}', ${!s.is_active})">${s.is_active ? 'Disable' : 'Enable'}</button>
                <button class="btn btn-danger btn-sm" onclick="ordersManager.deleteSource('${s.id}')">Delete</button>
            </div>
        `).join('');
    }

    // ---- Modals ----

    showCreateModal() {
        const title = prompt('Order title:');
        if (!title) return;
        this.createOrder({ title });
    }

    showCreateCustomerModal() {
        const name = prompt('Customer name:');
        if (!name) return;
        const email = prompt('Email (optional):') || null;
        const phone = prompt('Phone (optional):') || null;
        this.createCustomer({ name, email, phone });
    }

    showCreateSourceModal() {
        const name = prompt('Source name (e.g. "Instagram DM"):');
        if (!name) return;
        this.createSource({ name });
    }

    async showOrderDetail(orderId) {
        try {
            const response = await fetch(`/api/v1/orders/${orderId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const order = await response.json();

            const detail = `
Order: ${this._escapeHtml(order.title)}
Status: ${order.status}
Customer: ${order.customer?.name || 'None'}
Quoted: ${order.quoted_price != null ? '€' + order.quoted_price.toFixed(2) : '—'}
Payment: ${order.payment_status}
Material cost: €${(order.material_cost_eur || 0).toFixed(2)}
Energy cost: €${(order.energy_cost_eur || 0).toFixed(2)}
Jobs: ${order.jobs?.length || 0}
Files: ${order.files?.length || 0}`;

            alert(detail);
        } catch (error) {
            Logger.error('Failed to load order detail:', error);
            showToast('error', 'Error', 'Failed to load order details');
        }
    }

    // ---- CRUD operations ----

    async createOrder(data) {
        try {
            const response = await fetch('/api/v1/orders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            showToast('success', 'Order Created', `Order "${data.title}" created`);
            await this.load();
        } catch (error) {
            Logger.error('Failed to create order:', error);
            showToast('error', 'Error', 'Failed to create order');
        }
    }

    async deleteOrder(orderId) {
        if (!confirm('Delete this order? Linked jobs will be unlinked.')) return;
        try {
            const response = await fetch(`/api/v1/orders/${orderId}`, { method: 'DELETE' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            showToast('success', 'Deleted', 'Order deleted');
            await this.load();
        } catch (error) {
            showToast('error', 'Error', 'Failed to delete order');
        }
    }

    async createCustomer(data) {
        try {
            const response = await fetch('/api/v1/customers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            showToast('success', 'Customer Created', `Customer "${data.name}" created`);
            await this.loadCustomers();
        } catch (error) {
            showToast('error', 'Error', 'Failed to create customer');
        }
    }

    async deleteCustomer(customerId) {
        if (!confirm('Delete this customer? Their orders will be kept but unlinked.')) return;
        try {
            const response = await fetch(`/api/v1/customers/${customerId}`, { method: 'DELETE' });
            if (response.status === 404) throw new Error('Not found');
            showToast('success', 'Deleted', 'Customer deleted');
            await this.loadCustomers();
        } catch (error) {
            showToast('error', 'Error', 'Failed to delete customer');
        }
    }

    async createSource(data) {
        try {
            const response = await fetch('/api/v1/order-sources', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            showToast('success', 'Source Created', `Source "${data.name}" created`);
            await this.loadSources();
        } catch (error) {
            showToast('error', 'Error', 'Failed to create source');
        }
    }

    async toggleSource(sourceId, isActive) {
        try {
            const response = await fetch(`/api/v1/order-sources/${sourceId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: isActive })
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            await this.loadSources();
        } catch (error) {
            showToast('error', 'Error', 'Failed to update source');
        }
    }

    async deleteSource(sourceId) {
        if (!confirm('Delete this source?')) return;
        try {
            const response = await fetch(`/api/v1/order-sources/${sourceId}`, { method: 'DELETE' });
            if (response.status === 409) {
                showToast('error', 'Cannot Delete', 'Source is used by existing orders');
                return;
            }
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            showToast('success', 'Deleted', 'Source deleted');
            await this.loadSources();
        } catch (error) {
            showToast('error', 'Error', 'Failed to delete source');
        }
    }

    async unlinkJob(orderId, jobId) {
        try {
            const response = await fetch(`/api/v1/orders/${orderId}/jobs/${jobId}`, { method: 'DELETE' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            showToast('success', 'Unlinked', 'Job unlinked from order');
        } catch (error) {
            showToast('error', 'Error', 'Failed to unlink job');
        }
    }

    async detachFile(orderId, orderFileId) {
        try {
            const response = await fetch(`/api/v1/orders/${orderId}/files/${orderFileId}`, { method: 'DELETE' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            showToast('success', 'Removed', 'File detached from order');
        } catch (error) {
            showToast('error', 'Error', 'Failed to detach file');
        }
    }

    _escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
}

const ordersManager = new OrdersManager();
