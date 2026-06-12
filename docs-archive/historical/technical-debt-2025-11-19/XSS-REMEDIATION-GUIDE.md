# XSS Remediation Guide

**Created**: 2025-11-18  
**Status**: Infrastructure Complete - Systematic Application Pending  
**Task**: Phase 3, Task 3.3 - Fix Frontend XSS Risks

---

## ✅ Completed Infrastructure

### Security Utilities (in `frontend/js/utils.js`)

All security utilities have been implemented and are ready for use:

1. **`escapeHtml(unsafe)`** (Line 915)
   - Escapes `&`, `<`, `>`, `"`, `'`, `/` characters
   - Returns safe HTML-escaped string
   - **Use for**: User-provided text in template literals

2. **`sanitizeUrl(url)`** (Line 949)
   - Validates URL protocols (allows http, https, mailto, tel, ftp, ftps)
   - Blocks dangerous protocols (javascript:, data:, vbscript:)
   - **Use for**: href and src attributes

3. **`sanitizeAttribute(unsafe)`** (Line 932)
   - Removes dangerous protocols and escapes HTML
   - **Use for**: HTML attribute values

4. **`createSafeElement(tag, attrs, content)`** (Line 978)
   - Creates DOM elements safely without innerHTML
   - Auto-sanitizes URLs in href/src
   - Auto-escapes text content
   - **Use for**: Building complex DOM structures

5. **`safeSetInnerHTML(element, html, escape=true)`** (Line 1028)
   - Wrapper for innerHTML with optional auto-escaping
   - **Use for**: Setting innerHTML with safety

---

## 📊 innerHTML Usage Analysis

### Files with innerHTML (20 files)

**High Priority** (User-facing data):
- `jobs.js` - Job names, printer names
- `files.js` - File names, paths
- `library.js` - Library file names, metadata
- `ideas.js` - User ideas, descriptions
- `materials.js` - Material names, types

**Medium Priority** (Dynamic content):
- `components.js` - Printer tiles, status displays
- `printers.js` - Printer configuration forms
- `dashboard.js` - Statistics, charts
- `auto-download-ui.js` - Download status displays
- `search.js` - Search results

**Low Priority** (Mostly static content):
- `camera.js` - Camera controls
- `enhanced-metadata.js` - Metadata displays  
- `error-handler.js` - Error messages (already uses escapeHtml in some places)
- `global-drag-drop.js` - Drag/drop indicators
- `main.js` - App structure (already uses escapeHtml for thumbnails)
- `milestone-1-2-functions.js` - Legacy functions
- `navigation-preferences-ui.js` - UI preferences
- `printer-form.js` - Form controls
- `timelapses.js` - Timelapse displays
- `websocket.js` - WebSocket status

### Usage Patterns

**Pattern 1: Static HTML** (✅ Safe - No changes needed)
```javascript
element.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
```

**Pattern 2: Template Literals with User Data** (⚠️ RISK - Needs fixing)
```javascript
// UNSAFE:
element.innerHTML = `<span>${userName}</span>`;

// FIX:
element.innerHTML = `<span>${escapeHtml(userName)}</span>`;
```

**Pattern 3: URLs in Template Literals** (⚠️ RISK - Needs fixing)
```javascript
// UNSAFE:
element.innerHTML = `<a href="${url}">${text}</a>`;

// FIX:
element.innerHTML = `<a href="${sanitizeUrl(url)}">${escapeHtml(text)}</a>`;
```

**Pattern 4: Complex HTML Construction** (💡 Consider refactoring)
```javascript
// Instead of:
el.innerHTML = `<div class="item"><h3>${title}</h3><p>${desc}</p></div>`;

// Option 1 - Apply escapeHtml:
el.innerHTML = `<div class="item"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(desc)}</p></div>`;

// Option 2 - Use createSafeElement:
const div = createSafeElement('div', {class: 'item'}, [
    createSafeElement('h3', {}, title),
    createSafeElement('p', {}, desc)
]);
el.appendChild(div);
```

---

## 🎯 Implementation Checklist

### Phase 1: High Priority Files (5 files)

- [ ] **jobs.js**
  - [ ] Job name displays
  - [ ] Printer name displays
  - [ ] Status messages
  
- [ ] **files.js**
  - [ ] File name displays
  - [ ] File path displays
  - [ ] Metadata displays

- [ ] **library.js**
  - [ ] Library file names
  - [ ] Source information
  - [ ] File metadata

- [ ] **ideas.js**
  - [ ] Idea titles
  - [ ] Idea descriptions
  - [ ] Tag displays

- [ ] **materials.js**
  - [ ] Material names
  - [ ] Material types
  - [ ] Spool information

### Phase 2: Medium Priority Files (5 files)

- [ ] **components.js**
  - [ ] Printer tile content
  - [ ] Status badge text (already partially safe with getStatusConfig)
  - [ ] Timestamp displays (already using getRelativeTime)

