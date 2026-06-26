# Printernizer Design System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React component library at `frontend/react-ds/` that wraps Printernizer's existing CSS class names, builds to ESM + CSS via esbuild, and is ready for `/design-sync` to upload to claude.ai/design.

**Architecture:** 28 TypeScript React components split into `src/core/` (generic) and `src/domain/` (Printernizer-specific), all using existing CSS class names from `frontend/css/`. A single `PrinternizerProvider` sets the active theme. `styles/entry.css` imports the existing stylesheets; esbuild compiles JS + CSS to `dist/`.

**Tech Stack:** TypeScript 5.x, React 18, esbuild 0.25.x, Node 24.x, npm.

## Global Constraints

- All files live under `frontend/react-ds/` — never modify anything outside this directory
- Components apply CSS classes from existing stylesheets only — no new CSS in component files
- Global bundle name for design-sync: `PrinternizerDS`
- TypeScript `strict: true`, `jsx: "react-jsx"`
- React and react-dom are `peerDependencies` (externalized from bundle)
- `dist/` is gitignored via `frontend/react-ds/.gitignore`
- Commit style: Conventional Commits (`feat:`, `chore:`)
- CSS entry path: `styles/entry.css` → `@import "../../css/main.css"` etc.

---

### Task 1: Scaffold the package

**Files:**
- Create: `frontend/react-ds/package.json`
- Create: `frontend/react-ds/tsconfig.json`
- Create: `frontend/react-ds/build.mjs`
- Create: `frontend/react-ds/styles/entry.css`
- Create: `frontend/react-ds/.gitignore`
- Create: `frontend/react-ds/src/index.ts` (empty barrel, grows in later tasks)

**Interfaces:**
- Produces: `npm run build` outputs `dist/index.js` and `dist/styles.css`; `npm run typecheck` passes

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p frontend/react-ds/src/core frontend/react-ds/src/domain frontend/react-ds/styles
```

- [ ] **Step 2: Write `frontend/react-ds/package.json`**

```json
{
  "name": "@printernizer/design-system",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "node build.mjs",
    "typecheck": "tsc --noEmit"
  },
  "peerDependencies": {
    "react": ">=18",
    "react-dom": ">=18"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "esbuild": "^0.25.0",
    "typescript": "^5.5.0"
  }
}
```

- [ ] **Step 3: Write `frontend/react-ds/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "declaration": true,
    "declarationDir": "dist",
    "outDir": "dist",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Write `frontend/react-ds/build.mjs`**

```js
import * as esbuild from 'esbuild';
import { mkdirSync } from 'fs';

mkdirSync('dist', { recursive: true });

// JS bundle
await esbuild.build({
  entryPoints: ['src/index.ts'],
  bundle: true,
  format: 'esm',
  outfile: 'dist/index.js',
  external: ['react', 'react-dom', 'react/jsx-runtime'],
  minify: false,
  sourcemap: false,
  target: ['es2020'],
});

// CSS bundle
await esbuild.build({
  entryPoints: ['styles/entry.css'],
  bundle: true,
  outfile: 'dist/styles.css',
  loader: { '.css': 'css' },
  minify: false,
});

console.log('Build complete: dist/index.js + dist/styles.css');
```

- [ ] **Step 5: Write `frontend/react-ds/styles/entry.css`**

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

- [ ] **Step 6: Write `frontend/react-ds/.gitignore`**

```
dist/
node_modules/
```

- [ ] **Step 7: Write `frontend/react-ds/src/index.ts`** (empty barrel for now)

```ts
// components exported in later tasks
export {};
```

- [ ] **Step 8: Install dependencies**

```bash
cd frontend/react-ds && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 9: Verify the build runs**

```bash
cd frontend/react-ds && npm run build
```

Expected output:
```
Build complete: dist/index.js + dist/styles.css
```
Both files must exist. `dist/styles.css` should be non-empty (it bundles all Printernizer CSS).

- [ ] **Step 10: Verify typecheck passes**

```bash
cd frontend/react-ds && npm run typecheck
```

Expected: no errors.

- [ ] **Step 11: Commit**

```bash
git add frontend/react-ds/
git commit -m "feat: scaffold Printernizer React design system package"
```

---

### Task 2: PrinternizerProvider

**Files:**
- Create: `frontend/react-ds/src/PrinternizerProvider/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- Produces: `PrinternizerProvider`, `PrinternizerTheme` exported from package root

- [ ] **Step 1: Write `frontend/react-ds/src/PrinternizerProvider/index.tsx`**

