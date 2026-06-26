import React from 'react';

export interface StatCardProps {
  label: string;
  value: React.ReactNode;
  delta?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({ label, value, delta, icon, className }: StatCardProps) {
  return (
    <div className={['stat-card', className ?? ''].filter(Boolean).join(' ')}>
      {icon && <div className="stat-icon">{icon}</div>}
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {delta && <div className="stat-delta">{delta}</div>}
    </div>
  );
}
