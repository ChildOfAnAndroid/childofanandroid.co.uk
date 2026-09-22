import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const { api } = await import(process.env.BBY_API_TEST_MODULE);
const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; });
function callsWith(response = () => new Response('{}', { headers: { 'Content-Type': 'application/json' } })) {
  const calls = [];
  globalThis.fetch = async (...args) => { calls.push(args); return response(); };
  return calls;
}

test('reads remain same-origin without unnecessary JSON headers', async () => {
  const calls = callsWith();
  await api.getState();
  assert.equal(calls[0][0], '/api/state');
  assert.equal(calls[0][1].headers.has('Content-Type'), false);
});
test('paint event continuation is encoded on the same API', async () => {
  const calls = callsWith();
  await api.getPaintEvents('a & b');
  assert.equal(calls[0][0], '/api/paint_events?since=a+%26+b');
});
test('chat posts once and preserves speak=false', async () => {
  const calls = callsWith();
  await api.postSay({ text: 'hello', speak: false });
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], '/api/say');
  assert.equal(JSON.parse(calls[0][1].body).speak, false);
  assert.equal(calls[0][1].headers.get('Content-Type'), 'application/json');
});
test('binary gallery uploads keep PNG content type', async () => {
  const calls = callsWith();
  const image = new Blob(['test'], { type: 'image/png' });
  await api.postSaveToGallery(image, 'name ☃', 'picture');
  assert.equal(calls[0][1].body, image);
  assert.equal(calls[0][1].headers.get('Content-Type'), 'image/png');
  assert.equal(calls[0][1].headers.get('x-author'), encodeURIComponent('name ☃'));
});
test('missing admin credential stops before fetch', () => {
  const calls = callsWith();
  assert.throws(() => api.updateGalleryMetadata('id', 'title', undefined, ''), /token/);
  assert.equal(calls.length, 0);
});
test('admin credential goes only to the intended request, never public reads', async () => {
  const calls = callsWith();
  await api.updateGalleryMetadata('id', 'title', undefined, 'fixture-token');
  await api.getGallery();
  assert.equal(calls[0][0], '/api/gallery/update_meta');
  assert.equal(calls[0][1].headers.get('Authorization'), 'Bearer fixture-token');
  assert.equal(calls[1][1].headers.has('Authorization'), false);
});
test('HTTP failure is surfaced without retrying a write', async () => {
  const calls = callsWith(() => new Response('unavailable', { status: 503 }));
  await assert.rejects(api.postSay({ text: 'hello' }), /503/);
  assert.equal(calls.length, 1);
});
test('all paint polling uses the central relative API', () => {
  const source = readFileSync('src/composables/bbyUse.ts', 'utf8');
  assert.equal(source.includes('childofanandroid.co.uk/api'), false);
  assert.match(source, /api\.getPaintEvents\(lastPaintEventId\.value\)/);
});
test('development proxy has a local default and an explicit remote opt-in', () => {
  const source = readFileSync('vite.config.ts', 'utf8');
  assert.match(source, /http:\/\/127\.0\.0\.1:8420/);
  assert.match(source, /BBY_ALLOW_REMOTE_DEV_API !== '1'/);
  assert.equal(source.includes('https://childofanandroid.co.uk'), false);
});
