// src/composables/bbyUse.ts

import { reactive, readonly, ref, watch } from 'vue';
import _ from 'lodash';
import { api } from '@/api'; // <-- Import the new API module

interface Bubble {
  id: string;
  text: string;
  author?: string;
  ghostX?: string;
  ghostY?: string;
  ghostR?: string;
  startX?: string;
  startY?: string;
  width?: string;
  height?: string;
  duration?: string;
  easing?: string;
  delay?: string;
  ghostOpacity1?: number;
  ghostOpacity2?: number;
  ghostBlur?: number;
  bgColour?: string;
  borderColour?: string;
}

interface UserColour { r: number; g: number; b: number; }


const bbyState = reactive({
  eyes: 5, mouth: 1, cheeks_on: false, tears_on: false, jumping: false,
  stretch_left: false, stretch_right: false, stretch_up: false, stretch_down: false,
  squish_left: false, squish_right: false, squish_up: false, squish_down: false,
  isSpeaking: false, speechText: '',
  bubbles: [] as Bubble[],
  graveyardBubbles: [] as Bubble[],
});

const targetColour = reactive({ r: 133, g: 239, b: 238 });
const currentColour = reactive({ r: 133, g: 239, b: 238 });
const tintStrength = ref(1.0);

const author = ref(localStorage.getItem('bbyUsername') || 'kevinonline420');
function setUsername(name: string) { author.value = name; localStorage.setItem('bbyUsername', name); }

const webUserId = (() => {
  let v = localStorage.getItem('bbyWebUID');
  if (!v) { v = (globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2)); localStorage.setItem('bbyWebUID', v); }
  return v;
})();

const userColour = ref<UserColour>(JSON.parse(localStorage.getItem('bbyUserColour') || '{"r":133,"g":239,"b":238}'));
function setUserColour(r: number, g: number, b: number) {
  const newColour = { r, g, b };
  userColour.value = newColour;
  localStorage.setItem('bbyUserColour', JSON.stringify(newColour));
}

const bbyFacts = ref<Record<string, { value: string, author: string }>>({});
let isClientRunning = false;
const seenMessageIds = new Set<string>();

async function fetchBbyFacts() {
  try {
    bbyFacts.value = await api.getBbyBook();
    console.log(`Loaded ${Object.keys(bbyFacts.value).length} bbyfacts!`);
  } catch (error) { console.error("Could not fetch bbybook:", error); }
}

const paintOverlayData = ref<ImageData | null>(null);
const paintVersion = ref(0);
const bumpPaintVersion = _.throttle(() => { paintVersion.value++; }, 16, { trailing: true });
export function tickPaint() { bumpPaintVersion(); }

const lastPaintEventId = ref<string | null>(null);

async function fetchInitialPaintCanvas() {
  try {
    const data = await api.getPaintCanvas();
    if (data.paintOverlayData_b64) {
      const str = atob(data.paintOverlayData_b64);
      const len = str.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) bytes[i] = str.charCodeAt(i);
      const clampedBytes = new Uint8ClampedArray(bytes.buffer);
      paintOverlayData.value = new ImageData(clampedBytes, 64, 64);
      bumpPaintVersion();
      console.log("Initial paint canvas loaded.");
    }
  } catch (error) { console.error("Could not fetch initial paint canvas:", error); }
}

async function sendPixelUpdate(pixels: {x:number, y:number, r:number, g:number, b:number, a:number}[]) {
  try {
    await api.postPixelUpdate({ pixels });
  } catch (error) { console.error("Failed to send pixel update:", error); }
}

