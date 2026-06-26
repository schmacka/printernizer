import React from 'react';
import { StatCard } from '@printernizer/design-system';

export const PrintJobsStat = () => (
  <div style={{ padding: '1rem', display: 'grid', gridTemplateColumns: 'repeat(3, 180px)', gap: '1rem' }}>
    <StatCard label="Print Jobs Today" value="24" delta="+3 from yesterday" icon="🖨" />
    <StatCard label="Filament Used" value="847g" delta="-12% vs last week" icon="🧵" />
    <StatCard label="Active Printers" value="3 / 5" icon="✅" />
  </div>
);

export const Minimal = () => (
  <div style={{ padding: '1rem' }}>
    <StatCard label="Total Files" value="1,247" />
  </div>
);
