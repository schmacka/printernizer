# Printernizer React Design System

**Date:** 2026-06-24  
**Goal:** Create a React component library from the existing Printernizer vanilla JS/CSS frontend and sync it to claude.ai/design, so the design agent can produce new Printernizer screens using the real visual language.

---

## 1. Approach

CSS-wrapper React library. React components apply the exact CSS class names already present in the Printernizer stylesheets. No re-styling. The bundle ships the existing CSS files unchanged. Output is consumed by the `/design-sync` skill to upload to a claude.ai/design project.

---

## 2. Repository location

New package at `printernizer/frontend/react-ds/` — co-located with the existing frontend so it can import CSS files via relative paths.

```
frontend/react-ds/
├── package.json
├── tsconfig.json
├── build.mjs                 # esbuild script
├── src/
│   ├── index.ts              # barrel export
│   ├── core/                 # generic reusable components
│   │   ├── Button/index.tsx
│   │   ├── Card/index.tsx
│   │   ├── Modal/index.tsx
│   │   ├── Alert/index.tsx
│   │   ├── Badge/index.tsx
│   │   ├── Toast/index.tsx
│   │   ├── Input/index.tsx
│   │   ├── Select/index.tsx
│   │   ├── Table/index.tsx
│   │   ├── Pagination/index.tsx
│   │   ├── SearchBox/index.tsx
│   │   ├── StatCard/index.tsx
│   │   ├── Breadcrumb/index.tsx
│   │   ├── EmptyState/index.tsx
│   │   └── FormGroup/index.tsx
│   ├── domain/               # Printernizer-specific components
│   │   ├── PrinterCard/index.tsx
│   │   ├── PrinterStatusBadge/index.tsx
│   │   ├── JobListItem/index.tsx
│   │   ├── PrintProgressBar/index.tsx
│   │   ├── FileListItem/index.tsx
│   │   ├── FileThumbnail/index.tsx
│   │   ├── CameraView/index.tsx
│   │   ├── StatusBadge/index.tsx
│   │   ├── IdeaCard/index.tsx
│   │   ├── MaterialCard/index.tsx
│   │   ├── PageHeader/index.tsx
│   │   ├── PrinterTypeIcon/index.tsx
│   │   └── NavSidebar/index.tsx
│   └── PrinternizerProvider/
│       └── index.tsx         # theme wrapper, sets data-theme on root div
├── styles/
│   └── entry.css             # @imports all existing CSS files
└── dist/                     # build output (gitignored)
    ├── index.js
    └── styles.css
```

---

## 3. Component inventory

### Core components (15)

| Component | Key props | CSS classes |
|---|---|---|
| `Button` | `variant` (primary/secondary/success/warning/error/ghost), `size` (sm/md/lg), `icon`, `loading`, `disabled` | `.btn .btn-{variant} .btn-{size}` |
| `Card` | `header`, `icon`, `children`, `hoverable` | `.card .card-header .card-body` |
| `Badge` | `variant` (success/warning/error/info/gray), `size` | `.badge .badge-{variant}` |
| `Alert` | `variant`, `title`, `message`, `dismissible`, `onDismiss` | `.alert .alert-{variant}` |
| `Modal` | `open`, `onClose`, `title`, `size` (sm/md/lg), `footer` | `.modal .modal-content .modal-header .modal-body .modal-footer` |
| `Toast` | `variant`, `message`, `duration`, `onDismiss` | `.toast .toast-{variant}` |
| `Input` | `label`, `error`, `hint`, `prefix`, `suffix`, `type` | `.form-group .form-control` |
| `Select` | `label`, `options`, `error`, `value`, `onChange` | `.form-group select` |
| `Table` | `columns`, `data`, `sortable`, `loading`, `emptyMessage` | `.table` |
| `Pagination` | `page`, `totalPages`, `onChange` | `.pagination` |
| `SearchBox` | `value`, `onChange`, `placeholder`, `onClear` | `.search-box` |
| `StatCard` | `label`, `value`, `delta`, `icon`, `variant` | `.stat-card` |
| `Breadcrumb` | `items` (`{label: string, href?: string}[]`) | `.breadcrumb` |
| `EmptyState` | `icon`, `title`, `message`, `action` | `.empty-state` |
| `FormGroup` | `label`, `required`, `error`, `hint`, `children` | `.form-group` |

### Domain components (13)

