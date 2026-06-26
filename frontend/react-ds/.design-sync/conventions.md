# Printernizer Design System — Conventions

Always wrap every design in `<PrinternizerProvider theme="default">`. This sets CSS custom properties for the default professional-blue theme. Six themes are available: `default`, `refined`, `industrial`, `soft`, `retro`, `brutalist`.

Never write raw CSS classes or inline styles for UI patterns that have a named component. Use the components.

For layout glue that has no component (spacing between sections, page grid), use CSS variables: `var(--spacing-4)`, `var(--gray-100)`, `var(--primary-color)`.

## Component groups

**Core** — generic, reusable: Button, Card, Badge, Alert, Modal, Toast, Input, Select, Table, Pagination, SearchBox, StatCard, Breadcrumb, EmptyState, FormGroup

**Domain** — Printernizer-specific: PrinterCard, PrinterStatusBadge, JobListItem, PrintProgressBar, FileListItem, FileThumbnail, CameraView, StatusBadge, IdeaCard, MaterialCard, PageHeader, PrinterTypeIcon, NavSidebar

## Key conventions

- `Button` variants: `primary` (default CTA), `secondary` (secondary action), `success`/`warning`/`error` (status actions). No ghost variant.
- `Badge` maps to printer/job status dots: use `variant="success"` for completed, `"warning"` for printing, `"error"` for errors, `"gray"` for idle.
- `Table` uses `.professional-table` styling. Pass `columns` with `key` + `header`, and `data` as an array of records.
- Domain components accept a single `printer`/`job`/`file`/`material`/`idea` data object — see each component's Props interface for the shape.
- `NavSidebar` renders a horizontal top navigation bar (matches the Printernizer app's actual layout) despite its name.
