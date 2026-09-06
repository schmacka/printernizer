/**
 * API key management for the Integrations settings tab.
 *
 * Keys authenticate Printernizer Connect, the PrusaSlicer companion. The
 * plaintext of a key is available only in the create response, so it is shown
 * once and never re-fetched.
 */

async function loadApiKeys() {
    const container = document.getElementById('apiKeyList');
    if (!container) return;

    try {
        // CONFIG.API_BASE_URL already ends in /api/v1 — endpoints are relative to it.
        const response = await api.get('/settings/api-keys');
        const keys = response.data.keys || [];

        if (keys.length === 0) {
            container.innerHTML =
                `<p class="form-text text-muted">${escapeHtml(t('settings.apiKeysEmpty'))}</p>`;
            return;
        }

        // Translate via t() rather than data-i18n: applyTranslations() runs once
        // over the static document at load and is never re-applied to markup
        // inserted later, so data-i18n here would leave English for German users.
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>${escapeHtml(t('settings.apiKeyNameLabel'))}</th>
                        <th>${escapeHtml(t('settings.apiKeyCreatedCol'))}</th>
                        <th>${escapeHtml(t('settings.apiKeyLastUsed'))}</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${keys.map(key => `
                        <tr>
                            <td>${escapeHtml(key.name)}</td>
                            <td>${formatKeyDate(key.created_at)}</td>
                            <td>${formatKeyDate(key.last_used_at)}</td>
                            <td>
                                <button class="btn btn-danger btn-sm"
                                        onclick="revokeApiKey('${escapeHtml(key.id)}')">
                                    ${escapeHtml(t('settings.apiKeyRevoke'))}
                                </button>
                            </td>
                        </tr>`).join('')}
                </tbody>
            </table>`;
    } catch (error) {
        Logger.error('Failed to load API keys:', error);
        showToast('error', t('common.error'), t('settings.apiKeysLoadFailed'));
    }
}

async function createApiKey() {
    const input = document.getElementById('apiKeyName');
    const name = (input?.value || '').trim();

    if (!name) {
        showToast('warning', t('common.error'), t('settings.apiKeyNameRequired'));
        return;
    }

    try {
        const response = await api.post('/settings/api-keys', { name });

        document.getElementById('apiKeyRevealValue').textContent = response.data.key;
        document.getElementById('apiKeyReveal').style.display = 'block';
        input.value = '';

        showToast('success', t('common.success'), t('settings.apiKeyCreated'));
        await loadApiKeys();
    } catch (error) {
        Logger.error('Failed to create API key:', error);
        showToast('error', t('common.error'), t('settings.apiKeyCreateFailed'));
    }
}

async function revokeApiKey(keyId) {
    if (!confirm(t('settings.apiKeyRevokeConfirm'))) return;

    try {
        await api.delete(`/settings/api-keys/${encodeURIComponent(keyId)}`);
        showToast('success', t('common.success'), t('settings.apiKeyRevoked'));
        await loadApiKeys();
    } catch (error) {
        Logger.error('Failed to revoke API key:', error);
        showToast('error', t('common.error'), t('settings.apiKeyRevokeFailed'));
    }
}

function formatKeyDate(value) {
    if (!value) return '—';
    try {
        return new Date(value).toLocaleString();
    } catch {
        return value;
    }
}
