import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { fileURLToPath } from 'url';

const rootDir = fileURLToPath(new URL('.', import.meta.url));
const devCsp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https:",
  "connect-src 'self' ws://127.0.0.1:* ws://localhost:* http://127.0.0.1:* http://localhost:* https:",
  "font-src 'self' data:",
];

export default defineConfig({
  root: resolve(rootDir),
  base: './',
  server: {
    host: '127.0.0.1',
    port: 30013,
    headers: {
      'Content-Security-Policy': devCsp.join('; '),
    },
  },
  plugins: [react()],
  build: {
    outDir: resolve(rootDir, 'dist'),
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': resolve(rootDir, 'src'),
    },
  },
});
