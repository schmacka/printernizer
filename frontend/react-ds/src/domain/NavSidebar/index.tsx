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
