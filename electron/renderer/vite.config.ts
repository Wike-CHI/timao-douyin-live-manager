import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { fileURLToPath } from 'url';

const rootDir = fileURLToPath(new URL('.', import.meta.url));
// 🔧 CSP 策略 - 只允许本地连接（硬编码端口 11111）
const devCsp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https:",
  "connect-src 'self' ws://127.0.0.1:* ws://localhost:* http://127.0.0.1:* http://localhost:* http://127.0.0.1:11111 https:",
  "font-src 'self' data:",
];

export default defineConfig({
  root: resolve(rootDir),
  base: './',
  server: {
    host: '127.0.0.1',
    port: 10066, // 🔧 硬编码前端端口 10065（演示测试）
    strictPort: false, // 强制使用指定端口，不自动尝试其他端口
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
