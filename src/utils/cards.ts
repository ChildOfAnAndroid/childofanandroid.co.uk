import { loadImage } from './images';

export interface CardLike { label: string }

export function resolveCardLabel<T extends CardLike>(cards: T[], label: string): string {
  const match = cards.find(c => c.label.toLowerCase() === label.toLowerCase());
  return match ? match.label : label;
}

export interface StampCard extends CardLike {
  url: string;
  stamp_url?: string;         // may be missing
  stamp_file?: string;        // new: direct filename from index.json
  colour?: { h: number; s: number; l: number }; // optional hue data
}

const STAMP_SUFFIX_RE = /\.stamp\.png$/i;
const PNG_SUFFIX_RE = /\.png$/i;

export function normalizeStampUrl(url?: string | null): string | null {
  if (!url) return null;

  const hashIndex = url.indexOf('#');
  const hashPart = hashIndex >= 0 ? url.slice(hashIndex) : '';
  const withoutHash = hashIndex >= 0 ? url.slice(0, hashIndex) : url;

  const queryIndex = withoutHash.indexOf('?');
  const queryPart = queryIndex >= 0 ? withoutHash.slice(queryIndex) : '';
  const pathPart = queryIndex >= 0 ? withoutHash.slice(0, queryIndex) : withoutHash;

  if (STAMP_SUFFIX_RE.test(pathPart)) {
    return `${pathPart}${queryPart}${hashPart}`;
  }

  if (PNG_SUFFIX_RE.test(pathPart)) {
    const stampedPath = pathPart.replace(PNG_SUFFIX_RE, '.stamp.png');
    return `${stampedPath}${queryPart}${hashPart}`;
  }

  return null;
}

export function getStampUrlCandidates(card: StampCard): string[] {
  const urls = new Set<string>();

  // 1. Use explicit stamp_file from index.json if present
  if (card.stamp_file) {
    urls.add(`/api/gallery/file/${card.stamp_file}`);
  }

  // 2. Use provided stamp_url if any
  const preferred = normalizeStampUrl(card.stamp_url);
  if (preferred) urls.add(preferred);

  // 3. Derive from normal url
  const derived = normalizeStampUrl(card.url);
  if (derived) urls.add(derived);

  return Array.from(urls);
}

export function getPrimaryStampUrl(card: StampCard): string | null {
  const [primary] = getStampUrlCandidates(card);
  return primary ?? null;
}

export async function loadCardStamp(card: StampCard, maxSize = 64): Promise<ImageData | null> {
  const urls = getStampUrlCandidates(card);
  if (urls.length === 0) {
    console.error('No stamp URL available for card:', card.label);
    return null;
  }

  for (const url of urls) {
    try {
      const img = await loadImage(url, { crossOrigin: 'Anonymous' });
      const scale = Math.min(1, maxSize / Math.max(img.width, img.height));
      const w = Math.max(1, Math.floor(img.width * scale));
      const h = Math.max(1, Math.floor(img.height * scale));
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
      canvas.width = w;
      canvas.height = h;
      (ctx as any).imageSmoothingEnabled = false;
      ctx.drawImage(img, 0, 0, w, h);
      return ctx.getImageData(0, 0, w, h);
    } catch {
      // try next url
    }
  }
  console.error('Failed to load stamp:', card.label);
  return null;
}

/**
 * Utility: sort cards by colour (hue) if available, fallback to label.
 */
export function sortCardsByColour(cards: StampCard[]): StampCard[] {
  return [...cards].sort((a, b) => {
    if (a.colour && b.colour) {
      const ah = a.colour.h, bh = b.colour.h;
      const as = a.colour.s, bs = b.colour.s;
      const al = a.colour.l, bl = b.colour.l;

      // Sort by hue, then saturation, then lightness
      if (ah !== bh) return ah - bh;
      if (as !== bs) return as - bs;
      return al - bl;
    }
    if (a.colour) return -1;
    if (b.colour) return 1;
    return a.label.localeCompare(b.label);
  });
}