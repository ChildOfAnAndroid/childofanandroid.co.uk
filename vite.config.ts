import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
import { devApiTarget } from './dev-api-target';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'BBY_');
  return {
    plugins: [vue()],
    server: {
      host: '127.0.0.1',
      port: 6969,
      strictPort: true,
      proxy: {
        '/api': {
          target: devApiTarget(env),
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
  };
});