| Component | Key props | CSS classes |
|---|---|---|
| `PrinterCard` | `printer` (id, name, status, printerType, cameraUrl), `onAction` | `.printer-card .status-{status}` |
| `PrinterStatusBadge` | `status` (idle/printing/error/offline/connecting) | `.status-dot .status-{status}` |
| `JobListItem` | `job` (id, name, printer, progress, status, duration, startedAt) | `.job-list-item` |
| `PrintProgressBar` | `progress` (0–100), `status`, `timeRemaining` | `.progress-bar` |
| `FileListItem` | `file` (id, name, size, type, thumbnailUrl, uploadedAt) | `.file-item` |
| `FileThumbnail` | `src`, `fileType` (stl/3mf/gcode/image), `animated`, `size` | `.file-thumbnail` |
| `CameraView` | `streamUrl`, `snapshotUrl`, `status`, `printerName` | `.camera-feed` |
| `StatusBadge` | `type` (printer/job/file), `status`, `label` | `.status-badge` |
| `IdeaCard` | `idea` (id, title, platform, tags, thumbnailUrl, bookmarked) | `.idea-card` |
| `MaterialCard` | `material` (id, name, color, type, remainingGrams) | `.material-card` |
| `PageHeader` | `title`, `subtitle`, `breadcrumb`, `actions` | `.page-header` |
| `PrinterTypeIcon` | `type` (bambu/prusa), `size` (sm/md/lg) | inline SVG |
| `NavSidebar` | `items` (`{label, icon, href, active}[]`), `connectionStatus`, `appVersion` | `.nav-container .nav-link` |

### Provider

`PrinternizerProvider` — wraps designs, sets `data-theme` on its root `<div>`. Props: `theme` (default/refined/industrial/soft/retro/brutalist), `children`. Required wrapper for all components to render correctly.

---

## 4. CSS bundling

`styles/entry.css` imports the existing Printernizer stylesheets in order:

```css
@import "../../css/main.css";
@import "../../css/components.css";
@import "../../css/dark-theme.css";
@import "../../css/themes/theme-refined.css";
@import "../../css/themes/theme-industrial.css";
@import "../../css/themes/theme-soft.css";
@import "../../css/themes/theme-retro.css";
@import "../../css/themes/theme-brutalist.css";
```

esbuild bundles this to `dist/styles.css`. Components never import CSS themselves — all styling comes from this single entry. This guarantees visual fidelity to the live app with zero maintenance burden on the design system side.

---

## 5. Build setup

**`package.json` scripts:**
- `build` — runs `build.mjs` via Node; produces `dist/index.js` (ESM) and `dist/styles.css`
- `typecheck` — `tsc --noEmit`

**`build.mjs` (esbuild):**
- Entry: `src/index.ts`
- Format: ESM
- Global name (for design-sync bundle header): `PrinternizerDS`
- External: `react`, `react-dom`
- Bundle: true
- Minify: false (readable output aids design agent)
- CSS entry: `styles/entry.css` → `dist/styles.css` (separate esbuild pass)

**TypeScript config:**
- `strict: true`
- `jsx: "react-jsx"`
- `declaration: true` (generates `.d.ts` alongside `dist/index.js`)
- `moduleResolution: "bundler"`

---

## 6. Design-sync integration

After the component library builds cleanly, `/design-sync` is run from `frontend/react-ds/`. The sync skill:
1. Detects shape: `package` (no Storybook)
2. Bundles `dist/index.js` + `dist/styles.css` into the claude.ai/design upload format
3. Generates `.d.ts`-derived type docs and `.prompt.md` usage guides per component
4. Captures HTML preview cards per component
5. Uploads to a new claude.ai/design project named "Printernizer Design System"

The conventions header (authored post-sync) will instruct the design agent to:
- Always wrap in `<PrinternizerProvider theme="default">`
- Never write custom CSS classes for Printernizer UI patterns — use the named components
- Use CSS variables (`var(--primary-color)`, etc.) only for layout glue that has no named component

---

## 7. Out of scope

- Migrating the live Printernizer frontend from vanilla JS to React (this is a design system only)
- Server-side rendering
- Storybook
- npm publish
- Dark mode toggle component (dark theme CSS is bundled; toggling it is out of scope for the design system)
- Additional page CSS files (dashboard.css, library.css, etc.) — only `main.css` and `components.css` are needed for the component library; page-level layout CSS is not component-scoped
