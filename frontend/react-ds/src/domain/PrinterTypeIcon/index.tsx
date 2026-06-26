import React from 'react';

export type PrinterType = 'bambu' | 'prusa';
export type IconSize = 'sm' | 'md' | 'lg';

export interface PrinterTypeIconProps {
  type: PrinterType;
  size?: IconSize;
  className?: string;
}

const sizePx: Record<IconSize, number> = { sm: 16, md: 24, lg: 32 };

export function PrinterTypeIcon({ type, size = 'md', className }: PrinterTypeIconProps) {
  const px = sizePx[size];

  if (type === 'bambu') {
    return (
      <svg
        width={px}
        height={px}
        viewBox="0 0 24 24"
        fill="none"
        className={className}
        aria-label="Bambu Lab"
      >
        <rect width="24" height="24" rx="4" fill="#F97316" />
        <text x="12" y="17" textAnchor="middle" fill="white" fontSize="13" fontWeight="bold">B</text>
      </svg>
    );
  }

  return (
    <svg
      width={px}
      height={px}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-label="Prusa"
    >
      <rect width="24" height="24" rx="4" fill="#DC2626" />
      <text x="12" y="17" textAnchor="middle" fill="white" fontSize="13" fontWeight="bold">P</text>
    </svg>
  );
}