function startClient() {
  if (isClientRunning) return;
  isClientRunning = true;

  fetchBbyFacts();
  fetchInitialPaintCanvas();

  setInterval(async () => {
    try {
      const serverState = await api.getState();
      Object.assign(bbyState, serverState);

      if (serverState.R !== undefined) {
        targetColour.r = serverState.R;
        targetColour.g = serverState.G;
        targetColour.b = serverState.B;
      }
    } catch { /* ignore poll errors */ }
  }, 500);

  setInterval(async () => {
    if (!paintOverlayData.value) return;
    try {
      // This endpoint is unique; keep direct fetch for URL searchParams.
      const url = new URL('https://childofanandroid.co.uk/api/paint_events');
      if (lastPaintEventId.value) url.searchParams.append('since', lastPaintEventId.value);
      const response = await fetch(url.toString());
      if (!response.ok) return;

      const events: {id: string, pixels: {x:number, y:number, r:number, g:number, b:number, a:number}[]}[] = await response.json();
      if (events.length > 0) {
        const data = paintOverlayData.value.data;
        for (const ev of events) {
          for (const p of ev.pixels) {
            const i = (p.y * 64 + p.x) * 4;
            data[i] = p.r; data[i+1] = p.g; data[i+2] = p.b; data[i+3] = p.a;
          }
        }
        bumpPaintVersion();
        lastPaintEventId.value = events[events.length - 1].id;
      }
    } catch { /* ignore poll errors */ }
  }, 250);

  setInterval(fetchInitialPaintCanvas, 60000);

  setInterval(async () => {
    try {
      const serverHistory: { id: string; author: string; text: string; colour: UserColour }[] = await api.getChatHistory();
      const serverIds = new Set(serverHistory.map(m => m.id));
      seenMessageIds.forEach(id => { if (!serverIds.has(id)) seenMessageIds.delete(id); });

      serverHistory.forEach(message => {
        // ... (bubble creation logic is unchanged) ...
        const bubbleExists = bbyState.bubbles.some(b => b.id === message.id);
        const ghostExists = bbyState.graveyardBubbles.some(g => g.id === `ghost-${message.id}`);
        if (!bubbleExists && !ghostExists && !seenMessageIds.has(message.id)) {
          const randw = (min: number, max: number) => `${Math.random() * (max - min) + min}vw`;
          const randh = (min: number, max: number) => `${Math.random() * (max - min) + min}vh`;
          const bubbleColour = message.colour || { r: 103, g: 209, b: 208 };
          const { r, g, b } = bubbleColour;
          const stampedBgColour = `rgba(${r}, ${g}, ${b}, 0.9)`;
          const stampedBorderColour = `rgb(${Math.max(0, r - 30)}, ${Math.max(0, g - 30)}, ${Math.max(0, b - 30)})`;

          const baseTime = (Math.random() * 120000) + 30000;
          const timePerChar = (Math.random() * 3000) + 100;
          const maxTime = (Math.random() * 600000);
          const textLength = message.text.length;
          let timeout = Math.min(baseTime + textLength * timePerChar, maxTime);
          const jitter = Math.random() * 3000 - 1500;

          const newBubble: Bubble = {
            id: message.id, text: message.text, author: message.author,
            ghostX: randw(-50, 50), ghostY: randh(-50, 50),
            ghostR: `${Math.random() * jitter * (Math.random() > 0.5 ? 1 : -1) + 42}deg`,
            ghostOpacity1: (Math.random() * 0.2), ghostOpacity2: (Math.random() * 0.1),
            ghostBlur: (Math.random() * 100), bgColour: stampedBgColour, borderColour: stampedBorderColour,
          };

          bbyState.bubbles.push(newBubble);
          seenMessageIds.add(message.id);
          setTimeout(() => removeBubble(newBubble.id), timeout + jitter);
        }
      });
    } catch (error) { console.error("failed to fetch chat history:", error); }
  }, 4200);

  function colourAnimationLoop() {
    currentColour.r += (targetColour.r - currentColour.r) * 0.06;
    currentColour.g += (targetColour.g - currentColour.g) * 0.03;
    currentColour.b += (targetColour.b - currentColour.b) * 0.06;
    requestAnimationFrame(colourAnimationLoop);
  }
  requestAnimationFrame(colourAnimationLoop);
}

async function requestStateChange(updates: object) {
  try {
    await api.postStateChange(updates);
  } catch (error) { console.error("failed to send state change:", error); }
}

function setBbyTintColour(R: number, G: number, B: number) {
  targetColour.r = R; targetColour.g = G; targetColour.b = B;
  requestStateChange({ R, G, B });
}
async function sendBbyPaintColour(R: number, G: number, B: number) {
  await requestStateChange({ R, G, B });
}

async function say(text: string, author: string, colour: UserColour) {
  const trimmed = text.trim();
  if (!trimmed) return;
  setBbyTintColour(colour.r, colour.g, colour.b);
  try {
    await api.postSay({
      text: trimmed,
      author, // legacy/display only
      colour,
      platform: 'web',
      user_id: webUserId,
      handle: author,
      display_name: author,
      speak: true,            // <— NEW
    });
  } catch (error) { console.error("failed to talk to baby:", error); }
}