```tsx
import React from 'react';

export type PrinternizerTheme =
  | 'default'
  | 'refined'
  | 'industrial'
  | 'soft'
  | 'retro'
  | 'brutalist';

export interface PrinternizerProviderProps {
  theme?: PrinternizerTheme;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export function PrinternizerProvider({
  theme = 'default',
  children,
  className,
  style,
}: PrinternizerProviderProps) {
  return (
    <div
      data-theme={theme === 'default' ? undefined : theme}
      className={className}
      style={{ minHeight: '100%', ...style }}
    >
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Update `frontend/react-ds/src/index.ts`**

```ts
export { PrinternizerProvider } from './PrinternizerProvider';
export type { PrinternizerProviderProps, PrinternizerTheme } from './PrinternizerProvider';
```

- [ ] **Step 3: Verify typecheck passes**

```bash
cd frontend/react-ds && npm run typecheck
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add PrinternizerProvider theme wrapper"
```

---

### Task 3: Button and Card

**Files:**
- Create: `frontend/react-ds/src/core/Button/index.tsx`
- Create: `frontend/react-ds/src/core/Card/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- Produces: `Button`, `ButtonProps`, `Card`, `CardProps` exported from package root
- CSS classes used: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-success`, `.btn-warning`, `.btn-error`, `.btn-sm`, `.btn-lg`, `.btn-icon`, `.card`, `.card-header`, `.card-body`, `.card-icon`

- [ ] **Step 1: Write `frontend/react-ds/src/core/Button/index.tsx`**

```tsx
import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  loading?: boolean;
  children: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size,
  icon,
  loading = false,
  children,
  className,
  disabled,
  ...rest
}: ButtonProps) {
  const classes = [
    'btn',
    `btn-${variant}`,
    size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : '',
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={classes} disabled={disabled || loading} {...rest}>
      {icon && <span className="btn-icon">{icon}</span>}
      {loading ? '...' : children}
    </button>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/core/Card/index.tsx`**

```tsx
import React from 'react';

export interface CardProps {
  header?: React.ReactNode;
  icon?: React.ReactNode;
  children: React.ReactNode;
  hoverable?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function Card({ header, icon, children, hoverable = false, className, style }: CardProps) {
  return (
    <div className={['card', hoverable ? 'hoverable' : '', className ?? ''].filter(Boolean).join(' ')} style={style}>
      {(header || icon) && (
        <div className="card-header">
          {icon && <span className="card-icon">{icon}</span>}
          {header && <h3>{header}</h3>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
}
```

- [ ] **Step 3: Update `frontend/react-ds/src/index.ts`**

```ts
export { PrinternizerProvider } from './PrinternizerProvider';
export type { PrinternizerProviderProps, PrinternizerTheme } from './PrinternizerProvider';

export { Button } from './core/Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './core/Button';

export { Card } from './core/Card';
export type { CardProps } from './core/Card';
```

- [ ] **Step 4: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors; `dist/index.js` updated.

- [ ] **Step 5: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add Button and Card core components"
```

---

### Task 4: Badge, Alert, Toast, Breadcrumb, EmptyState, StatCard

**Files:**
- Create: `frontend/react-ds/src/core/Badge/index.tsx`
- Create: `frontend/react-ds/src/core/Alert/index.tsx`
- Create: `frontend/react-ds/src/core/Toast/index.tsx`
- Create: `frontend/react-ds/src/core/Breadcrumb/index.tsx`
- Create: `frontend/react-ds/src/core/EmptyState/index.tsx`
- Create: `frontend/react-ds/src/core/StatCard/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- CSS classes used: `.status-badge`, `.status-online`, `.status-offline`, `.status-printing`, `.status-idle`, `.status-error`, `.status-completed`, `.alert`, `.alert-success`, `.alert-warning`, `.alert-error`, `.alert-info`, `.toast`, `.toast-header`, `.toast-title`, `.toast-close`, `.toast-body`, `.toast-success`, `.toast-warning`, `.toast-error`, `.toast-info`, `.breadcrumb-back`, `.breadcrumb-separator`, `.empty-state`, `.stat-card`, `.stat-value`, `.stat-label`

- [ ] **Step 1: Write `frontend/react-ds/src/core/Badge/index.tsx`**

Note: The existing CSS uses `.status-badge` + `.status-{variant}` for all semantic pill badges. `Badge` maps to those classes.

```tsx
import React from 'react';

export type BadgeVariant = 'success' | 'error' | 'warning' | 'info' | 'gray';

const variantClass: Record<BadgeVariant, string> = {
  success: 'status-completed',
  error: 'status-error',
  warning: 'status-printing',
  info: 'status-online',
  gray: 'status-idle',
};

export interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

export function Badge({ variant = 'gray', children, className }: BadgeProps) {
  return (
    <span className={['status-badge', variantClass[variant], className ?? ''].filter(Boolean).join(' ')}>
      {children}
    </span>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/core/Alert/index.tsx`**

```tsx
import React from 'react';

export type AlertVariant = 'success' | 'warning' | 'error' | 'info';

export interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  message: React.ReactNode;
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

export function Alert({ variant = 'info', title, message, dismissible, onDismiss, className }: AlertProps) {
  return (
    <div className={['alert', `alert-${variant}`, className ?? ''].filter(Boolean).join(' ')}>
      {title && <strong>{title} </strong>}
      {message}
      {dismissible && (
        <button
          onClick={onDismiss}
          style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem' }}
          aria-label="Dismiss"
        >
          ×
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Write `frontend/react-ds/src/core/Toast/index.tsx`**

```tsx
import React from 'react';

export type ToastVariant = 'success' | 'warning' | 'error' | 'info';

export interface ToastProps {
  variant?: ToastVariant;
  title?: string;
  message: React.ReactNode;
  onDismiss?: () => void;
  className?: string;
}

export function Toast({ variant = 'info', title, message, onDismiss, className }: ToastProps) {
  return (
    <div className={['toast', `toast-${variant}`, className ?? ''].filter(Boolean).join(' ')}>
      <div className="toast-header">
        {title && <span className="toast-title">{title}</span>}
        {onDismiss && (
          <button className="toast-close" onClick={onDismiss} aria-label="Close">
            ×
          </button>
        )}
      </div>
      <div className="toast-body">{message}</div>
    </div>
  );
}
```

- [ ] **Step 4: Write `frontend/react-ds/src/core/Breadcrumb/index.tsx`**

```tsx
import React from 'react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  return (
    <nav className={['breadcrumb-nav', className ?? ''].filter(Boolean).join(' ')} aria-label="Breadcrumb">
      {items.map((item, i) => (
        <React.Fragment key={i}>
          {i > 0 && <span className="breadcrumb-separator">›</span>}
          {item.href ? (
            <a className="breadcrumb-back" href={item.href}>
              {item.label}
            </a>
          ) : (
            <span>{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}
```

- [ ] **Step 5: Write `frontend/react-ds/src/core/EmptyState/index.tsx`**

```tsx
import React from 'react';

export interface EmptyStateAction {
  label: string;
  onClick: () => void;
}

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  message?: string;
  action?: EmptyStateAction;
  className?: string;
}

export function EmptyState({ icon, title, message, action, className }: EmptyStateProps) {
  return (
    <div className={['empty-state', className ?? ''].filter(Boolean).join(' ')}>
      {icon && <div>{icon}</div>}
      <h3>{title}</h3>
      {message && <p>{message}</p>}
      {action && (
        <button className="btn btn-primary" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Write `frontend/react-ds/src/core/StatCard/index.tsx`**

```tsx
import React from 'react';

export interface StatCardProps {
  label: string;
  value: React.ReactNode;
  delta?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({ label, value, delta, icon, className }: StatCardProps) {
  return (
    <div className={['stat-card', className ?? ''].filter(Boolean).join(' ')}>
      {icon && <div className="stat-icon">{icon}</div>}
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {delta && <div className="stat-delta">{delta}</div>}
    </div>
  );
}
```

- [ ] **Step 7: Update `frontend/react-ds/src/index.ts`**

```ts
export { PrinternizerProvider } from './PrinternizerProvider';
export type { PrinternizerProviderProps, PrinternizerTheme } from './PrinternizerProvider';

export { Button } from './core/Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './core/Button';

export { Card } from './core/Card';
export type { CardProps } from './core/Card';

export { Badge } from './core/Badge';
export type { BadgeProps, BadgeVariant } from './core/Badge';

export { Alert } from './core/Alert';
export type { AlertProps, AlertVariant } from './core/Alert';

export { Toast } from './core/Toast';
export type { ToastProps, ToastVariant } from './core/Toast';

export { Breadcrumb } from './core/Breadcrumb';
export type { BreadcrumbProps, BreadcrumbItem } from './core/Breadcrumb';

export { EmptyState } from './core/EmptyState';
export type { EmptyStateProps, EmptyStateAction } from './core/EmptyState';

export { StatCard } from './core/StatCard';
export type { StatCardProps } from './core/StatCard';
```

- [ ] **Step 8: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 9: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add Badge, Alert, Toast, Breadcrumb, EmptyState, StatCard"
```

---

### Task 5: FormGroup, Input, Select, SearchBox

**Files:**
- Create: `frontend/react-ds/src/core/FormGroup/index.tsx`
- Create: `frontend/react-ds/src/core/Input/index.tsx`
- Create: `frontend/react-ds/src/core/Select/index.tsx`
- Create: `frontend/react-ds/src/core/SearchBox/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- CSS classes used: `.form-group`, `.form-control`, `.form-control.error`, `.search-controls`, `.search-input-wrapper`, `.search-input`, `.search-clear-btn`, `.search-icon`

- [ ] **Step 1: Write `frontend/react-ds/src/core/FormGroup/index.tsx`**

```tsx
import React from 'react';

export interface FormGroupProps {
  label?: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormGroup({ label, required, error, hint, children, className }: FormGroupProps) {
  return (
    <div className={['form-group', className ?? ''].filter(Boolean).join(' ')}>
      {label && (
        <label>
          {label}
          {required && <span style={{ color: 'var(--error-color)' }}> *</span>}
        </label>
      )}
      {children}
      {hint && !error && <small style={{ color: 'var(--gray-500)', display: 'block', marginTop: '0.25rem' }}>{hint}</small>}
      {error && <small style={{ color: 'var(--error-color)', display: 'block', marginTop: '0.25rem' }}>{error}</small>}
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/core/Input/index.tsx`**

```tsx
import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
}

export function Input({ label, error, hint, prefix, suffix, className, required, ...rest }: InputProps) {
  return (
    <div className="form-group">
      {label && (
        <label>
          {label}
          {required && <span style={{ color: 'var(--error-color)' }}> *</span>}
        </label>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {prefix && <span>{prefix}</span>}
        <input
          className={['form-control', error ? 'error' : '', className ?? ''].filter(Boolean).join(' ')}
          required={required}
          {...rest}
        />
        {suffix && <span>{suffix}</span>}
      </div>
      {hint && !error && <small style={{ color: 'var(--gray-500)', display: 'block', marginTop: '0.25rem' }}>{hint}</small>}
      {error && <small style={{ color: 'var(--error-color)', display: 'block', marginTop: '0.25rem' }}>{error}</small>}
    </div>
  );
}
```

- [ ] **Step 3: Write `frontend/react-ds/src/core/Select/index.tsx`**

```tsx
import React from 'react';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps {
  label?: string;
  options: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export function Select({ label, options, value, onChange, error, placeholder, required, disabled, className }: SelectProps) {
  return (
    <div className="form-group">
      {label && (
        <label>
          {label}
          {required && <span style={{ color: 'var(--error-color)' }}> *</span>}
        </label>
      )}
      <select
        className={['form-control', error ? 'error' : '', className ?? ''].filter(Boolean).join(' ')}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        required={required}
        disabled={disabled}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <small style={{ color: 'var(--error-color)', display: 'block', marginTop: '0.25rem' }}>{error}</small>}
    </div>
  );
}
```

- [ ] **Step 4: Write `frontend/react-ds/src/core/SearchBox/index.tsx`**

```tsx
import React from 'react';

export interface SearchBoxProps {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  className?: string;
}

export function SearchBox({ value, onChange, onClear, placeholder = 'Search…', className }: SearchBoxProps) {
  return (
    <div className={['search-controls', className ?? ''].filter(Boolean).join(' ')}>
      <div className="search-input-wrapper">
        <span className="search-icon">🔍</span>
        <input
          type="search"
          className="search-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
        {value && (
          <button className="search-clear-btn" onClick={() => { onChange(''); onClear?.(); }} aria-label="Clear search">
            ×
          </button>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Update `frontend/react-ds/src/index.ts`** — append:

```ts
export { FormGroup } from './core/FormGroup';
export type { FormGroupProps } from './core/FormGroup';

export { Input } from './core/Input';
export type { InputProps } from './core/Input';

export { Select } from './core/Select';
export type { SelectProps, SelectOption } from './core/Select';

export { SearchBox } from './core/SearchBox';
export type { SearchBoxProps } from './core/SearchBox';
```

- [ ] **Step 6: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add FormGroup, Input, Select, SearchBox"
```

---

### Task 6: Modal

**Files:**
- Create: `frontend/react-ds/src/core/Modal/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- CSS classes used: `.modal`, `.modal.show`, `.modal-content`, `.modal-content.large`, `.modal-header`, `.modal-close`, `.modal-body`, `.modal-footer`

- [ ] **Step 1: Write `frontend/react-ds/src/core/Modal/index.tsx`**

```tsx
import React from 'react';

export type ModalSize = 'sm' | 'md' | 'lg';

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  size?: ModalSize;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, size = 'md', footer, children, className }: ModalProps) {
  if (!open) return null;

  return (
    <div className="modal show" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={['modal-content', size === 'lg' ? 'large' : '', className ?? ''].filter(Boolean).join(' ')}>
        {title && (
          <div className="modal-header">
            <h3>{title}</h3>
            <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
          </div>
        )}
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Append to `frontend/react-ds/src/index.ts`**

```ts
export { Modal } from './core/Modal';
export type { ModalProps, ModalSize } from './core/Modal';
```

- [ ] **Step 3: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add Modal"
```

---

### Task 7: Table and Pagination

**Files:**
- Create: `frontend/react-ds/src/core/Table/index.tsx`
- Create: `frontend/react-ds/src/core/Pagination/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- CSS classes used: `.professional-table`, `.table-container`, `.pagination`, `.pagination-btn`, `.pagination-btn.active`, `.pagination-info`

- [ ] **Step 1: Write `frontend/react-ds/src/core/Table/index.tsx`**

```tsx
import React from 'react';

export interface TableColumn<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
  sortable?: boolean;
}

export interface TableProps<T extends Record<string, unknown>> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function Table<T extends Record<string, unknown>>({
  columns,
  data,
  loading,
  emptyMessage = 'No data',
  className,
}: TableProps<T>) {
  return (
    <div className={['table-container', className ?? ''].filter(Boolean).join(' ')}>
      <table className="professional-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={String(col.key)}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} style={{ textAlign: 'center', padding: '2rem' }}>
                Loading…
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={{ textAlign: 'center', padding: '2rem', color: 'var(--gray-500)' }}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIdx) => (
              <tr key={rowIdx}>
                {columns.map((col) => (
                  <td key={String(col.key)}>
                    {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/core/Pagination/index.tsx`**

```tsx
import React from 'react';

export interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
  className?: string;
}

export function Pagination({ page, totalPages, onChange, className }: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className={['pagination', className ?? ''].filter(Boolean).join(' ')}>
      <button
        className="pagination-btn"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        ‹
      </button>
      {pages.map((p) => (
        <button
          key={p}
          className={['pagination-btn', p === page ? 'active' : ''].filter(Boolean).join(' ')}
          onClick={() => onChange(p)}
        >
          {p}
        </button>
      ))}
      <button
        className="pagination-btn"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
      >
        ›
      </button>
      <span className="pagination-info">
        Page {page} of {totalPages}
      </span>
    </div>
  );
}
```

- [ ] **Step 3: Append to `frontend/react-ds/src/index.ts`**

```ts
export { Table } from './core/Table';
export type { TableProps, TableColumn } from './core/Table';

export { Pagination } from './core/Pagination';
export type { PaginationProps } from './core/Pagination';
```

- [ ] **Step 4: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add Table and Pagination"
```

---

### Task 8: PageHeader and NavSidebar

**Files:**
- Create: `frontend/react-ds/src/domain/PageHeader/index.tsx`
- Create: `frontend/react-ds/src/domain/NavSidebar/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- CSS classes used: `.page-header`, `.nav-container`, `.nav-menu`, `.nav-link`, `.nav-link.active`, `.nav-icon`, `.nav-brand`, `.status-dot`, `.status-dot.connected`, `.status-dot.disconnected`, `.status-dot.connecting`

- [ ] **Step 1: Write `frontend/react-ds/src/domain/PageHeader/index.tsx`**

```tsx
import React from 'react';

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumb?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, subtitle, breadcrumb, actions, className }: PageHeaderProps) {
  return (
    <div className={['page-header', className ?? ''].filter(Boolean).join(' ')}>
      {breadcrumb && <div className="page-breadcrumb">{breadcrumb}</div>}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>{title}</h1>
          {subtitle && <p style={{ color: 'var(--gray-500)', marginBottom: 0 }}>{subtitle}</p>}
        </div>
        {actions && <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>{actions}</div>}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/domain/NavSidebar/index.tsx`**

```tsx
import React from 'react';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

export interface NavItem {
  label: string;
  icon?: React.ReactNode;
  href: string;
  active?: boolean;
}

export interface NavSidebarProps {
  items: NavItem[];
  connectionStatus?: ConnectionStatus;
  appVersion?: string;
  className?: string;
}

export function NavSidebar({ items, connectionStatus, appVersion, className }: NavSidebarProps) {
  return (
    <nav className={['nav-container', className ?? ''].filter(Boolean).join(' ')}>
      <div className="nav-brand">Printernizer</div>
      <ul className="nav-menu" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
        {items.map((item) => (
          <li key={item.href}>
            <a
              href={item.href}
              className={['nav-link', item.active ? 'active' : ''].filter(Boolean).join(' ')}
            >
              {item.icon && <span className="nav-icon">{item.icon}</span>}
              {item.label}
            </a>
          </li>
        ))}
      </ul>
      {connectionStatus && (
        <div className="nav-status" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className={`status-dot ${connectionStatus}`} />
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--gray-500)' }}>
            {connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting…' : 'Disconnected'}
          </span>
        </div>
      )}
      {appVersion && (
        <div style={{ padding: '0 1rem 1rem', fontSize: 'var(--font-size-xs)', color: 'var(--gray-400)' }}>
          v{appVersion}
        </div>
      )}
    </nav>
  );
}
```

- [ ] **Step 3: Append to `frontend/react-ds/src/index.ts`**

```ts
export { PageHeader } from './domain/PageHeader';
export type { PageHeaderProps } from './domain/PageHeader';

export { NavSidebar } from './domain/NavSidebar';
export type { NavSidebarProps, NavItem, ConnectionStatus } from './domain/NavSidebar';
```

- [ ] **Step 4: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add PageHeader and NavSidebar domain components"
```

---

### Task 9: PrinterStatusBadge, StatusBadge, PrinterTypeIcon

**Files:**
- Create: `frontend/react-ds/src/domain/PrinterStatusBadge/index.tsx`
- Create: `frontend/react-ds/src/domain/StatusBadge/index.tsx`
- Create: `frontend/react-ds/src/domain/PrinterTypeIcon/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- CSS classes used: `.status-dot`, `.status-dot.connected`, `.status-dot.disconnected`, `.status-dot.connecting`, `.status-badge`, `.status-idle`, `.status-printing`, `.status-error`, `.status-completed`, `.status-offline`, `.status-planned`, `.status-idea`, `.status-archived`

- [ ] **Step 1: Write `frontend/react-ds/src/domain/PrinterStatusBadge/index.tsx`**

```tsx
import React from 'react';

export type PrinterStatus = 'idle' | 'printing' | 'error' | 'offline' | 'connecting';

export interface PrinterStatusBadgeProps {
  status: PrinterStatus;
  showLabel?: boolean;
  className?: string;
}

const dotClass: Record<PrinterStatus, string> = {
  idle: 'connected',
  printing: 'connected',
  error: 'disconnected',
  offline: 'disconnected',
  connecting: 'connecting',
};

const labels: Record<PrinterStatus, string> = {
  idle: 'Idle',
  printing: 'Printing',
  error: 'Error',
  offline: 'Offline',
  connecting: 'Connecting',
};

export function PrinterStatusBadge({ status, showLabel = true, className }: PrinterStatusBadgeProps) {
  return (
    <span
      className={['status-badge', `status-${status}`, className ?? ''].filter(Boolean).join(' ')}
    >
      <span className={`status-dot ${dotClass[status]}`} />
      {showLabel && labels[status]}
    </span>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/domain/StatusBadge/index.tsx`**

```tsx
import React from 'react';

export type IdeaStatus = 'idea' | 'planned' | 'printing' | 'completed' | 'archived';

export interface StatusBadgeProps {
  status: IdeaStatus;
  label?: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const displayLabel = label ?? status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span className={['status-badge', `status-${status}`, className ?? ''].filter(Boolean).join(' ')}>
      {displayLabel}
    </span>
  );
}
```

- [ ] **Step 3: Write `frontend/react-ds/src/domain/PrinterTypeIcon/index.tsx`**

```tsx
import React from 'react';

export type PrinterType = 'bambu' | 'prusa';
export type IconSize = 'sm' | 'md' | 'lg';

export interface PrinterTypeIconProps {
  type: PrinterType;
  size?: IconSize;
  className?: string;
}

const sizePx: Record<IconSize, number> = { sm: 16, md: 24, lg: 32 };

export function PrinterTypeIcon({ type, size = 'md', className }: PrinterTypeIconProps) {
  const px = sizePx[size];

  if (type === 'bambu') {
    return (
      <svg
        width={px}
        height={px}
        viewBox="0 0 24 24"
        fill="none"
        className={className}
        aria-label="Bambu Lab"
      >
        <rect width="24" height="24" rx="4" fill="#F97316" />
        <text x="12" y="17" textAnchor="middle" fill="white" fontSize="13" fontWeight="bold">B</text>
      </svg>
    );
  }

  return (
    <svg
      width={px}
      height={px}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-label="Prusa"
    >
      <rect width="24" height="24" rx="4" fill="#DC2626" />
      <text x="12" y="17" textAnchor="middle" fill="white" fontSize="13" fontWeight="bold">P</text>
    </svg>
  );
}
```

- [ ] **Step 4: Append to `frontend/react-ds/src/index.ts`**

```ts
export { PrinterStatusBadge } from './domain/PrinterStatusBadge';
export type { PrinterStatusBadgeProps, PrinterStatus } from './domain/PrinterStatusBadge';

export { StatusBadge } from './domain/StatusBadge';
export type { StatusBadgeProps, IdeaStatus } from './domain/StatusBadge';

export { PrinterTypeIcon } from './domain/PrinterTypeIcon';
export type { PrinterTypeIconProps, PrinterType, IconSize } from './domain/PrinterTypeIcon';
```

- [ ] **Step 5: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add PrinterStatusBadge, StatusBadge, PrinterTypeIcon"
```

---

### Task 10: PrintProgressBar and PrinterCard

**Files:**
- Create: `frontend/react-ds/src/domain/PrintProgressBar/index.tsx`
- Create: `frontend/react-ds/src/domain/PrinterCard/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- Consumes: `PrinterStatusBadge`, `PrinterStatus` from Task 9; `PrinterTypeIcon`, `PrinterType` from Task 9
- CSS classes used: `.progress`, `.progress-bar`, `.progress-success`, `.progress-warning`, `.progress-error`, `.progress-animated`, `.progress-header`, `.progress-label`, `.progress-details`, `.printer-card`, `.card`, `.card-header`, `.card-body`, `.connection-indicator`

- [ ] **Step 1: Write `frontend/react-ds/src/domain/PrintProgressBar/index.tsx`**

```tsx
import React from 'react';

export type ProgressStatus = 'printing' | 'success' | 'error' | 'warning';

export interface PrintProgressBarProps {
  progress: number;
  status?: ProgressStatus;
  timeRemaining?: string;
  label?: string;
  className?: string;
}

const statusClass: Record<ProgressStatus, string> = {
  printing: 'progress-animated',
  success: 'progress-success',
  error: 'progress-error',
  warning: 'progress-warning',
};

export function PrintProgressBar({ progress, status = 'printing', timeRemaining, label, className }: PrintProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, progress));
  return (
    <div className={['progress-wrapper', statusClass[status], className ?? ''].filter(Boolean).join(' ')}>
      {(label || timeRemaining) && (
        <div className="progress-header">
          {label && <span className="progress-label">{label}</span>}
          {timeRemaining && <span className="progress-details">{timeRemaining}</span>}
        </div>
      )}
      <div className="progress">
        <div
          className="progress-bar"
          style={{ width: `${clamped}%` }}
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/domain/PrinterCard/index.tsx`**

```tsx
import React from 'react';
import { PrinterStatusBadge } from '../PrinterStatusBadge';
import type { PrinterStatus } from '../PrinterStatusBadge';
import { PrinterTypeIcon } from '../PrinterTypeIcon';
import type { PrinterType } from '../PrinterTypeIcon';
import { PrintProgressBar } from '../PrintProgressBar';

export interface PrinterData {
  id: string;
  name: string;
  status: PrinterStatus;
  printerType: PrinterType;
  cameraUrl?: string;
  progress?: number;
  currentFile?: string;
  timeRemaining?: string;
}

export interface PrinterCardProps {
  printer: PrinterData;
  onAction?: (action: 'pause' | 'resume' | 'cancel' | 'settings', printerId: string) => void;
  monitoring?: boolean;
  className?: string;
}

export function PrinterCard({ printer, onAction, monitoring = false, className }: PrinterCardProps) {
  return (
    <div
      className={[
        'card',
        'printer-card',
        monitoring ? 'monitoring-active' : '',
        className ?? '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <PrinterTypeIcon type={printer.printerType} size="md" />
          <div>
            <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)', fontWeight: 600 }}>{printer.name}</h3>
            <PrinterStatusBadge status={printer.status} />
          </div>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onAction?.('settings', printer.id)}
          aria-label="Printer settings"
        >
          ⚙
        </button>
      </div>
      <div className="card-body">
        {printer.cameraUrl ? (
          <img
            src={printer.cameraUrl}
            alt={`${printer.name} camera`}
            style={{ width: '100%', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}
          />
        ) : (
          <div className="camera-placeholder">
            <span className="camera-icon">📷</span>
            <span className="camera-text">No camera</span>
          </div>
        )}
        {printer.status === 'printing' && printer.progress !== undefined && (
          <PrintProgressBar
            progress={printer.progress}
            status="printing"
            label={printer.currentFile}
            timeRemaining={printer.timeRemaining}
          />
        )}
        {printer.status === 'printing' && (
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
            <button className="btn btn-warning btn-sm" onClick={() => onAction?.('pause', printer.id)}>
              Pause
            </button>
            <button className="btn btn-error btn-sm" onClick={() => onAction?.('cancel', printer.id)}>
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Append to `frontend/react-ds/src/index.ts`**

```ts
export { PrintProgressBar } from './domain/PrintProgressBar';
export type { PrintProgressBarProps, ProgressStatus } from './domain/PrintProgressBar';

export { PrinterCard } from './domain/PrinterCard';
export type { PrinterCardProps, PrinterData } from './domain/PrinterCard';
```

- [ ] **Step 4: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add PrintProgressBar and PrinterCard"
```

---

### Task 11: JobListItem, FileListItem, FileThumbnail

**Files:**
- Create: `frontend/react-ds/src/domain/JobListItem/index.tsx`
- Create: `frontend/react-ds/src/domain/FileThumbnail/index.tsx`
- Create: `frontend/react-ds/src/domain/FileListItem/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- Consumes: `PrinterStatus` from Task 9
- CSS classes used: `.file-item`, `.file-thumbnail`, `.status-badge`, `.status-printing`, `.status-completed`, `.status-error`, `.status-idle`

- [ ] **Step 1: Write `frontend/react-ds/src/domain/FileThumbnail/index.tsx`**

```tsx
import React from 'react';

export type FileType = 'stl' | '3mf' | 'gcode' | 'image';
export type ThumbnailSize = 'sm' | 'md' | 'lg';

export interface FileThumbnailProps {
  src?: string;
  fileType: FileType;
  animated?: boolean;
  size?: ThumbnailSize;
  alt?: string;
  className?: string;
}

const sizePx: Record<ThumbnailSize, number> = { sm: 48, md: 80, lg: 128 };
const typeEmoji: Record<FileType, string> = { stl: '🧊', '3mf': '🖨', gcode: '📄', image: '🖼' };

export function FileThumbnail({ src, fileType, animated, size = 'md', alt, className }: FileThumbnailProps) {
  const px = sizePx[size];
  return (
    <div
      className={['file-thumbnail', animated ? 'animated' : '', className ?? ''].filter(Boolean).join(' ')}
      style={{ width: px, height: px, flexShrink: 0 }}
    >
      {src ? (
        <img src={src} alt={alt ?? fileType} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'var(--radius-md)' }} />
      ) : (
        <span style={{ fontSize: px * 0.5, display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          {typeEmoji[fileType]}
        </span>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/domain/JobListItem/index.tsx`**

```tsx
import React from 'react';
import type { PrinterStatus } from '../PrinterStatusBadge';

export interface JobData {
  id: string;
  name: string;
  printer: string;
  progress: number;
  status: PrinterStatus;
  duration?: string;
  startedAt?: string;
}

export interface JobListItemProps {
  job: JobData;
  onClick?: (jobId: string) => void;
  className?: string;
}

const jobStatusClass: Record<PrinterStatus, string> = {
  printing: 'status-printing',
  idle: 'status-idle',
  error: 'status-error',
  offline: 'status-offline',
  connecting: 'status-idle',
};

export function JobListItem({ job, onClick, className }: JobListItemProps) {
  return (
    <div
      className={['file-item', className ?? ''].filter(Boolean).join(' ')}
      onClick={() => onClick?.(job.id)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, color: 'var(--gray-900)' }}>{job.name}</div>
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--gray-500)' }}>
            {job.printer} {job.startedAt && `· ${job.startedAt}`}
          </div>
        </div>
        {job.status === 'printing' && (
          <div style={{ width: 120 }}>
            <div className="progress">
              <div className="progress-bar" style={{ width: `${job.progress}%` }} />
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--gray-500)', marginTop: '0.25rem' }}>
              {job.progress}%
            </div>
          </div>
        )}
        <span className={`status-badge ${jobStatusClass[job.status]}`}>
          {job.status}
        </span>
        {job.duration && (
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--gray-500)' }}>{job.duration}</span>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write `frontend/react-ds/src/domain/FileListItem/index.tsx`**

```tsx
import React from 'react';
import { FileThumbnail } from '../FileThumbnail';
import type { FileType } from '../FileThumbnail';

export interface FileData {
  id: string;
  name: string;
  size: string;
  type: FileType;
  thumbnailUrl?: string;
  uploadedAt?: string;
}

export interface FileListItemProps {
  file: FileData;
  onClick?: (fileId: string) => void;
  actions?: React.ReactNode;
  className?: string;
}

export function FileListItem({ file, onClick, actions, className }: FileListItemProps) {
  return (
    <div
      className={['file-item', className ?? ''].filter(Boolean).join(' ')}
      onClick={() => onClick?.(file.id)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <FileThumbnail src={file.thumbnailUrl} fileType={file.type} size="sm" alt={file.name} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, color: 'var(--gray-900)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {file.name}
        </div>
        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--gray-500)' }}>
          {file.size} {file.uploadedAt && `· ${file.uploadedAt}`}
        </div>
      </div>
      {actions && <div onClick={(e) => e.stopPropagation()}>{actions}</div>}
    </div>
  );
}
```

- [ ] **Step 4: Append to `frontend/react-ds/src/index.ts`**

```ts
export { FileThumbnail } from './domain/FileThumbnail';
export type { FileThumbnailProps, FileType, ThumbnailSize } from './domain/FileThumbnail';

export { JobListItem } from './domain/JobListItem';
export type { JobListItemProps, JobData } from './domain/JobListItem';

export { FileListItem } from './domain/FileListItem';
export type { FileListItemProps, FileData } from './domain/FileListItem';
```

- [ ] **Step 5: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add JobListItem, FileListItem, FileThumbnail"
```

---

### Task 12: CameraView, IdeaCard, MaterialCard

**Files:**
- Create: `frontend/react-ds/src/domain/CameraView/index.tsx`
- Create: `frontend/react-ds/src/domain/IdeaCard/index.tsx`
- Create: `frontend/react-ds/src/domain/MaterialCard/index.tsx`
- Modify: `frontend/react-ds/src/index.ts`

**Interfaces:**
- CSS classes used: `.camera-section`, `.camera-stream`, `.camera-placeholder`, `.camera-controls`, `.idea-card`, `.material-card`, `.material-card-header`, `.material-name`, `.material-info`, `.material-progress`, `.material-type-badge`, `.material-status-badge`, `.material-status-badge.low`, `.material-status-badge.out`

- [ ] **Step 1: Write `frontend/react-ds/src/domain/CameraView/index.tsx`**

```tsx
import React from 'react';

export type CameraStatus = 'active' | 'inactive' | 'error';

export interface CameraViewProps {
  streamUrl?: string;
  snapshotUrl?: string;
  status: CameraStatus;
  printerName?: string;
  onSnapshot?: () => void;
  className?: string;
}

export function CameraView({ streamUrl, snapshotUrl, status, printerName, onSnapshot, className }: CameraViewProps) {
  return (
    <div className={['camera-section', className ?? ''].filter(Boolean).join(' ')}>
      {status === 'active' && streamUrl ? (
        <div className="camera-preview-container">
          <img
            src={streamUrl}
            alt={printerName ? `${printerName} camera` : 'Camera feed'}
            className="camera-stream"
          />
        </div>
      ) : (
        <div className="camera-placeholder">
          <span className="placeholder-icon">📷</span>
          <span className="placeholder-text">
            {status === 'error' ? 'Camera unavailable' : 'No camera feed'}
          </span>
          {printerName && <small>{printerName}</small>}
        </div>
      )}
      {onSnapshot && status === 'active' && (
        <div className="camera-controls">
          <button className="btn btn-secondary btn-sm" onClick={onSnapshot}>
            📸 Snapshot
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/react-ds/src/domain/IdeaCard/index.tsx`**

```tsx
import React from 'react';
import { StatusBadge } from '../StatusBadge';
import type { IdeaStatus } from '../StatusBadge';

export interface IdeaData {
  id: string;
  title: string;
  platform?: string;
  tags?: string[];
  thumbnailUrl?: string;
  bookmarked?: boolean;
  status?: IdeaStatus;
}

export interface IdeaCardProps {
  idea: IdeaData;
  onClick?: (ideaId: string) => void;
  onBookmark?: (ideaId: string, bookmarked: boolean) => void;
  className?: string;
}

export function IdeaCard({ idea, onClick, onBookmark, className }: IdeaCardProps) {
  return (
    <div
      className={['idea-card', className ?? ''].filter(Boolean).join(' ')}
      onClick={() => onClick?.(idea.id)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {idea.thumbnailUrl && (
        <img
          src={idea.thumbnailUrl}
          alt={idea.title}
          style={{ width: '100%', aspectRatio: '4/3', objectFit: 'cover' }}
        />
      )}
      <div style={{ padding: '0.75rem' }}>
        <div style={{ fontWeight: 600, color: 'var(--gray-900)', marginBottom: '0.25rem' }}>{idea.title}</div>
        {idea.platform && (
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--gray-500)', marginBottom: '0.5rem' }}>
            {idea.platform}
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {idea.status && <StatusBadge status={idea.status} />}
          {idea.tags?.map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      </div>
      {onBookmark && (
        <button
          className="btn btn-secondary btn-sm"
          style={{ position: 'absolute', top: '0.5rem', right: '0.5rem' }}
          onClick={(e) => { e.stopPropagation(); onBookmark(idea.id, !idea.bookmarked); }}
          aria-label={idea.bookmarked ? 'Remove bookmark' : 'Bookmark'}
        >
          {idea.bookmarked ? '★' : '☆'}
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Write `frontend/react-ds/src/domain/MaterialCard/index.tsx`**

```tsx
import React from 'react';

export type MaterialStockStatus = 'ok' | 'low' | 'out';

export interface MaterialData {
  id: string;
  name: string;
  color: string;
  type: string;
  remainingGrams?: number;
  totalGrams?: number;
  stockStatus?: MaterialStockStatus;
}

export interface MaterialCardProps {
  material: MaterialData;
  onClick?: (materialId: string) => void;
  className?: string;
}

export function MaterialCard({ material, onClick, className }: MaterialCardProps) {
  const pct =
    material.remainingGrams !== undefined && material.totalGrams
      ? Math.round((material.remainingGrams / material.totalGrams) * 100)
      : undefined;

  return (
    <div
      className={[
        'material-card',
        material.stockStatus === 'low' ? 'low-stock' : '',
        material.stockStatus === 'out' ? 'out-of-stock' : '',
        className ?? '',
      ]
        .filter(Boolean)
        .join(' ')}
      onClick={() => onClick?.(material.id)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div className="material-card-header">
        <span
          className="material-color-indicator"
          style={{ backgroundColor: material.color, width: 16, height: 16, borderRadius: '50%', display: 'inline-block', marginRight: '0.5rem' }}
        />
        <span className="material-name">{material.name}</span>
        <span className="material-type-badge">{material.type}</span>
      </div>
      <div className="material-info">
        {material.remainingGrams !== undefined && (
          <div className="material-detail-item">
            <span className="material-detail-label">Remaining</span>
            <span className="material-detail-value">{material.remainingGrams}g</span>
          </div>
        )}
        {material.stockStatus && material.stockStatus !== 'ok' && (
          <span className={['material-status-badge', material.stockStatus].join(' ')}>
            {material.stockStatus === 'low' ? 'Low stock' : 'Out of stock'}
          </span>
        )}
      </div>
      {pct !== undefined && (
        <div className="material-progress">
          <div className="progress">
            <div className="progress-bar" style={{ width: `${pct}%` }} />
          </div>
          <span className="material-progress-label">{pct}%</span>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Append to `frontend/react-ds/src/index.ts`**

```ts
export { CameraView } from './domain/CameraView';
export type { CameraViewProps, CameraStatus } from './domain/CameraView';

export { IdeaCard } from './domain/IdeaCard';
export type { IdeaCardProps, IdeaData } from './domain/IdeaCard';

export { MaterialCard } from './domain/MaterialCard';
export type { MaterialCardProps, MaterialData, MaterialStockStatus } from './domain/MaterialCard';
```

- [ ] **Step 5: Verify typecheck + build**

```bash
cd frontend/react-ds && npm run typecheck && npm run build
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/react-ds/src/
git commit -m "feat: add CameraView, IdeaCard, MaterialCard"
```

---

### Task 13: Final build verification and design-sync handoff

**Files:**
- No new files — verifies the complete package is ready for `/design-sync`

**Interfaces:**
- Produces: clean `npm run build` + `npm run typecheck`; confirmed exports in `dist/index.js`

- [ ] **Step 1: Full typecheck**

```bash
cd frontend/react-ds && npm run typecheck
```

Expected: 0 errors, 0 warnings.

- [ ] **Step 2: Full build**

```bash
cd frontend/react-ds && npm run build
```

Expected:
```
Build complete: dist/index.js + dist/styles.css
```

- [ ] **Step 3: Verify export count**

```bash
grep -c "^export" frontend/react-ds/dist/index.js || node -e "
  import('./frontend/react-ds/dist/index.js').then(m => {
    console.log('Exports:', Object.keys(m).join(', '));
  });
"
```

Alternatively, count the named exports in `src/index.ts`:

```bash
grep "^export {" frontend/react-ds/src/index.ts | wc -l
```

Expected: 28 component exports (14 component + 14 type pairs).

- [ ] **Step 4: Verify `dist/styles.css` contains Printernizer tokens**

```bash
grep "primary-color\|gray-900\|spacing-4" frontend/react-ds/dist/styles.css | head -5
```

Expected: matches found — confirms the existing CSS was bundled correctly.

- [ ] **Step 5: Confirm `dist/` is not tracked by git**

```bash
git status frontend/react-ds/dist/
```

Expected: `dist/` not shown (gitignored).

- [ ] **Step 6: Final commit**

```bash
git add frontend/react-ds/src/index.ts
git commit -m "feat: complete Printernizer React design system — 28 components ready for design-sync"
```

- [ ] **Step 7: Run `/design-sync`**

The component library is now ready. From `frontend/react-ds/`, invoke:

```
/design-sync
```

The skill will detect `shape: package` (no Storybook), run its converter, generate `.d.ts`-derived usage guides per component, capture preview cards, and upload to a new claude.ai/design project named **"Printernizer Design System"**.

Note: the spec lists `globalName: PrinternizerDS` — this is NOT an esbuild option in ESM format. The design-sync skill's converter creates its own IIFE bundle with that global. When the skill asks for config, confirm `globalName: "PrinternizerDS"` in `.design-sync/config.json`.

---

## File map summary

```
frontend/react-ds/
├── package.json                         Task 1
├── tsconfig.json                        Task 1
├── build.mjs                            Task 1
├── .gitignore                           Task 1
├── styles/entry.css                     Task 1
└── src/
    ├── index.ts                         Tasks 1–12 (grows each task)
    ├── PrinternizerProvider/index.tsx   Task 2
    ├── core/
    │   ├── Button/index.tsx             Task 3
    │   ├── Card/index.tsx               Task 3
    │   ├── Badge/index.tsx              Task 4
    │   ├── Alert/index.tsx              Task 4
    │   ├── Toast/index.tsx              Task 4
    │   ├── Breadcrumb/index.tsx         Task 4
    │   ├── EmptyState/index.tsx         Task 4
    │   ├── StatCard/index.tsx           Task 4
    │   ├── FormGroup/index.tsx          Task 5
    │   ├── Input/index.tsx              Task 5
    │   ├── Select/index.tsx             Task 5
    │   ├── SearchBox/index.tsx          Task 5
    │   ├── Modal/index.tsx              Task 6
    │   ├── Table/index.tsx              Task 7
    │   └── Pagination/index.tsx         Task 7
    └── domain/
        ├── PageHeader/index.tsx         Task 8
        ├── NavSidebar/index.tsx         Task 8
        ├── PrinterStatusBadge/index.tsx Task 9
        ├── StatusBadge/index.tsx        Task 9
        ├── PrinterTypeIcon/index.tsx    Task 9
        ├── PrintProgressBar/index.tsx   Task 10
        ├── PrinterCard/index.tsx        Task 10
        ├── FileThumbnail/index.tsx      Task 11
        ├── JobListItem/index.tsx        Task 11
        ├── FileListItem/index.tsx       Task 11
        ├── CameraView/index.tsx         Task 12
        ├── IdeaCard/index.tsx           Task 12
        └── MaterialCard/index.tsx       Task 12
```
