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
      '/baby.png': 'https://bbyapi.childofanandroid.co.uk',
      '/speech.txt': 'https://bbyapi.childofanandroid.co.uk',
      '/set': 'https://bbyapi.childofanandroid.co.uk',
      '/say': 'https://bbyapi.childofanandroid.co.uk',
      '/speak': 'https://bbyapi.childofanandroid.co.uk',
      '/colour': 'https://bbyapi.childofanandroid.co.uk',
    }
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    }
  }
})