const MAX_GHOSTS = 100;
function removeBubble(id: string) {
  const bubbleEl = document.querySelector(`[data-bubble-id="${id}"]`);
  const bubbleIndex = bbyState.bubbles.findIndex(b => b.id === id);

  if (bubbleEl && bubbleIndex !== -1) {
    const rect = bubbleEl.getBoundingClientRect();
    const originalBubble = bbyState.bubbles[bubbleIndex];

    const duration = Math.random() * 2000 + 30;
    const delay = Math.random() * 2;
    const easings = ['ease-in-out', 'ease-in', 'ease-out', 'linear', 'cubic-bezier(0.25, 1, 0.5, 1)', 'cubic-bezier(0.4, 0, 0.2, 1)'];
    const easing = easings[Math.floor(Math.random() * easings.length)];

    const ghostBubble: Bubble = {
      id: `ghost-${originalBubble.id}`, text: originalBubble.text,
      startX: `${rect.left + window.scrollX}px`, startY: `${rect.top + window.scrollY}px`,
      width: `${rect.width}px`, height: `${rect.height}px`,
      ghostX: originalBubble.ghostX, ghostY: originalBubble.ghostY, ghostR: originalBubble.ghostR,
      ghostOpacity1: originalBubble.ghostOpacity1, ghostOpacity2: originalBubble.ghostOpacity2, ghostBlur: originalBubble.ghostBlur,
      author: originalBubble.author, duration: `${duration}s`, easing: easing, delay: `${delay}s`,
      bgColour: originalBubble.bgColour, borderColour: originalBubble.borderColour,
    };

    bbyState.graveyardBubbles.push(ghostBubble);
    if (bbyState.graveyardBubbles.length > MAX_GHOSTS) bbyState.graveyardBubbles.shift();
    bbyState.bubbles.splice(bubbleIndex, 1);
  } else if (bubbleIndex !== -1) {
    bbyState.bubbles.splice(bubbleIndex, 1);
  }
}
function clearBubbles() { bbyState.bubbles = []; bbyState.graveyardBubbles = []; }
function sayRandomFact() {
  const factKeys = Object.keys(bbyFacts.value);
  if (factKeys.length === 0) { say("I don't know any facts yet...", author.value, userColour.value); return; }
  const randomKey = factKeys[Math.floor(Math.random() * factKeys.length)];
  const fact = bbyFacts.value[randomKey];
  if (fact && fact.value) {
    const message = `hey bby, did you know that ${randomKey} is ${fact.value}?`;
    say(message, author.value, userColour.value);
  }
}

