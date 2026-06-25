import React from 'react';

export interface FormGroupProps {
  label?: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormGroup({ label, required, error, hint, children, className }: FormGroupProps) {
  return (
    <div className={['form-group', className ?? ''].filter(Boolean).join(' ')}>
      {label && (
        <label>
          {label}
          {required && <span style={{ color: 'var(--error-color)' }}> *</span>}
        </label>
      )}
      {children}
      {hint && !error && <small style={{ color: 'var(--gray-500)', display: 'block', marginTop: '0.25rem' }}>{hint}</small>}
      {error && <small style={{ color: 'var(--error-color)', display: 'block', marginTop: '0.25rem' }}>{error}</small>}
    </div>
  );
}
