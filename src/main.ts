import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { router } from './router'
import { api } from './api'

// Existing console helper, now authenticated by the server. The token is passed
// for this call only, never bundled, persisted, or attached to public requests.
const cab = {
  async name(url: string, newTitle: string, newLabel?: string, adminToken?: string) {
    if (!adminToken?.trim()) throw new Error('A server administrator token is required.');
    const filename = new URL(url, window.location.origin).pathname.split('/').pop();
    if (!filename) throw new Error('bad URL');
    const list = await api.getGallery();
    const item = list.find((m: { id: string; file?: string; url?: string }) =>
      m.file === filename || (typeof m.url === 'string' && m.url.endsWith('/' + filename))
    );
    if (!item) throw new Error('not found in gallery');
    return api.updateGalleryMetadata(item.id, newTitle, newLabel, adminToken);
  },
};
(window as unknown as { cab: typeof cab }).cab = cab;

const app = createApp(App);
app.use(router);
app.mount('#app');
