import React from 'react';

export interface SearchBoxProps {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  className?: string;
}

export function SearchBox({ value, onChange, onClear, placeholder = 'Search…', className }: SearchBoxProps) {
  return (
    <div className={['search-controls', className ?? ''].filter(Boolean).join(' ')}>
      <div className="search-input-wrapper">
        <span className="search-icon">🔍</span>
        <input
          type="search"
          className="search-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
        {value && (
          <button className="search-clear-btn" onClick={() => { onChange(''); onClear?.(); }} aria-label="Clear search">
            ×
          </button>
        )}
      </div>
    </div>
  );
}
