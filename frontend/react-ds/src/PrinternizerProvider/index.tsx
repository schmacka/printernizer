import React from 'react';

export type PrinternizerTheme =
  | 'default'
  | 'refined'
  | 'industrial'
  | 'soft'
  | 'retro'
  | 'brutalist';

export interface PrinternizerProviderProps {
  theme?: PrinternizerTheme;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export function PrinternizerProvider({
  theme = 'default',
  children,
  className,
  style,
}: PrinternizerProviderProps) {
  return (
    <div
      data-theme={theme === 'default' ? undefined : theme}
      className={className}
      style={{ minHeight: '100%', ...style }}
    >
      {children}
    </div>
  );
}
