import React from 'react';
import { IdeaCard } from '@printernizer/design-system';

export const Default = () => (
  <div style={{ padding: '1rem', width: 240 }}>
    <IdeaCard
      idea={{
        id: '1',
        title: 'Articulated Dragon',
        platform: 'Printables',
        tags: ['dragon', 'articulated', 'toy'],
        status: 'idea',
        bookmarked: true,
      }}
    />
  </div>
);

export const Planned = () => (
  <div style={{ padding: '1rem', display: 'flex', gap: '1rem' }}>
    <IdeaCard
      idea={{ id: '2', title: 'Cable Organizer', platform: 'Thingiverse', status: 'planned', tags: ['utility'] }}
    />
    <IdeaCard
      idea={{ id: '3', title: 'Plant Pot', platform: 'Printables', status: 'archived', tags: ['home'] }}
    />
  </div>
);
