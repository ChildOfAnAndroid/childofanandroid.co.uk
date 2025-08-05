<template>
  <canvas ref="bbyCanvas" :width="canvasSize[0]" :height="canvasSize[1]"></canvas>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { bbyUse } from '@/composables/bbyUse.ts';

// Import images for Vite to process
import bbyBodyUrl from '@/assets/bbySprites/bbyBODY.png';
import bbyCheeksUrl from '@/assets/bbySprites/bbyCHEEKS.png';
import bbyEyesUrl from '@/assets/bbySprites/bbyEYES.png';
import bbyMouthUrl from '@/assets/bbySprites/bbyMOUTH.png';

const { bbyState, currentColour, tintStrength } = bbyUse();

const spriteSize = { width: 64, height: 64 };
const canvasSize = [68, 68];
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

const draw = () => {
  if (!ctx || !images.bbyBODY) return;

  ctx.clearRect(0, 0, canvasSize[0], canvasSize[1]);
  ctx.imageSmoothingEnabled = false;

  const offscreenCanvas = document.createElement('canvas');
  offscreenCanvas.width = spriteSize.width;
  offscreenCanvas.height = spriteSize.height;
  const offCtx = offscreenCanvas.getContext('2d', { willReadFrequently: true })!;

  // 1. Draw base body to offscreen canvas
  for (let i = 0; i < bbyBODY_numLayers; i++) {
    offCtx.drawImage(images.bbyBODY, 0, i * spriteSize.height, spriteSize.width, spriteSize.height, 0, 0, spriteSize.width, spriteSize.height);
  }

  // 2. Apply colour tint pixel by pixel
  const imageData = offCtx.getImageData(0, 0, spriteSize.width, spriteSize.height);
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

  // 3. Calculate final dimensions and position
  const stretch_x = spriteSize.width + (bbyState.stretch_left ? 1 : 0) + (bbyState.stretch_right ? 1 : 0) - (bbyState.squish_left ? 1 : 0) - (bbyState.squish_right ? 1 : 0);
  const stretch_y = spriteSize.height + (bbyState.stretch_up ? 1 : 0) + (bbyState.stretch_down ? 1 : 0) - (bbyState.squish_up ? 1 : 0) - (bbyState.squish_down ? 1 : 0);
  const offset_x = (canvasSize[0] - stretch_x) / 2 - (bbyState.stretch_left ? 1 : 0);
  let offset_y = (canvasSize[1] - stretch_y) / 2 - (bbyState.stretch_up ? 1 : 0);
  const jumpset = bbyState.jumping ? -4 : 0;
  offset_y += jumpset;
  const baseOffsetX = (canvasSize[0] - spriteSize.width) / 2;
  const baseOffsetY = (canvasSize[1] - spriteSize.height) / 2 + jumpset;

  // 4. Draw tinted, stretched body
  ctx.drawImage(offscreenCanvas, offset_x, offset_y, stretch_x, stretch_y);
  
  // 5. Draw facial features with darken filter
  ctx.filter = 'brightness(85%)';
  if (bbyState.cheeks_on) {
    ctx.drawImage(images.bbyCHEEKS, 0, 0, spriteSize.width, spriteSize.height, baseOffsetX, baseOffsetY, spriteSize.width, spriteSize.height);
  }
  const eyeSourceX = bbyState.eyes * spriteSize.width;
  for (let i = 0; i < 3 + (bbyState.tears_on ? 1 : 0); i++) {
     ctx.drawImage(images.bbyEYES, eyeSourceX, i * spriteSize.height, spriteSize.width, spriteSize.height, baseOffsetX, baseOffsetY, spriteSize.width, spriteSize.height);
  }
  const mouthSourceX = Math.max(0, Math.min(bbyState.mouth, numMouthStyles)) * spriteSize.width;
  ctx.drawImage(images.bbyMOUTH, mouthSourceX, 0, spriteSize.width, spriteSize.height, baseOffsetX, baseOffsetY, spriteSize.width, spriteSize.height);
  
  ctx.filter = 'none';
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
    draw();
  } catch (error) {
    console.error("failed to load bby sprites:", error);
  }
});

watch([bbyState, currentColour], draw, { deep: true });
</script>

<style scoped>
canvas {
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
  width: 68px;
  height: 68px;
}
</style>