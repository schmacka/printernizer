/**
 * Notification Channel Management
 * Handles multi-channel notifications (Discord, Slack, ntfy)
 */

class NotificationManager {
    constructor() {
        this.channels = [];
        this.eventTypes = [];
        this.isLoading = false;
        this.editingChannelId = null;
    }

    /**
     * Initialize notification manager
     */
    async init() {
        Logger.debug('Initializing notification manager');

        try {
            // Load event types first
            await this.loadEventTypes();

            // Load channels
            await this.loadChannels();

            // Setup modal handlers
            this.setupModalHandlers();

            Logger.debug('Notification manager initialized');
        } catch (error) {
            Logger.error('Failed to initialize notification manager:', error);
            showToast('error', 'Initialization Error', 'Failed to load notification settings');
        }
    }

    /**
     * Load available event types from API
     */
    async loadEventTypes() {
        try {
            const response = await fetch('/api/v1/notifications/events');
            if (!response.ok) throw new Error('Failed to load event types');

            const data = await response.json();
            this.eventTypes = data.events || [];
            Logger.debug('Loaded event types:', this.eventTypes.length);
        } catch (error) {
            Logger.error('Failed to load event types:', error);
            // Use defaults if API fails
            this.eventTypes = [
                { id: 'job_started', label: 'Job Started', icon: 'play', description: 'When a print job begins' },
                { id: 'job_completed', label: 'Job Completed', icon: 'check', description: 'When a print job finishes' },
                { id: 'job_failed', label: 'Job Failed', icon: 'x', description: 'When a print job fails' },
                { id: 'job_paused', label: 'Job Paused', icon: 'pause', description: 'When a print job is paused' },
                { id: 'printer_online', label: 'Printer Online', icon: 'wifi', description: 'When a printer comes online' },
                { id: 'printer_offline', label: 'Printer Offline', icon: 'wifi-off', description: 'When a printer goes offline' },
                { id: 'printer_error', label: 'Printer Error', icon: 'alert-triangle', description: 'When a printer reports an error' },
                { id: 'material_low_stock', label: 'Material Low Stock', icon: 'package', description: 'When material inventory is low' },
                { id: 'file_downloaded', label: 'File Downloaded', icon: 'download', description: 'When a file is downloaded' }
            ];
        }
    }

