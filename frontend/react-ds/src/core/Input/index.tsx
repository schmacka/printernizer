import React from 'react';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  label?: string;
  error?: string;
  hint?: string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
}

export function Input({ label, error, hint, prefix, suffix, className, required, ...rest }: InputProps) {
  return (
    <div className="form-group">
      {label && (
        <label>
          {label}
          {required && <span style={{ color: 'var(--error-color)' }}> *</span>}
        </label>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {prefix && <span>{prefix}</span>}
        <input
          className={['form-control', error ? 'error' : '', className ?? ''].filter(Boolean).join(' ')}
          required={required}
          {...rest}
        />
        {suffix && <span>{suffix}</span>}
      </div>
      {hint && !error && <small style={{ color: 'var(--gray-500)', display: 'block', marginTop: '0.25rem' }}>{hint}</small>}
      {error && <small style={{ color: 'var(--error-color)', display: 'block', marginTop: '0.25rem' }}>{error}</small>}
    </div>
  );
}
