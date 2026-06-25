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
