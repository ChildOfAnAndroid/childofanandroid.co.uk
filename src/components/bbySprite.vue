<template>
  <canvas
    ref="bbyCanvas"
    aria-label="AI baby sprite, somewhere between a ghost and a robot"
    role="img"
    @click="requestStateChange({ jumping: true })"
  ></canvas>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import { bbyUse } from '@/composables/bbyUse.ts';
import bbyBodyUrl from '@/assets/bbySprites/bbyBODY.png';
import bbyCheeksUrl from '@/assets/bbySprites/bbyCHEEKS.png';
import bbyEyesUrl from '@/assets/bbySprites/bbyEYES.png';
import bbyMouthUrl from '@/assets/bbySprites/bbyMOUTH.png';

const { bbyState, currentColour, tintStrength, requestStateChange, paintOverlayData } = bbyUse();

const SPRITE_W = 64;
const SPRITE_H = 64;
const NUM_MOUTH_STYLES = 63;
const BODY_LAYERS = 5;

const bbyCanvas = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;
let ro: ResizeObserver | null = null;
let onWinResize: (() => void) | null = null;

const images: Record<string, HTMLImageElement> = {};

const loadImage = (src: string): Promise<HTMLImageElement> =>
  new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = (e) => reject(`Failed to load image: ${src} - ${e}`);
    img.src = src;
  });

const paintCanvas = document.createElement('canvas');
paintCanvas.width = SPRITE_W;
paintCanvas.height = SPRITE_H;
const pctx = paintCanvas.getContext('2d', { willReadFrequently: true })!;

watch(paintOverlayData, (img) => {
  if (!img || !pctx) return;
  pctx.clearRect(0, 0, SPRITE_W, SPRITE_H);
  pctx.putImageData(img, 0, 0);  // per-pixel alpha
  draw();                        // show fades
});

const maskedPaintCanvas = document.createElement('canvas');
maskedPaintCanvas.width = SPRITE_W;
maskedPaintCanvas.height = SPRITE_H;
const mctx = maskedPaintCanvas.getContext('2d')!;

function fitCanvas() {
  if (!bbyCanvas.value || !ctx) return;
  const canvas = bbyCanvas.value;
  const parent = canvas.parentElement!;
  const dpr = window.devicePixelRatio || 1;
  const box = parent.getBoundingClientRect();
  const s = Math.min(box.width / SPRITE_W, box.height / SPRITE_H) || 1;

  const cssW = SPRITE_W * s;
  const cssH = SPRITE_H * s;

  canvas.style.width = cssW + 'px';
  canvas.style.height = cssH + 'px';
  canvas.width = Math.round(cssW * dpr);
  canvas.height = Math.round(cssH * dpr);

  ctx.setTransform(s * dpr, 0, 0, s * dpr, 0, 0);
  ctx.imageSmoothingEnabled = false;
}

