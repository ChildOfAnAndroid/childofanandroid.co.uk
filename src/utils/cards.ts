import { loadImage } from './images';

export interface CardLike { label: string }

export function resolveCardLabel<T extends CardLike>(cards: T[], label: string): string {
  const match = cards.find(c => c.label.toLowerCase() === label.toLowerCase());
  return match ? match.label : label;
}

export interface StampCard extends CardLike { url: string; stamp_url?: string }

export async function loadCardStamp(card: StampCard, maxSize = 64): Promise<ImageData | null> {
  const urls: string[] = [];
  if (card.stamp_url) urls.push(card.stamp_url);
  urls.push(card.url.replace(/\.png$/i, '.stamp.png'));
  urls.push(card.url);

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
