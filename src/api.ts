// src/api.ts

const API_BASE = 'https://childofanandroid.co.uk/api';

/**
 * A centralized fetch wrapper for the bbyAPI.
 * Handles base URL, JSON headers, error handling, and response parsing.
 * @param endpoint The API endpoint to call (e.g., '/state').
 * @param options Standard RequestInit options.
 * @returns The parsed JSON response, or nothing if the response has no body.
 */
async function request(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  let hasContentType = false;
  let headersInit: Record<string, string> = {};

  if (options.headers) {
    if (options.headers instanceof Headers) {
      hasContentType = options.headers.has('content-type') || options.headers.has('Content-Type');
      options.headers.forEach((value, key) => {
        headersInit[key] = value;
      });
    } else if (Array.isArray(options.headers)) {
      hasContentType = options.headers.some(([key]) => key.toLowerCase() === 'content-type');
      for (const [key, value] of options.headers) {
        headersInit[key] = value;
      }
    } else {
      hasContentType = Object.keys(options.headers).some(key => key.toLowerCase() === 'content-type');
      headersInit = options.headers as Record<string, string>;
    }
  }

  const headers = {
    ...(hasContentType ? {} : { 'Content-Type': 'application/json' }),
    ...headersInit,
  };

  try {
    const response = await fetch(url, { ...options, headers, cache: 'no-store' });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ error: 'Request failed with no JSON body' }));
      throw new Error(`API Error on ${endpoint}: ${errorBody.error || response.statusText}`);
    }

    // Handle successful responses that might not have a JSON body (e.g., 204 No Content).
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return; // Return undefined for non-JSON success responses.

  } catch (error) {
    console.error(`API request to ${endpoint} failed:`, error);
    throw error; // Re-throw so the calling function can handle it if needed.
  }
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
  speak?: boolean;        // <— NEW
}

export const api = {
  getState: () => request('/state'),
  getChatHistory: () => request('/chat_history'),
  getPaintCanvas: () => request('/get_paint_canvas'),
  getBbyBook: () => request('/bbybook'),
  getGallery: () => request('/gallery'),
  getActivity: () => request('/activity'),

  postSay: (body: PostSayBody) => request('/say', { method: 'POST', body: JSON.stringify(body) }),
  postPixelUpdate: (body: { pixels: object[] }) => request('/paint_pixel', { method: 'POST', body: JSON.stringify(body) }),
  postStateChange: (body: object) => request('/state', { method: 'POST', body: JSON.stringify(body) }),
  // --- Snapshot & Gallery Save Pipeline ---
  // The frontend customization pipeline saves in two stages:
  // 1. postSnapshot: Sends the state and composite base64 PNG. The server writes the snapshot to storage.
  // 2. postSaveToGallery: Sends the raw canvas drawing as a binary PNG blob to the public gallery.
  // Uses a custom 'content-type' header to override the request helper's default JSON header.
  postSnapshot: (body: { label: string; composite_png_b64: string }) => request('/snapshot', { method: 'POST', body: JSON.stringify(body) }),
  postAttachPng: (snap_id: string, body: { composite_png_b64: string }) => request(`/snapshot_attach_png/${snap_id}`, { method: 'POST', body: JSON.stringify(body) }),

  postSaveToGallery: (blob: Blob, authorName: string, label: string) => {
    return request('/gallery/save', {
      method: 'POST',
      headers: {
        'content-type': 'image/png', // Lowercase content-type to override default JSON Content-Type
        'x-author': encodeURIComponent(authorName),
        'x-label': encodeURIComponent(label),
      },
      body: blob,
    });
  },
};
