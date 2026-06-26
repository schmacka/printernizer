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
