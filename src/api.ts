// src/api.ts

const API_BASE = 'https://bbyapi.childofanandroid.co.uk/api';

/**
 * A centralized fetch wrapper for the bbyAPI.
 * Handles base URL, JSON headers, error handling, and response parsing.
 * @param endpoint The API endpoint to call (e.g., '/state').
 * @param options Standard RequestInit options.
 * @returns The parsed JSON response, or nothing if the response has no body.
 */
async function request(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    // Defaults to JSON, but can be overridden for file uploads.
    'Content-Type': 'application/json',
    ...options.headers,
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

export const api = {
  getState: () => request('/state'),
  getChatHistory: () => request('/chat_history'),
  getPaintCanvas: () => request('/get_paint_canvas'),
  getBbyBook: () => request('/bbybook'),
  getGallery: () => request('/gallery'),
  getActivity: () => request('/activity'),

  postSay: (body: { text: string; author: string; colour: object }) => request('/say', { method: 'POST', body: JSON.stringify(body) }),
  postPixelUpdate: (body: { pixels: object[] }) => request('/paint_pixel', { method: 'POST', body: JSON.stringify(body) }),
  postStateChange: (body: object) => request('/set', { method: 'POST', body: JSON.stringify(body) }),
  postSnapshot: (body: { label: string; composite_png_b64: string }) => request('/snapshot', { method: 'POST', body: JSON.stringify(body) }),
  postAttachPng: (snap_id: string, body: { composite_png_b64: string }) => request(`/snapshot_attach_png/${snap_id}`, { method: 'POST', body: JSON.stringify(body) }),

  // Gallery save has a different body/header type
  postSaveToGallery: (blob: Blob, authorName: string, label: string) => {
    return request('/gallery/save', {
      method: 'POST',
      headers: {
        'content-type': 'image/png', // Override default header
        'x-author': authorName,
        'x-label': label,
      },
      body: blob,
    });
  },
};