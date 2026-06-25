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
