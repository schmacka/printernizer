import React from 'react';
import { Input } from '@printernizer/design-system';

export const TextInput = () => (
  <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem', width: 320 }}>
    <Input label="Email address" type="email" placeholder="you@example.com" />
    <Input label="Password" type="password" placeholder="Enter password" />
    <Input label="Search" type="text" placeholder="Search printers..." prefix="🔍" />
  </div>
);

export const WithError = () => (
  <div style={{ padding: '1rem', width: 320 }}>
    <Input label="File name" value="broken-file" error="File name contains invalid characters" hint="Use letters, numbers, and hyphens only" />
  </div>
);

export const Required = () => (
  <div style={{ padding: '1rem', width: 320 }}>
    <Input label="Printer name" required placeholder="e.g. Bambu A1 Mini" hint="This will appear in job reports" />
  </div>
);
