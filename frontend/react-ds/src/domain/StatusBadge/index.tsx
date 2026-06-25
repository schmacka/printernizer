import React from 'react';

export type IdeaStatus = 'idea' | 'planned' | 'printing' | 'completed' | 'archived';

export interface StatusBadgeProps {
  status: IdeaStatus;
  label?: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const displayLabel = label ?? status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span className={['status-badge', `status-${status}`, className ?? ''].filter(Boolean).join(' ')}>
      {displayLabel}
    </span>
  );
}
