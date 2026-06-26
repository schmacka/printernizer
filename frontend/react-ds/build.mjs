import * as esbuild from 'esbuild';
import { mkdirSync } from 'fs';

mkdirSync('dist', { recursive: true });

// JS bundle
await esbuild.build({
  entryPoints: ['src/index.ts'],
  bundle: true,
  format: 'esm',
  outfile: 'dist/index.js',
  external: ['react', 'react-dom', 'react/jsx-runtime'],
  minify: false,
  sourcemap: false,
  target: ['es2020'],
});

// CSS bundle
await esbuild.build({
  entryPoints: ['styles/entry.css'],
  bundle: true,
  outfile: 'dist/styles.css',
  loader: { '.css': 'css' },
  minify: false,
});

console.log('Build complete: dist/index.js + dist/styles.css');
