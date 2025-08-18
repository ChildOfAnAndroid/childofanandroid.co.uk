// vite.config.js
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],

  server: {
    host: "0.0.0.0",
    port: 6969,
    proxy: {
      '/api': {
        target: 'https://childofanandroid.co.uk',
        changeOrigin: true, // This is essential for fixing CORS
      }
    }
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    }
  }
})