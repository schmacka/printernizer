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
