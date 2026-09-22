// All browser requests stay on the page's origin. Vite proxies /api locally in dev.
const API_BASE = '/api';

async function request(endpoint: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  if (options.body !== undefined && typeof options.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers, cache: 'no-store' });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(`API Error on ${endpoint}: ${body?.error || body?.message || response.statusText || response.status}`);
  }
  if (response.status === 204) return;
  if (response.headers.get('content-type')?.includes('application/json')) return response.json();
}

export interface PostSayBody {
  text: string;
  author?: string;
  colour?: object;
  platform?: 'web' | 'discord' | 'twitch';
  user_id?: string;
  handle?: string;
  display_name?: string;
  is_command?: boolean;
  speak?: boolean;
}

export const api = {
  getState: () => request('/state'),
  getChatHistory: () => request('/chat_history'),
  getPaintCanvas: () => request('/get_paint_canvas'),
  getPaintEvents: (since?: string | null) => request(`/paint_events${since ? `?${new URLSearchParams({ since })}` : ''}`),
  getBbyBook: () => request('/bbybook'),
  getGallery: () => request('/gallery'),
  getActivity: () => request('/activity'),
  postSay: (body: PostSayBody) => request('/say', { method: 'POST', body: JSON.stringify(body) }),
  postPixelUpdate: (body: { pixels: object[] }) => request('/paint_pixel', { method: 'POST', body: JSON.stringify(body) }),
  postStateChange: (body: object) => request('/state', { method: 'POST', body: JSON.stringify(body) }),
  postSnapshot: (body: { label: string; composite_png_b64: string }) => request('/snapshot', { method: 'POST', body: JSON.stringify(body) }),
  postAttachPng: (snap_id: string, body: { composite_png_b64: string }) => request(`/snapshot_attach_png/${encodeURIComponent(snap_id)}`, { method: 'POST', body: JSON.stringify(body) }),
  updateGalleryMetadata: (id: string, title: string, label: string | undefined, adminToken: string) => {
    if (!adminToken?.trim()) throw new Error('A server administrator token is required.');
    return request('/gallery/update_meta', {
      method: 'POST',
      headers: { Authorization: `Bearer ${adminToken.trim()}` },
      body: JSON.stringify({ id, title, ...(label ? { label } : {}) }),
    });
  },
  postSaveToGallery: (blob: Blob, authorName: string, label: string) => request('/gallery/save', {
    method: 'POST',
    headers: {
      'Content-Type': 'image/png',
      'x-author': encodeURIComponent(authorName),
      'x-label': encodeURIComponent(label),
    },
    body: blob,
  }),
};
