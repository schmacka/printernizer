# Frontend Internationalization (i18n) Guide

Printernizer's frontend has a lightweight, framework-free translation layer.
This guide explains how it works and how to migrate remaining hardcoded
strings.

## Architecture

| Piece | Location | Purpose |
|-------|----------|---------|
| `I18n` class | `frontend/js/i18n.js` | Loads locale files, provides `t()`, applies `data-i18n` attributes |
| Locale files | `frontend/locales/de.json`, `frontend/locales/en.json` | Nested, namespaced translation keys |
| Language selector | Settings → Appearance tab | Persists the locale in `localStorage` (`printernizer_locale`) and reloads |

`i18n.init()` runs at the top of the `DOMContentLoaded` bootstrap in
`frontend/js/main.js`, before any page renders. The locale defaults to the
stored preference, then the browser language, then German.

**Fallback chain:** active locale → German → the key itself. If the locale
files cannot be loaded at all, static markup keeps its inline text, so the
UI never breaks.

## Usage

### In JavaScript

```js
showToast('error', t('common.error'), t('errors.network'));

// With interpolation
t('files.uploaded', { name: file.filename });
// locale entry: "uploaded": "Datei {name} wurde hochgeladen"
```

Dynamically built HTML (template literals in `components.js`, page
managers, etc.) must call `t()` at render time — the attribute scan below
only covers static markup.

### In static HTML

```html
<span data-i18n="nav.dashboard">Dashboard</span>
<button data-i18n-title="common.delete" title="Löschen">🗑️</button>
<input data-i18n-placeholder="common.search" placeholder="Suchen">
```

The inline text acts as the no-JS/loading fallback. `data-i18n` replaces
the element's `textContent` — never put it on an element with child
elements (wrap the text in its own `<span>` instead, as the nav links do).

## Key naming conventions

- Namespaces: `nav.*`, `common.*`, `status.<type>.*`, `errors.*`,
  `success.*`, `loading.*`, `settings.*`, plus one namespace per page
  module (`files.*`, `printers.*`, `jobs.*`, …).
- camelCase leaf keys: `errors.printerOffline`, not `errors.printer_offline`.
- Keys describe meaning, not the German wording.

## Rules

1. **No new hardcoded UI strings.** Any new user-facing text goes into both
   locale files and is referenced via `t()` / `data-i18n`.
2. Add every key to **both** `de.json` and `en.json` in the same structure.
3. `CONFIG.ERROR_MESSAGES` / `SUCCESS_MESSAGES` / `LOADING_MESSAGES` and the
   `*_STATUS` label dictionaries in `config.js` are frozen German fallbacks.
   Do not extend them — add locale keys instead and migrate call sites to
   `t()` (see `ApiError.getUserMessage()` in `api.js` and
   `getStatusConfig()` in `utils.js` for the pattern).

## Migration status

Phase A (done): infrastructure, navigation, status badges, API error
messages, language selector.

Phase B (incremental): the remaining page modules still contain hardcoded
German strings (`settings.js`, `orders.js`, `jobs.js`, `files.js`,
`printers.js`, `components.js` render strings, `notifications.js`, the
setup wizard, `library.js`, …). When touching one of these files, extract
the strings you touch into the locale files. Date/number formatting
(`toLocaleString('de-DE')`, `CONFIG.CURRENCY_FORMAT`) is also still
hardcoded German and should be parameterized per locale in Phase B.

## Adding a new locale

1. Copy `frontend/locales/en.json` to `frontend/locales/<code>.json` and translate.
2. Add the code to `supportedLocales` in `frontend/js/i18n.js`.
3. Add an `<option>` to the language selector in `frontend/index.html`.
