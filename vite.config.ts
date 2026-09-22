import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig(({ mode }) => {
  // Server-side configuration only. No secrets or backend tokens use VITE_* names.
  const env = loadEnv(mode, process.cwd(), 'BBY_');
  const target = new URL(env.BBY_DEV_API_TARGET || 'http://127.0.0.1:8420');
  if (!['http:', 'https:'].includes(target.protocol) || target.username || target.password || target.pathname !== '/' || target.search || target.hash) {
    throw new Error('BBY_DEV_API_TARGET must be an HTTP(S) origin without credentials.');
  }
  const local = ['127.0.0.1', 'localhost', '[::1]'].includes(target.hostname);
  if (!local && env.BBY_ALLOW_REMOTE_DEV_API !== '1') {
    throw new Error('Remote development API requires explicit BBY_ALLOW_REMOTE_DEV_API=1.');
  }
  return {
    plugins: [vue()],
    server: {
      host: '127.0.0.1',
      port: 6969,
      strictPort: true,
      proxy: { '/api': { target: target.origin, changeOrigin: true } },
    },
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  };
});
