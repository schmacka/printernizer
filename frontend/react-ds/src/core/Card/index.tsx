import React from 'react';

export interface CardProps {
  header?: React.ReactNode;
  icon?: React.ReactNode;
  children: React.ReactNode;
  hoverable?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function Card({ header, icon, children, hoverable = false, className, style }: CardProps) {
  return (
    <div className={['card', hoverable ? 'hoverable' : '', className ?? ''].filter(Boolean).join(' ')} style={style}>
      {(header || icon) && (
        <div className="card-header">
          {icon && <span className="card-icon">{icon}</span>}
          {header && <h3>{header}</h3>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
}
