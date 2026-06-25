import React from 'react';
import { FileThumbnail } from '../FileThumbnail';
import type { FileType } from '../FileThumbnail';

export interface FileData {
  id: string;
  name: string;
  size: string;
  type: FileType;
  thumbnailUrl?: string;
  uploadedAt?: string;
}

export interface FileListItemProps {
  file: FileData;
  onClick?: (fileId: string) => void;
  actions?: React.ReactNode;
  className?: string;
}

export function FileListItem({ file, onClick, actions, className }: FileListItemProps) {
  return (
    <div
      className={['file-item', className ?? ''].filter(Boolean).join(' ')}
      onClick={() => onClick?.(file.id)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <FileThumbnail src={file.thumbnailUrl} fileType={file.type} size="sm" alt={file.name} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, color: 'var(--gray-900)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {file.name}
        </div>
        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--gray-500)' }}>
          {file.size} {file.uploadedAt && `· ${file.uploadedAt}`}
        </div>
      </div>
      {actions && <div onClick={(e) => e.stopPropagation()}>{actions}</div>}
    </div>
  );
}
