# Printernizer Design System — Sync Notes

## Setup

- Shape: `package` (no Storybook)
- Entry: `dist/index.js` (esbuild ESM)
- CSS: `dist/styles.css` (bundled from all theme files + main + components + materials)
- `.d.ts` generation: tsconfig has `noEmit: true` — run `npx tsc --declaration --emitDeclarationOnly --outDir dist --noEmit false` before the converter. This is required; without it the converter finds 0 components.
- PlayWright version: `1228` — matches `~/.cache/ms-playwright/chromium-1228`

## Known render warns

- `[TOKENS_MISSING]` 70 CSS custom properties — Printernizer defines its CSS vars in `main.css`/`components.css` (always bundled). The tokens that are "missing" in static analysis are theme-specific vars defined in the theme CSS files. Since `PrinternizerProvider` wraps all previews and the CSS is bundled in, rendered previews look correct. Not a real issue.
- `[FONT_REMOTE]` — Space Mono, DM Sans, etc. are loaded from Google Fonts via a remote @import in the Printernizer CSS. Expected behavior.

## Re-sync procedure

```bash
cd frontend/react-ds

# 1. Rebuild the component library
npm run build

# 2. Generate .d.ts (REQUIRED — noEmit:true means tsc won't do this automatically)
npx tsc --declaration --emitDeclarationOnly --outDir dist --noEmit false

# 3. Stage converter scripts (re-copy on every sync to get latest converter)
SKILL_BASE="/tmp/claude-1000/bundled-skills/2.1.187/5e7097dfd7a2ae64a3299b8dfb4b194e/design-sync"
cp -r "$SKILL_BASE/package-build.mjs" "$SKILL_BASE/package-validate.mjs" "$SKILL_BASE/package-capture.mjs" "$SKILL_BASE/resync.mjs" "$SKILL_BASE/lib" "$SKILL_BASE/storybook" .ds-sync/

# 4. Run the resync driver
node .ds-sync/resync.mjs --config .design-sync/config.json --node-modules ./node_modules --entry ./dist/index.js --out ./ds-bundle --remote .design-sync/.cache/remote-sync.json
```

## Re-sync risks

- **`.d.ts` generation step**: must be run manually before every sync — the build.mjs doesn't emit declarations. If skipped, converter finds 0 components.
- **Skill base path**: The SKILL_BASE path `/tmp/claude-1000/bundled-skills/...` is session-specific. On re-sync, find the current path by checking available bundled skills.
- **Authored previews** (`.design-sync/previews/*.tsx`): Input, StatCard, IdeaCard, JobListItem, PrintProgressBar. These are committed and carry forward. Re-sync will pick them up automatically.
- **10 floor-card components**: these have no authored previews and show the typographic floor card. They can be authored incrementally on any re-sync. Components: Alert, Badge, Breadcrumb, Button, Card, EmptyState, FormGroup, Modal, Pagination, SearchBox, Select, Table, Toast (core) + CameraView, FileListItem, FileThumbnail, MaterialCard, NavSidebar, PageHeader, PrinterCard, PrinterStatusBadge, PrinterTypeIcon, StatusBadge (domain) — minus the 5 authored above.
- **NavSidebar naming**: despite the name, this component renders a horizontal top navigation bar (matching the actual Printernizer app). The design agent should be aware of this — it's documented in conventions.md.
