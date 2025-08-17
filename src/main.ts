import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { router } from './router'

// --- cab admin helpers ---
const cab: any = {};

// set token
cab.bo = (t: string) => localStorage.setItem('bbyAdminToken', t || '');

// delete by URL
cab.no = async function (url: string) {
  const filename = (url || '').split('/').pop();
  if (!filename) throw new Error('Bad URL');

  let tok = localStorage.getItem('bbyAdminToken') || '';
  if (!tok) {
    tok = prompt('Enter admin delete token') || '';
    localStorage.setItem('bbyAdminToken', tok);
  }

  const res = await fetch(`/api/gallery/${filename}`, {
    method: 'DELETE',
    headers: { 'X-Admin-Token': tok },
  });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
  return await res.json();
};

// expose globally
(window as any).cab = cab;

// --- vue app ---
const app = createApp(App);
app.use(router);
app.mount('#app');