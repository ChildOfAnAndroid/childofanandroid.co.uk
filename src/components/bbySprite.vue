<template>
  <canvas
    ref="bbyCanvas"
    aria-label="AI baby sprite, somewhere between a ghost and a robot"
    role="img"
    @click="requestStateChange({ jumping: true })"
  ></canvas>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { bbyUse } from '@/composables/bbyUse.ts';
import bbyBodyUrl from '@/assets/bbySprites/bbyBODY.png';
import bbyCheeksUrl from '@/assets/bbySprites/bbyCHEEKS.png';
import bbyEyesUrl from '@/assets/bbySprites/bbyEYES.png';
import bbyMouthUrl from '@/assets/bbySprites/bbyMOUTH.png';

const { bbyState, currentColour, tintStrength, requestStateChange } = bbyUse();

const SPRITE_W = 64;
const SPRITE_H = 64;
const numMouthStyles = 63;
const bbyBODY_numLayers = 5;

const bbyCanvas = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;
const images: { [key: string]: HTMLImageElement } = {};

const loadImage = (src: string): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = (e) => reject(`Failed to load image: ${src} - ${e}`);
    img.src = src;
  });
};

// resize canvas to fit parent, keep ratio, stay crisp
function fitCanvas() {
  const canvas = bbyCanvas.value!;
  const parent = canvas.parentElement!;
  const dpr = window.devicePixelRatio || 1;
  const box = parent.getBoundingClientRect();

  // integer scale for pixel-snappy, or remove Math.floor for smooth
  const s = Math.floor(Math.min(box.width / SPRITE_W, box.height / SPRITE_H)) || 1;

  const cssW = SPRITE_W * s;
  const cssH = SPRITE_H * s;

  canvas.style.width  = cssW + 'px';
  canvas.style.height = cssH + 'px';

  canvas.width  = Math.round(cssW * dpr);
  canvas.height = Math.round(cssH * dpr);

  const tx = (box.width  - cssW) / 2;
  const ty = (box.height - cssH) / 2;

  ctx!.setTransform(s * dpr, 0, 0, s * dpr, tx * dpr, ty * dpr);
}

const draw = () => {
  if (!ctx || !images.bbyBODY) return;

  ctx.save();
  ctx.clearRect(-1e5, -1e5, 2e5, 2e5);
  ctx.imageSmoothingEnabled = false;

  // offscreen base
  const offscreenCanvas = document.createElement('canvas');
  offscreenCanvas.width = SPRITE_W;
  offscreenCanvas.height = SPRITE_H;
  const offCtx = offscreenCanvas.getContext('2d', { willReadFrequently: true })!;

  // draw base layers
  for (let i = 0; i < bbyBODY_numLayers; i++) {
    offCtx.drawImage(
      images.bbyBODY,
      0, i * SPRITE_H, SPRITE_W, SPRITE_H,
      0, 0, SPRITE_W, SPRITE_H
    );
  }

  // tint
  const imageData = offCtx.getImageData(0, 0, SPRITE_W, SPRITE_H);
  const pixels = imageData.data;
  for (let i = 0; i < pixels.length; i += 4) {
    const r_orig = pixels[i];
    const g_orig = pixels[i + 1];
    const b_orig = pixels[i + 2];

    const gray = (r_orig + g_orig + b_orig) / 3;
    const rTint = gray * currentColour.r / 255;
    const gTint = gray * currentColour.g / 255;
    const bTint = gray * currentColour.b / 255;

    pixels[i]   = (1 - tintStrength.value) * r_orig + tintStrength.value * rTint;
    pixels[i+1] = (1 - tintStrength.value) * g_orig + tintStrength.value * gTint;
    pixels[i+2] = (1 - tintStrength.value) * b_orig + tintStrength.value * bTint;
  }
  offCtx.putImageData(imageData, 0, 0);

  // stretch/squish in SPRITE pixels
  const stretch_x = SPRITE_W
    + (bbyState.stretch_left ? 1 : 0) + (bbyState.stretch_right ? 1 : 0)
    - (bbyState.squish_left ? 1 : 0)  - (bbyState.squish_right ? 1 : 0);

  const stretch_y = SPRITE_H
    + (bbyState.stretch_up ? 1 : 0) + (bbyState.stretch_down ? 1 : 0)
    - (bbyState.squish_up ? 1 : 0)  - (bbyState.squish_down ? 1 : 0);

  const jumpset = bbyState.jumping ? -4 : 0;
  const offset_x = (SPRITE_W - stretch_x) / 2 - (bbyState.stretch_left ? 1 : 0);
  const offset_y = (SPRITE_H - stretch_y) / 2 - (bbyState.stretch_up ? 1 : 0) + jumpset;

  const baseOffsetX = (SPRITE_W - SPRITE_W) / 2;
  const baseOffsetY = (SPRITE_H - SPRITE_H) / 2 + jumpset;

  // draw tinted body
  ctx.drawImage(offscreenCanvas, offset_x, offset_y, stretch_x, stretch_y);

  // overlays
  ctx.filter = 'brightness(85%)';
  if (bbyState.cheeks_on) {
    ctx.drawImage(images.bbyCHEEKS, 0, 0, SPRITE_W, SPRITE_H,
                  baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H);
  }

  const eyeSourceX = bbyState.eyes * SPRITE_W;
  for (let i = 0; i < 3 + (bbyState.tears_on ? 1 : 0); i++) {
    ctx.drawImage(images.bbyEYES, eyeSourceX, i * SPRITE_H, SPRITE_W, SPRITE_H,
                  baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H);
  }

  const mouthSourceX = Math.max(0, Math.min(bbyState.mouth, numMouthStyles - 1)) * SPRITE_W;
  ctx.drawImage(images.bbyMOUTH, mouthSourceX, 0, SPRITE_W, SPRITE_H,
                baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H);

  ctx.filter = 'none';
  ctx.restore();
};

onMounted(async () => {
  if (!bbyCanvas.value) return;
  ctx = bbyCanvas.value.getContext('2d');

  try {
    const [body, cheeks, eyes, mouth] = await Promise.all([
      loadImage(bbyBodyUrl),
      loadImage(bbyCheeksUrl),
      loadImage(bbyEyesUrl),
      loadImage(bbyMouthUrl),
    ]);
    images.bbyBODY = body;
    images.bbyCHEEKS = cheeks;
    images.bbyEYES = eyes;
    images.bbyMOUTH = mouth;

    fitCanvas();
    draw();

    const ro = new ResizeObserver(() => { fitCanvas(); draw(); });
    ro.observe(bbyCanvas.value.parentElement!);
    window.addEventListener('resize', () => { fitCanvas(); draw(); });

  } catch (error) {
    console.error("failed to load bby sprites:", error);
  }
});

watch([bbyState, currentColour, tintStrength], () => {
  fitCanvas();
  draw();
}, { deep: true });
</script>

<style scoped>

</style>