    /**
     * Load notification channels from API
     */
    async loadChannels() {
        this.isLoading = true;
        this.renderLoading();

        try {
            const response = await fetch('/api/v1/notifications');
            if (!response.ok) throw new Error('Failed to load channels');

            const data = await response.json();
            this.channels = data.channels || [];

            this.renderChannels();
            Logger.debug('Loaded notification channels:', this.channels.length);
        } catch (error) {
            Logger.error('Failed to load channels:', error);
            this.renderError('Failed to load notification channels');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Render loading state
     */
    renderLoading() {
        const container = document.getElementById('notificationChannelsList');
        if (!container) return;

        container.innerHTML = `
            <div class="loading-placeholder">
                <div class="spinner"></div>
                <p>Loading notification channels...</p>
            </div>
        `;
    }

    /**
     * Render error state
     */
    renderError(message) {
        const container = document.getElementById('notificationChannelsList');
        if (!container) return;

        container.innerHTML = `
            <div class="empty-state error">
                <span class="empty-icon">⚠️</span>
                <p>${message}</p>
                <button class="btn btn-secondary" onclick="notificationManager.loadChannels()">
                    Retry
                </button>
            </div>
        `;
    }

    /**
     * Render all notification channels
     */
    renderChannels() {
        const container = document.getElementById('notificationChannelsList');
        if (!container) return;

        if (this.channels.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">🔔</span>
                    <p>No notification channels configured</p>
                    <p class="text-muted">Add a channel to receive notifications when print jobs complete, printers go offline, and more.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.channels.map(channel => this.renderChannelCard(channel)).join('');
    }

    /**
     * Render a single channel card
     */
    renderChannelCard(channel) {
        const typeIcons = {
            discord: '💬',
            slack: '📱',
            ntfy: '📣'
        };

        const typeLabels = {
            discord: 'Discord',
            slack: 'Slack',
            ntfy: 'ntfy.sh'
        };

        const icon = typeIcons[channel.channel_type] || '🔔';
        const label = typeLabels[channel.channel_type] || channel.channel_type;
        const statusClass = channel.is_enabled ? 'status-online' : 'status-offline';
        const statusText = channel.is_enabled ? 'Enabled' : 'Disabled';

        const eventCount = channel.subscribed_events?.length || 0;
        const eventText = eventCount === 1 ? '1 event' : `${eventCount} events`;

        return `
            <div class="notification-channel-card" data-channel-id="${channel.id}">
                <div class="channel-header">
                    <div class="channel-icon">${icon}</div>
                    <div class="channel-info">
                        <div class="channel-name">${this.escapeHtml(channel.name)}</div>
                        <div class="channel-type">${label}</div>
                    </div>
                    <div class="channel-status">
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                </div>
                <div class="channel-details">
                    <div class="channel-events">
                        <span class="events-count">${eventText}</span>
                        ${this.renderEventBadges(channel.subscribed_events)}
                    </div>
                </div>
                <div class="channel-actions">
                    <button class="btn btn-sm btn-secondary" onclick="notificationManager.testChannel('${channel.id}')" title="Send test notification">
                        🔔 Test
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="notificationManager.showEditChannel('${channel.id}')" title="Edit channel">
                        ✏️ Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="notificationManager.deleteChannel('${channel.id}')" title="Delete channel">
                        🗑️
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render event badges
     */
    renderEventBadges(events) {
        if (!events || events.length === 0) {
            return '<span class="text-muted">No events subscribed</span>';
        }

        const maxDisplay = 4;
        const displayEvents = events.slice(0, maxDisplay);
        const remaining = events.length - maxDisplay;

        let html = displayEvents.map(eventId => {
            const event = this.eventTypes.find(e => e.id === eventId);
            const label = event ? event.label : eventId;
            return `<span class="event-badge">${label}</span>`;
        }).join('');

        if (remaining > 0) {
            html += `<span class="event-badge more">+${remaining} more</span>`;
        }

        return html;
    }

    /**
     * Setup modal handlers
     */
    setupModalHandlers() {
        // Close modal on background click
        const modal = document.getElementById('notificationChannelModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal();
                }
            });
        }

        // Channel type change handler
        const typeSelect = document.getElementById('channelType');
        if (typeSelect) {
            typeSelect.addEventListener('change', (e) => {
                this.updateFormForChannelType(e.target.value);
            });
        }
    }

    /**
     * Show add channel modal
     */
    showAddChannel() {
        this.editingChannelId = null;

        const modal = document.getElementById('notificationChannelModal');
        const title = document.getElementById('channelModalTitle');
        const form = document.getElementById('channelForm');

        if (!modal || !title || !form) return;

        title.textContent = 'Add Notification Channel';
        form.reset();

        // Set defaults
        document.getElementById('channelEnabled').checked = true;

        // Show/hide topic field based on default type
        this.updateFormForChannelType('discord');

        // Reset event checkboxes
        this.renderEventCheckboxes([]);

        modal.classList.add('show');
    }

    /**
     * Show edit channel modal
     */
    async showEditChannel(channelId) {
        this.editingChannelId = channelId;

        const channel = this.channels.find(c => c.id === channelId);
        if (!channel) {
            showToast('error', 'Error', 'Channel not found');
            return;
        }

        const modal = document.getElementById('notificationChannelModal');
        const title = document.getElementById('channelModalTitle');
        const form = document.getElementById('channelForm');

        if (!modal || !title || !form) return;

        title.textContent = 'Edit Notification Channel';

        // Populate form
        document.getElementById('channelName').value = channel.name;
        document.getElementById('channelType').value = channel.channel_type;
        document.getElementById('channelWebhookUrl').value = channel.webhook_url;
        document.getElementById('channelTopic').value = channel.topic || '';
        document.getElementById('channelEnabled').checked = channel.is_enabled;

        // Show/hide topic field
        this.updateFormForChannelType(channel.channel_type);

        // Set event checkboxes
        this.renderEventCheckboxes(channel.subscribed_events || []);

        modal.classList.add('show');
    }

    /**
     * Hide modal
     */
    hideModal() {
        const modal = document.getElementById('notificationChannelModal');
        if (modal) {
            modal.classList.remove('show');
        }
        this.editingChannelId = null;
    }

    /**
     * Update form based on channel type
     */
    updateFormForChannelType(type) {
        const topicGroup = document.getElementById('topicGroup');
        const webhookLabel = document.getElementById('webhookUrlLabel');
        const webhookHelp = document.getElementById('webhookUrlHelp');

        if (!topicGroup) return;

        if (type === 'ntfy') {
            topicGroup.style.display = 'block';
            if (webhookLabel) webhookLabel.textContent = 'Server URL';
            if (webhookHelp) webhookHelp.textContent = 'ntfy server URL (e.g., https://ntfy.sh)';
        } else {
            topicGroup.style.display = 'none';
            if (webhookLabel) webhookLabel.textContent = 'Webhook URL';
            if (webhookHelp) {
                webhookHelp.textContent = type === 'discord'
                    ? 'Discord webhook URL from channel settings'
                    : 'Slack incoming webhook URL';
            }
        }
    }

    /**
     * Render event checkboxes
     */
    renderEventCheckboxes(selectedEvents) {
        const container = document.getElementById('eventCheckboxes');
        if (!container) return;

        container.innerHTML = this.eventTypes.map(event => {
            const checked = selectedEvents.includes(event.id) ? 'checked' : '';
            return `
                <label class="event-checkbox">
                    <input type="checkbox" name="events" value="${event.id}" ${checked}>
                    <span class="event-label">
                        <span class="event-name">${event.label}</span>
                        <span class="event-desc">${event.description}</span>
                    </span>
                </label>
            `;
        }).join('');
    }

    /**
     * Save channel (create or update)
     */
    async saveChannel() {
        const form = document.getElementById('channelForm');
        if (!form) return;

        const name = document.getElementById('channelName').value.trim();
        const channelType = document.getElementById('channelType').value;
        const webhookUrl = document.getElementById('channelWebhookUrl').value.trim();
        const topic = document.getElementById('channelTopic').value.trim();
        const isEnabled = document.getElementById('channelEnabled').checked;

        // Get selected events
        const eventCheckboxes = document.querySelectorAll('input[name="events"]:checked');
        const subscribedEvents = Array.from(eventCheckboxes).map(cb => cb.value);

        // Validation
        if (!name) {
            showToast('error', 'Validation Error', 'Channel name is required');
            return;
        }

        if (!webhookUrl) {
            showToast('error', 'Validation Error', 'Webhook URL is required');
            return;
        }

        if (channelType === 'ntfy' && !topic) {
            showToast('error', 'Validation Error', 'Topic is required for ntfy channels');
            return;
        }

        const payload = {
            name,
            channel_type: channelType,
            webhook_url: webhookUrl,
            topic: channelType === 'ntfy' ? topic : null,
            is_enabled: isEnabled,
            subscribed_events: subscribedEvents
        };

        try {
            let response;

            if (this.editingChannelId) {
                // Update existing channel
                response = await fetch(`/api/v1/notifications/${this.editingChannelId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                // Update subscriptions separately
                if (response.ok) {
                    await fetch(`/api/v1/notifications/${this.editingChannelId}/subscriptions`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ subscribed_events: subscribedEvents })
                    });
                }
            } else {
                // Create new channel
                response = await fetch('/api/v1/notifications', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to save channel');
            }

            showToast('success', 'Success', this.editingChannelId ? 'Channel updated' : 'Channel created');
            this.hideModal();
            await this.loadChannels();

        } catch (error) {
            Logger.error('Failed to save channel:', error);
            showToast('error', 'Error', error.message || 'Failed to save channel');
        }
    }

