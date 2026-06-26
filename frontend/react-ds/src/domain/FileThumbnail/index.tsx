import React from 'react';

export type FileType = 'stl' | '3mf' | 'gcode' | 'image';
export type ThumbnailSize = 'sm' | 'md' | 'lg';

export interface FileThumbnailProps {
  src?: string;
  fileType: FileType;
  animated?: boolean;
  size?: ThumbnailSize;
  alt?: string;
  className?: string;
}

const sizePx: Record<ThumbnailSize, number> = { sm: 48, md: 80, lg: 128 };
const typeEmoji: Record<FileType, string> = { stl: '🧊', '3mf': '🖨', gcode: '📄', image: '🖼' };

export function FileThumbnail({ src, fileType, animated, size = 'md', alt, className }: FileThumbnailProps) {
  const px = sizePx[size];
  return (
    <div
      className={['file-thumbnail', animated ? 'supports-animation' : '', className ?? ''].filter(Boolean).join(' ')}
      style={{ width: px, height: px, flexShrink: 0 }}
    >
      {src ? (
        <img src={src} alt={alt ?? fileType} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'var(--radius-md)' }} />
      ) : (
        <span style={{ fontSize: px * 0.5, display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          {typeEmoji[fileType]}
        </span>
      )}
    </div>
  );
}
