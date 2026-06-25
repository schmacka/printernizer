import React from 'react';

export interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
  className?: string;
}

export function Pagination({ page, totalPages, onChange, className }: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className={['pagination', className ?? ''].filter(Boolean).join(' ')}>
      <button
        className="pagination-btn"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        ‹
      </button>
      {pages.map((p) => (
        <button
          key={p}
          className={['pagination-btn', p === page ? 'active' : ''].filter(Boolean).join(' ')}
          onClick={() => onChange(p)}
        >
          {p}
        </button>
      ))}
      <button
        className="pagination-btn"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
      >
        ›
      </button>
      <span className="pagination-info">
        Page {page} of {totalPages}
      </span>
    </div>
  );
}