/** Main draw */
function draw() {
  if (!ctx || !images.bbyBODY) return;

  ctx.save();
  ctx.clearRect(-1e5, -1e5, 2e5, 2e5);
  ctx.imageSmoothingEnabled = false;

  const bodyCanvas = document.createElement('canvas');
  bodyCanvas.width = SPRITE_W;
  bodyCanvas.height = SPRITE_H;
  const bctx = bodyCanvas.getContext('2d', { willReadFrequently: true })!;

  for (let i = 0; i < BODY_LAYERS; i++) {
    bctx.drawImage(
      images.bbyBODY,
      0, i * SPRITE_H, SPRITE_W, SPRITE_H,
      0, 0, SPRITE_W, SPRITE_H
    );
  }

  const imageData = bctx.getImageData(0, 0, SPRITE_W, SPRITE_H);
  const px = imageData.data;
  const t = tintStrength.value;

  for (let i = 0; i < px.length; i += 4) {
    if (px[i + 3] === 0) continue; // skip fully transparent pixels
    const r0 = px[i], g0 = px[i + 1], b0 = px[i + 2];
    const gray = (r0 + g0 + b0) / 3;

    const rTint = gray * (currentColour.r / 255);
    const gTint = gray * (currentColour.g / 255);
    const bTint = gray * (currentColour.b / 255);

    px[i]     = (1 - t) * r0 + t * rTint;
    px[i + 1] = (1 - t) * g0 + t * gTint;
    px[i + 2] = (1 - t) * b0 + t * bTint;
  }
  bctx.putImageData(imageData, 0, 0);

  const stretch_x =
    SPRITE_W +
    (bbyState.stretch_left ? 1 : 0) +
    (bbyState.stretch_right ? 1 : 0) -
    (bbyState.squish_left ? 1 : 0) -
    (bbyState.squish_right ? 1 : 0);

  const stretch_y =
    SPRITE_H +
    (bbyState.stretch_up ? 1 : 0) +
    (bbyState.stretch_down ? 1 : 0) -
    (bbyState.squish_up ? 1 : 0) -
    (bbyState.squish_down ? 1 : 0);

  const jumpset = bbyState.jumping ? -4 : 0;
  const offset_x = (SPRITE_W - stretch_x) / 2 - (bbyState.stretch_left ? 1 : 0);
  const offset_y = (SPRITE_H - stretch_y) / 2 - (bbyState.stretch_up ? 1 : 0) + jumpset;

  const baseOffsetX = 0;
  const baseOffsetY = jumpset;

  mctx.globalCompositeOperation = 'source-over';
  mctx.clearRect(0, 0, SPRITE_W, SPRITE_H);
  mctx.drawImage(paintCanvas, 0, 0);          // put raw paint down
  mctx.globalCompositeOperation = 'destination-in';
  mctx.drawImage(bodyCanvas, 0, 0);           // keep only where body is
  mctx.globalCompositeOperation = 'source-over'; // reset for next frame

  ctx.drawImage(bodyCanvas,       offset_x, offset_y, stretch_x, stretch_y);
  ctx.drawImage(maskedPaintCanvas, offset_x, offset_y, stretch_x, stretch_y);

  ctx.filter = 'brightness(85%)';
  if (bbyState.cheeks_on) {
    ctx.drawImage(images.bbyCHEEKS, 0, 0, SPRITE_W, SPRITE_H, baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H);
  }
  ctx.filter = 'none';

  const eyeSourceX = bbyState.eyes * SPRITE_W;
  for (let i = 0; i < 3 + (bbyState.tears_on ? 1 : 0); i++) {
    ctx.drawImage(
      images.bbyEYES,
      eyeSourceX, i * SPRITE_H, SPRITE_W, SPRITE_H,
      baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H
    );
  }

  const mouthIndex = Math.max(0, Math.min(bbyState.mouth, NUM_MOUTH_STYLES - 1));
  const mouthSourceX = mouthIndex * SPRITE_W;
  ctx.drawImage(
    images.bbyMOUTH,
    mouthSourceX, 0, SPRITE_W, SPRITE_H,
    baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H
  );

  ctx.restore();
}

onMounted(async () => {
  if (!bbyCanvas.value) return;
  ctx = bbyCanvas.value.getContext('2d');
  if (!ctx) return;

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

    ro = new ResizeObserver(() => {
      fitCanvas();
      draw();
    });
    ro.observe(bbyCanvas.value.parentElement!);

  onWinResize = () => {
      fitCanvas();
      draw();
    };
    window.addEventListener('resize', onWinResize);
  } catch (err) {
    console.error('failed to load bby sprites:', err);
  }
});

onBeforeUnmount(() => {
  if (ro) { try { ro.disconnect(); } catch {} ro = null; }
  if (onWinResize) {
    window.removeEventListener('resize', onWinResize);
    onWinResize = null;
  }
});

/** Re-render when state/tint changes */
watch([bbyState, currentColour, tintStrength], () => {
  fitCanvas();
  draw();
}, { deep: true });
</script>

<style scoped>
/* canvas is sized by fitCanvas; no extra styles needed */
</style>
