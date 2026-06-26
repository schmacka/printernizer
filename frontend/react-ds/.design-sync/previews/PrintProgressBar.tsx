import React from 'react';
import { PrintProgressBar } from '@printernizer/design-system';

export const Printing = () => (
  <div style={{ padding: '1rem', width: 400, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
    <PrintProgressBar progress={67} status="printing" timeRemaining="1h 12m remaining" />
    <PrintProgressBar progress={100} status="completed" />
    <PrintProgressBar progress={23} status="warning" timeRemaining="3h 45m remaining" />
  </div>
);

export const Error = () => (
  <div style={{ padding: '1rem', width: 400 }}>
    <PrintProgressBar progress={45} status="error" />
  </div>
);
