import React from 'react';

export type MaterialStockStatus = 'ok' | 'low' | 'out';

export interface MaterialData {
  id: string;
  name: string;
  color: string;
  type: string;
  remainingGrams?: number;
  totalGrams?: number;
  stockStatus?: MaterialStockStatus;
}

export interface MaterialCardProps {
  material: MaterialData;
  onClick?: (materialId: string) => void;
  className?: string;
}

export function MaterialCard({ material, onClick, className }: MaterialCardProps) {
  const pct =
    material.remainingGrams !== undefined && material.totalGrams
      ? Math.round((material.remainingGrams / material.totalGrams) * 100)
      : undefined;

  return (
    <div
      className={[
        'material-card',
        material.stockStatus === 'low' ? 'low-stock' : '',
        material.stockStatus === 'out' ? 'out-of-stock' : '',
        className ?? '',
      ]
        .filter(Boolean)
        .join(' ')}
      onClick={() => onClick?.(material.id)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div className="material-card-header">
        <span
          className="material-color-indicator"
          style={{ backgroundColor: material.color, width: 16, height: 16, borderRadius: '50%', display: 'inline-block', marginRight: '0.5rem' }}
        />
        <span className="material-name">{material.name}</span>
        <span className="material-type-badge">{material.type}</span>
      </div>
      <div className="material-info">
        <div className="material-details">
          {material.remainingGrams !== undefined && (
            <div className="material-detail-item">
              <span className="material-detail-label">Remaining</span>
              <span className="material-detail-value">{material.remainingGrams}g</span>
            </div>
          )}
          {material.stockStatus && material.stockStatus !== 'ok' && (
            <span className={['material-status-badge', material.stockStatus].join(' ')}>
              {material.stockStatus === 'low' ? 'Low stock' : 'Out of stock'}
            </span>
          )}
        </div>
      </div>
      {pct !== undefined && (
        <div className="material-progress">
          <div className="progress">
            <div className="progress-bar" style={{ width: `${pct}%` }} />
          </div>
          <span className="material-progress-label">{pct}%</span>
        </div>
      )}
    </div>
  );
}