- [ ] **printers.js**
  - [ ] Printer configuration displays
  - [ ] Discovery results
  - [ ] Error messages

- [ ] **dashboard.js**
  - [ ] Statistics displays (mostly uses textContent - already safe)
  - [ ] Status badges

- [ ] **auto-download-ui.js**
  - [ ] Download status displays
  - [ ] File name displays

- [ ] **search.js**
  - [ ] Search results
  - [ ] File/idea name displays

### Phase 3: Low Priority Files (10 files)

- [ ] **camera.js** - Camera status/controls
- [ ] **enhanced-metadata.js** - Metadata formatting
- [ ] **error-handler.js** - Error displays  
- [ ] **global-drag-drop.js** - Drop zone indicators
- [ ] **main.js** - Thumbnail modal (already uses escapeHtml)
- [ ] **milestone-1-2-functions.js** - Legacy functions
- [ ] **navigation-preferences-ui.js** - Preference displays
- [ ] **printer-form.js** - Form validation messages
- [ ] **timelapses.js** - Timelapse displays
- [ ] **websocket.js** - Connection status

---

## 📝 Implementation Guidelines

### 1. Before Making Changes

```javascript
// Search for innerHTML usage
grep -n "innerHTML" filename.js

// Look for template literals with user data
grep -n 'innerHTML.*`.*\${' filename.js
```

### 2. Identify Risk Level

- **High Risk**: User-provided strings (names, descriptions, URLs)
- **Medium Risk**: API data that could be modified
- **Low Risk**: Static HTML, controlled enums, system-generated IDs

### 3. Apply Appropriate Fix

```javascript
// For user text:
${userName} → ${escapeHtml(userName)}

// For URLs:
href="${url}" → href="${sanitizeUrl(url)}"

// For attributes:
data-value="${value}" → data-value="${sanitizeAttribute(value)}"

// For complex structures, consider createSafeElement
```

### 4. Testing Each Change

```javascript
// Test with XSS payloads:
const xssTest = '<script>alert("XSS")</script>';
const xssURL = 'javascript:alert("XSS")';

// Verify output is escaped:
// Expected: &lt;script&gt;alert("XSS")&lt;/script&gt;
// NOT: <script>alert("XSS")</script>
```

---

## 🔍 Current Status

### ✅ Completed

- [x] Security utilities implemented in utils.js
- [x] escapeHtml() function available and exported
- [x] sanitizeUrl() blocks dangerous protocols
- [x] createSafeElement() for safe DOM construction
- [x] CSP headers configured in backend (SecurityHeadersMiddleware)
- [x] Some files already use escapeHtml (error-handler.js, utils.js, main.js)

### 🔄 Remaining Work

- [ ] Systematic review of 20 files with innerHTML
- [ ] Apply escapeHtml() to ~50-100 template literal locations
- [ ] Test each change for functional and security correctness
- [ ] Document any edge cases or special handling

### ⏱️ Estimated Effort

- **Phase 1** (High Priority): 4-6 hours
- **Phase 2** (Medium Priority): 3-4 hours
- **Phase 3** (Low Priority): 2-3 hours
- **Testing & QA**: 2-3 hours
- **Total**: 11-16 hours (1.5-2 days)

---

## 📚 References

### Security Resources

- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [MDN: textContent vs innerHTML](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)

### Existing Safe Patterns in Codebase

1. **utils.js:438,441** - Toast messages use escapeHtml
2. **utils.js:629,755** - Modal breadcrumbs use escapeHtml
3. **utils.js:891** - Status labels use escapeHtml for unknown values
4. **main.js:554** - Thumbnail modal uses escapeHtml for filename
5. **dashboard.js** - Uses textContent for statistics (safe pattern)

---

## 🎓 Learning Points

### Why innerHTML is Risky

```javascript
// If userName = '<img src=x onerror=alert(1)>'
element.innerHTML = `Welcome ${userName}`; 
// Result: XSS executed ❌

// Safe version:
element.innerHTML = `Welcome ${escapeHtml(userName)}`;
// Result: Text displayed safely ✅
```

### When to Use Each Utility

| Use Case | Utility | Example |
|----------|---------|---------|
| Display user text | `escapeHtml()` | `${escapeHtml(name)}` |
| URL in href/src | `sanitizeUrl()` | `href="${sanitizeUrl(url)}"` |
| Attribute value | `sanitizeAttribute()` | `data-id="${sanitizeAttribute(id)}"` |
| Build DOM structure | `createSafeElement()` | `createSafeElement('div', {}, text)` |
| Set HTML safely | `safeSetInnerHTML()` | `safeSetInnerHTML(el, html, true)` |
| Display numbers/booleans | Direct use (safe) | `${count}` or `${isActive}` |

---

**Next Steps**: Begin systematic application starting with Phase 1 high-priority files.

**Tracking**: Update `progress-tracker.md` as each file is completed.

**Questions**: See technical debt documentation or contact the development team.

