/**
 * Printernizer i18n
 *
 * Lightweight translation layer without any framework dependency.
 *
 * Usage:
 *   - JS:   t('nav.dashboard')  or  t('files.uploaded', { name: 'benchy.3mf' })
 *   - HTML: <span data-i18n="nav.dashboard">Dashboard</span>
 *           data-i18n-title / data-i18n-placeholder for attributes
 *
 * Translations live in frontend/locales/<locale>.json with nested,
 * namespaced keys (nav.*, common.*, status.*, errors.*, ...).
 *
 * If a key is missing in the active locale, the German locale is used,
 * then the key itself. If locale files cannot be loaded at all, existing
 * markup text stays untouched, so the UI never breaks on first paint.
 *
 * See docs/development/I18N_GUIDE.md for conventions.
 */

class I18n {
    constructor() {
        this.storageKey = 'printernizer_locale';
        this.defaultLocale = 'de';
        this.supportedLocales = ['de', 'en'];
        this.locale = this.detectLocale();
        this.translations = {};
        this.fallbackTranslations = {};
        this.ready = false;
    }

    detectLocale() {
        const stored = localStorage.getItem(this.storageKey);
        if (stored && this.supportedLocales.includes(stored)) {
            return stored;
        }
        const browser = (navigator.language || '').slice(0, 2).toLowerCase();
        return this.supportedLocales.includes(browser) ? browser : this.defaultLocale;
    }

    async init() {
        try {
            // Relative paths so the files resolve under HA ingress base paths
            this.translations = await this.loadLocale(this.locale);
            this.fallbackTranslations = this.locale === this.defaultLocale
                ? this.translations
                : await this.loadLocale(this.defaultLocale);
            this.ready = true;
        } catch (error) {
            // Markup keeps its inline text when no translations are available
            console.warn('i18n: failed to load locale files, using inline text', error);
            this.translations = {};
            this.fallbackTranslations = {};
        }

        document.documentElement.lang = this.locale;
        this.applyTranslations();
    }

    async loadLocale(locale) {
        const response = await fetch(`locales/${locale}.json`, { cache: 'no-cache' });
        if (!response.ok) {
            throw new Error(`Failed to load locale '${locale}': HTTP ${response.status}`);
        }
        return response.json();
    }

    /**
     * Resolve a dot-separated key against a nested translations object
     */
    resolve(translations, key) {
        return key.split('.').reduce(
            (node, part) => (node && typeof node === 'object') ? node[part] : undefined,
            translations
        );
    }

    /**
     * Translate a key with optional {placeholder} interpolation.
     * Falls back: active locale -> default locale -> the key itself.
     */
    t(key, params = null) {
        let text = this.resolve(this.translations, key);
        if (text === undefined) {
            text = this.resolve(this.fallbackTranslations, key);
        }
        if (text === undefined || typeof text !== 'string') {
            return key;
        }

        if (params) {
            text = text.replace(/\{(\w+)\}/g, (match, name) =>
                params[name] !== undefined ? params[name] : match
            );
        }
        return text;
    }

    /**
     * Check whether a translation exists for the key
     */
    has(key) {
        return this.resolve(this.translations, key) !== undefined
            || this.resolve(this.fallbackTranslations, key) !== undefined;
    }

    /**
     * Persist a new locale and reload so all rendered text is rebuilt
     */
    setLocale(locale) {
        if (!this.supportedLocales.includes(locale)) {
            console.warn(`i18n: unsupported locale '${locale}'`);
            return;
        }
        if (locale === this.locale) return;
        localStorage.setItem(this.storageKey, locale);
        location.reload();
    }

    getLocale() {
        return this.locale;
    }

    /**
     * Full Intl locale tag for date/number formatting
     */
    getIntlLocale() {
        const intlLocales = { de: 'de-DE', en: 'en-US' };
        return intlLocales[this.locale] || 'de-DE';
    }

    /**
     * Apply translations to static markup via data-i18n attributes.
     * Only replaces content when a translation actually exists.
     */
    applyTranslations(root = document) {
        root.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (this.has(key)) el.textContent = this.t(key);
        });
        root.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            if (this.has(key)) el.setAttribute('title', this.t(key));
        });
        root.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (this.has(key)) el.setAttribute('placeholder', this.t(key));
        });
    }
}

// Global instance + shorthand
window.i18n = new I18n();
window.t = (key, params) => window.i18n.t(key, params);