// --- optional admin token + delete helpers ---
export async function deleteGalleryById(id: string, token?: string) {
  const headers: Record<string,string> = {};
  if (token) headers['X-Admin-Token'] = token;
  const res = await fetch(`/api/gallery/${encodeURIComponent(id)}`, { method: 'DELETE', headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
export function extractGalleryIdFromUrl(url: string): string | null {
  try {
    const name = url.split('/').pop() || '';
    return name.replace(/\\.png$/i, '') || null;
  } catch { return null; }
}
export async function deleteGalleryByUrl(url: string, token?: string) {
  const id = extractGalleryIdFromUrl(url);
  if (!id) throw new Error('could not parse id from url');
  return deleteGalleryById(id, token);
}

export async function saveCompositeToServer(label = "manual") {
  const canvas = document.querySelector('[aria-label="AI baby sprite, somewhere between a ghost and a robot"]') as HTMLCanvasElement | null;
  if (!canvas) throw new Error('no canvas');
  const dataUrl = canvas.toDataURL('image/png');

  const j = await api.postSnapshot({ label, composite_png_b64: dataUrl });
  const pngUrl = j?.png_url ?? j?.snapshot?.png_url;
  if (!pngUrl) throw new Error('snapshot saved but no png_url returned');

  try {
    await saveCanvasToGallery(canvas, author.value, label);
  } catch (e: any) {
    console.error('[gallery/save] failed:', e?.message || e);
  }
  return pngUrl as string;
}

export async function saveCanvasToGallery(canvas: HTMLCanvasElement, authorName: string, label = 'grid') {
  const blob: Blob = await new Promise((res, rej) => canvas.toBlob(b => b ? res(b) : rej(new Error('canvas.toBlob() returned null')), 'image/png', 1));
  const j = await api.postSaveToGallery(blob, authorName, label);
  return j.url as string;
}

export async function saveTestGridImage(canvas: HTMLCanvasElement, authorName: string, label = 'grid') {
  return saveCanvasToGallery(canvas, authorName, label);
}

export async function fetchTestGridGallery() {
  try {
    return await api.getGallery() as { url: string; author?: string; label?: string }[];
  } catch (error) {
    console.error('Could not fetch live gallery:', error);
    return [];
  }
}

export async function fetchBbyBookGallery() {
  try {
    const [gallery, book] = await Promise.all([
      api.getGallery() as Promise<{ url: string; author?: string; label?: string }[]>,
      api.getBbyBook() as Promise<Record<string, {
        value: string;
        author: string;
        timestamp: number;
        teach_bonus: number;
        num_produced: number;
        id: number;
      }>>
    ]);

    return gallery
      // The filter remains the same: it only includes gallery items
      // that have a label which is a key in the bbybook.
      .filter((item): item is { url: string; author?: string; label: string } =>
        !!item.label && !!book[item.label]
      )
      // This part is updated to return ALL the data we need for the styled card.
      .map(item => ({
        url: item.url,
        imageAuthor: item.author,
        factName: item.label,      // The name of the fact (e.g., "cat")
        factData: book[item.label] // The full object with all details
      }));
  } catch (error) {
    console.error('Could not fetch bbybook gallery:', error);
    return [];
  }
}

export async function getRandomBbyFactPrompt() {
  try {
    if (Object.keys(bbyFacts.value).length === 0) await fetchBbyFacts();
    const gallery = await api.getGallery() as { label?: string }[];
    const labels = new Set(gallery.map(g => g.label).filter(Boolean));
    const entries = Object.entries(bbyFacts.value).filter(([key]) => !labels.has(key));
    if (entries.length === 0) return null;
    const [name, data] = entries[Math.floor(Math.random() * entries.length)];
    return { name, ...data } as { name: string; value: string; author: string };
  } catch (error) {
    console.error('Could not fetch unillustrated bbyfact:', error);
    return null;
  }
}

let lastSeenAutoSnapId: string | null = null;
export async function pollActivityForAutosnap() {
  try {
    const a = await api.getActivity();
    if (a.last_autosnap_id && a.last_autosnap_id !== lastSeenAutoSnapId) {
      const canvas = document.querySelector('[aria-label="AI baby sprite, somewhere between a ghost and a robot"]') as HTMLCanvasElement | null;
      if (canvas) {
        const dataUrl = canvas.toDataURL('image/png');
        await api.postAttachPng(a.last_autosnap_id, { composite_png_b64: dataUrl });
      }
      lastSeenAutoSnapId = a.last_autosnap_id;
    }
  } catch { /* ignore poll errors */ }
  setTimeout(pollActivityForAutosnap, 7000);
}

watch(currentColour, (newColour) => {
  const r = Math.round(newColour.r); const g = Math.round(newColour.g); const b = Math.round(newColour.b);
  const root = document.documentElement;
  root.style.setProperty('--bby-colour', `rgba(${r}, ${g}, ${b}, 0.9)`);
  const panelR = Math.max(0, r - 75); const panelG = Math.max(0, g - 100); const panelB = Math.max(0, b - 75);
  root.style.setProperty('--bby-colour-panel', `rgb(${panelR}, ${panelG}, ${panelB})`);
  const borderR = Math.max(0, r - 30); const borderG = Math.max(0, g - 40); const borderB = Math.max(0, b - 30);
  root.style.setProperty('--bby-colour-dark', `rgb(${borderR}, ${borderG}, ${borderB})`);
  const bgR = Math.max(0, r - 135); const bgG = Math.max(0, g - 180); const bgB = Math.max(0, b - 135);
  root.style.setProperty('--bby-colour-black', `rgb(${bgR}, ${bgG}, ${bgB})`);
}, { deep: true, immediate: true });
watch(userColour, (newUserColour) => {
  const { r, g, b } = newUserColour;
  const root = document.documentElement;
  root.style.setProperty('--user-colour', `rgb(${r}, ${g}, ${b})`);
  const hoverR = Math.max(0, r - 30); const hoverG = Math.max(0, g - 40); const hoverB = Math.max(0, b - 30);
  root.style.setProperty('--user-colour-dark', `rgb(${hoverR}, ${hoverG}, ${hoverB})`);
}, { deep: true, immediate: true });

export function bbyUse() {
  startClient();
  return {
    bbyState: readonly(bbyState), currentColour: readonly(currentColour), tintStrength: readonly(tintStrength),
    author: readonly(author), userColour: readonly(userColour), paintOverlayData, paintVersion, tickPaint,
    sendPixelUpdate, setUsername, setUserColour, requestStateChange, setBbyTintColour, sendBbyPaintColour, say,
    removeBubble, sayRandomFact, saveCompositeToServer, pollActivityForAutosnap, saveTestGridImage, fetchTestGridGallery,
    fetchBbyBookGallery, getRandomBbyFactPrompt, clearBubbles, bbyFacts: readonly(bbyFacts),
  };
}