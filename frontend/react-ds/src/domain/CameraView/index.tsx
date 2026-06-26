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
