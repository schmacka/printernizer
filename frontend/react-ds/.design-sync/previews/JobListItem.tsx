import React from 'react';
import { JobListItem } from '@printernizer/design-system';

export const Printing = () => (
  <div style={{ padding: '1rem', width: 500 }}>
    <JobListItem
      job={{
        id: 'j1',
        name: 'Dragon_v3_final.3mf',
        printer: 'Bambu A1 Mini',
        progress: 67,
        status: 'printing',
        duration: '2h 34m',
        startedAt: '2026-06-26T08:00:00Z',
      }}
    />
  </div>
);

export const Completed = () => (
  <div style={{ padding: '1rem', width: 500, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
    <JobListItem
      job={{ id: 'j2', name: 'Cable_Clip.stl', printer: 'Prusa Core One', progress: 100, status: 'completed', duration: '45m', startedAt: '2026-06-26T06:00:00Z' }}
    />
    <JobListItem
      job={{ id: 'j3', name: 'Phone_Stand.3mf', printer: 'Bambu A1', progress: 0, status: 'error', duration: '—', startedAt: '2026-06-26T07:30:00Z' }}
    />
  </div>
);
