import React from 'react';
import { StatusBadge } from '../StatusBadge';
import type { IdeaStatus } from '../StatusBadge';

export interface IdeaData {
  id: string;
  title: string;
  platform?: string;
  tags?: string[];
  thumbnailUrl?: string;
  bookmarked?: boolean;
  status?: IdeaStatus;
}

export interface IdeaCardProps {
  idea: IdeaData;
  onClick?: (ideaId: string) => void;
  onBookmark?: (ideaId: string, bookmarked: boolean) => void;
  className?: string;
}

export function IdeaCard({ idea, onClick, onBookmark, className }: IdeaCardProps) {
  return (
    <div
      className={['idea-card', className ?? ''].filter(Boolean).join(' ')}
      onClick={() => onClick?.(idea.id)}
      style={{ cursor: onClick ? 'pointer' : 'default', position: 'relative' }}
    >
      {idea.thumbnailUrl && (
        <img
          src={idea.thumbnailUrl}
          alt={idea.title}
          style={{ width: '100%', aspectRatio: '4/3', objectFit: 'cover' }}
        />
      )}
      <div style={{ padding: '0.75rem' }}>
        <div style={{ fontWeight: 600, color: 'var(--gray-900)', marginBottom: '0.25rem' }}>{idea.title}</div>
        {idea.platform && (
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--gray-500)', marginBottom: '0.5rem' }}>
            {idea.platform}
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {idea.status && <StatusBadge status={idea.status} />}
          {idea.tags?.map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      </div>
      {onBookmark && (
        <button
          className="btn btn-secondary btn-sm"
          style={{ position: 'absolute', top: '0.5rem', right: '0.5rem' }}
          onClick={(e) => { e.stopPropagation(); onBookmark(idea.id, !idea.bookmarked); }}
          aria-label={idea.bookmarked ? 'Remove bookmark' : 'Bookmark'}
        >
          {idea.bookmarked ? '★' : '☆'}
        </button>
      )}
    </div>
  );
}
