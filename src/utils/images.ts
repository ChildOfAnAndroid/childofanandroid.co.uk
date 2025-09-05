export interface LoadImageOptions {
  crossOrigin?: string;
}

export function loadImage(src: string, options: LoadImageOptions = {}): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    if (options.crossOrigin) img.crossOrigin = options.crossOrigin;
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
    img.src = src;
  });
}
