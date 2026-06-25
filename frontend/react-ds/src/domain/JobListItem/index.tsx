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