    /**
     * Delete a channel
     */
    async deleteChannel(channelId) {
        const channel = this.channels.find(c => c.id === channelId);
        if (!channel) return;

        const confirmed = confirm(`Are you sure you want to delete the channel "${channel.name}"?`);
        if (!confirmed) return;

        try {
            const response = await fetch(`/api/v1/notifications/${channelId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete channel');
            }

            showToast('success', 'Success', 'Channel deleted');
            await this.loadChannels();

        } catch (error) {
            Logger.error('Failed to delete channel:', error);
            showToast('error', 'Error', 'Failed to delete channel');
        }
    }

    /**
     * Test a channel
     */
    async testChannel(channelId) {
        const channel = this.channels.find(c => c.id === channelId);
        if (!channel) return;

        try {
            showToast('info', 'Testing...', `Sending test notification to ${channel.name}`);

            const response = await fetch(`/api/v1/notifications/${channelId}/test`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                showToast('success', 'Test Successful', result.message);
            } else {
                showToast('error', 'Test Failed', result.message);
            }

        } catch (error) {
            Logger.error('Failed to test channel:', error);
            showToast('error', 'Error', 'Failed to send test notification');
        }
    }

    /**
     * Toggle all events
     */
    toggleAllEvents(checked) {
        const checkboxes = document.querySelectorAll('input[name="events"]');
        checkboxes.forEach(cb => cb.checked = checked);
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create global instance
const notificationManager = new NotificationManager();
