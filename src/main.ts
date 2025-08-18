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
    tok = prompt('enter admin delete token') || '';
    localStorage.setItem('bbyAdminToken', tok);
  }

  const res = await fetch(`/api/gallery/${filename}`, {
    method: 'DELETE',
    headers: { 'X-Admin-Token': tok },
  });
  if (!res.ok) throw new Error(`delete failed: ${res.status}`);
  return await res.json();
};

// rename by URL (finds the item's id, then PATCHes)
cab.name = async function (url: string, newTitle: string, newLabel?: string) {
  const filename = (url || '').split('/').pop();
  if (!filename) throw new Error('bad URL');

  // 1) fetch latest gallery to find the id for that filename
  const list = await (await fetch('/api/gallery')).json();

  const item = list.find((m: any) =>
    (m.file && m.file === filename) ||
    (m.url && typeof m.url === 'string' && m.url.endsWith('/' + filename))
  );
  if (!item) throw new Error('not found in gallery');

  // 2) call update_meta with the id
  const res = await fetch('/api/gallery/update_meta', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: item.id,
      title: newTitle,
      ...(newLabel ? { label: newLabel } : {})
    })
  });

  const j = await res.json();
  if (!res.ok || !j.ok) throw new Error(`update failed: ${j.error || res.status}`);
  return j;
};

// expose globally
(window as any).cab = cab;

// --- vue app ---
const app = createApp(App);
app.use(router);
app.mount('#app');