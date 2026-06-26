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
