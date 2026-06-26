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
