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
