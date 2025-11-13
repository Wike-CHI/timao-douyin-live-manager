import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  const port = Number(env.VITE_ADMIN_PORT || env.PORT || '10065');
  const apiTarget = env.VITE_FASTAPI_URL || 'http://127.0.0.1:10090';
  const base = mode === 'production' ? '/admin/' : '/';

  return {
    plugins: [react()],
    base, // 支持子路径部署
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
    },
  };
});
