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
    port: 10050, // 默认前端开发端口，可通过环境变量覆盖
    strictPort: false, // 如果端口被占用，自动尝试下一个可用端口
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
