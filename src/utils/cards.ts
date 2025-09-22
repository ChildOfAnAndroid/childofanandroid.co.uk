import { loadImage } from './images';

export interface CardLike { label: string }

export function resolveCardLabel<T extends CardLike>(cards: T[], label: string): string {
  const match = cards.find(c => c.label.toLowerCase() === label.toLowerCase());
  return match ? match.label : label;
}

export interface StampCard extends CardLike { url: string; stamp_url: string }

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
  const preferred = normalizeStampUrl(card.stamp_url);
  if (preferred) urls.add(preferred);
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
