import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { api } from '../src/api.ts';
import { devApiTarget } from '../dev-api-target.ts';

const response = () => new Response(JSON.stringify({ ok: true }), {
  headers: { 'Content-Type': 'application/json' },
});

test('development defaults to the local backend', () => {
  assert.equal(devApiTarget({}), 'http://127.0.0.1:8420');
  assert.equal(devApiTarget({ BBY_DEV_API_TARGET: 'http://localhost:8420' }), 'http://localhost:8420');
});

test('remote development requires a separate explicit opt-in', () => {
  assert.throws(() => devApiTarget({ BBY_DEV_API_TARGET: 'https://site.example' }));
  assert.equal(devApiTarget({ BBY_DEV_API_TARGET: 'https://site.example',
    BBY_DEV_ALLOW_REMOTE: '1' }), 'https://site.example');
});

test('proxy target refuses credentials, paths, and non-HTTP schemes', () => {
  for (const target of ['https://user:password@site.example', 'http://localhost:8420/api',
                        'file:///tmp/backend', 'http://localhost:8420?x=1']) {
    assert.throws(() => devApiTarget({ BBY_DEV_API_TARGET: target, BBY_DEV_ALLOW_REMOTE: '1' }));
  }
});

test('read and write API requests remain on the current origin', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options }); return response();
  });
  await api.getState();
  await api.postSay({ text: 'test' });
  await api.postStateChange({ jumping: true });
  assert.deepEqual(calls.map(call => call.url), ['/api/state', '/api/say', '/api/state']);
  assert.equal(calls[1].options.method, 'POST');
});

test('binary gallery upload retains its PNG content type and body', async (t) => {
  let call;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    call = { url, options }; return response();
  });
  const blob = new Blob(['test fixture'], { type: 'image/png' });
  await api.postSaveToGallery(blob, 'Charis', 'test');
  assert.equal(call.url, '/api/gallery/save');
  assert.equal(new Headers(call.options.headers).get('content-type'), 'image/png');
  assert.equal(call.options.body, blob);
});

test('snapshot completion stays within the same API origin', async (t) => {
  let url;
  t.mock.method(globalThis, 'fetch', async (value) => { url = value; return response(); });
  await api.postAttachPng('snapshot-test', { composite_png_b64: 'test' });
  assert.equal(url, '/api/snapshot_attach_png/snapshot-test');
});

test('admin helper takes an explicit per-call token, with no persistent storage', async () => {
  const source = await readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.match(source, /adminToken\?: string/);
  assert.match(source, /if \(!adminToken\?\.trim\(\)\)/);
  assert.match(source, /Authorization.*Bearer/);
  assert.doesNotMatch(source, /localStorage|sessionStorage|VITE_.*TOKEN/);
});

test('paint polling also follows the current origin, not production', async () => {
  const source = await readFile(new URL('../src/composables/bbyUse.ts', import.meta.url), 'utf8');
  assert.match(source, /new URL\('\/api\/paint_events', window\.location\.origin\)/);
  assert.doesNotMatch(source, /https:\/\/childofanandroid\.co\.uk\/api/);
});
