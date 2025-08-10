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

// UPDATED: Import the shared paint data
const { bbyState, currentColour, tintStrength, requestStateChange, paintOverlayData } = bbyUse();

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

function fitCanvas() {
	const canvas = bbyCanvas.value!;
	const parent = canvas.parentElement!;
	const dpr = window.devicePixelRatio || 1;
	const box = parent.getBoundingClientRect();
	const s = Math.min(box.width / SPRITE_W, box.height / SPRITE_H) || 1;
	const cssW = SPRITE_W * s;
	const cssH = SPRITE_H * s;
	canvas.style.width	= cssW + 'px';
	canvas.style.height = cssH + 'px';
	canvas.width	= Math.round(cssW * dpr);
	canvas.height = Math.round(cssH * dpr);
	ctx!.setTransform(s * dpr, 0, 0, s * dpr, 0, 0);
}

const draw = () => {
	if (!ctx || !images.bbyBODY) return;

	ctx.save();
	ctx.clearRect(-1e5, -1e5, 2e5, 2e5);
	ctx.imageSmoothingEnabled = false;

	const offscreenCanvas = document.createElement('canvas');
	offscreenCanvas.width = SPRITE_W;
	offscreenCanvas.height = SPRITE_H;
	const offCtx = offscreenCanvas.getContext('2d', { willReadFrequently: true })!;

	for (let i = 0; i < bbyBODY_numLayers; i++) {
		offCtx.drawImage(images.bbyBODY, 0, i * SPRITE_H, SPRITE_W, SPRITE_H, 0, 0, SPRITE_W, SPRITE_H);
	}

	// --- NEW: INTELLIGENT TINTING LOGIC ---
	const imageData = offCtx.getImageData(0, 0, SPRITE_W, SPRITE_H);
	const pixels = imageData.data;
	const paintPixels = paintOverlayData.value?.data; // Get the user's paint data

	for (let i = 0; i < pixels.length; i += 4) {
		// If the base pixel is transparent, do nothing. This preserves the outline.
		if (pixels[i + 3] === 0) continue;

		// Check if the user has painted on this pixel
		if (paintPixels && paintPixels[i + 3] > 0) {
			// If yes, use the user's color directly
			pixels[i]	 = paintPixels[i];
			pixels[i+1] = paintPixels[i+1];
			pixels[i+2] = paintPixels[i+2];
		} else {
			// If no, apply the default server-driven tint
			const r_orig = pixels[i], g_orig = pixels[i+1], b_orig = pixels[i+2];
			const gray = (r_orig + g_orig + b_orig) / 3;
			const rTint = gray * currentColour.r / 255;
			const gTint = gray * currentColour.g / 255;
			const bTint = gray * currentColour.b / 255;
			pixels[i]	 = (1 - tintStrength.value) * r_orig + tintStrength.value * rTint;
			pixels[i+1] = (1 - tintStrength.value) * g_orig + tintStrength.value * gTint;
			pixels[i+2] = (1 - tintStrength.value) * b_orig + tintStrength.value * bTint;
		}
	}
	offCtx.putImageData(imageData, 0, 0);
	// --- END OF NEW LOGIC ---

	const stretch_x = SPRITE_W + (bbyState.stretch_left ? 1 : 0) + (bbyState.stretch_right ? 1 : 0) - (bbyState.squish_left ? 1 : 0)	- (bbyState.squish_right ? 1 : 0);
	const stretch_y = SPRITE_H + (bbyState.stretch_up ? 1 : 0) + (bbyState.stretch_down ? 1 : 0) - (bbyState.squish_up ? 1 : 0)	- (bbyState.squish_down ? 1 : 0);
	const jumpset = bbyState.jumping ? -4 : 0;
	const offset_x = (SPRITE_W - stretch_x) / 2 - (bbyState.stretch_left ? 1 : 0);
	const offset_y = (SPRITE_H - stretch_y) / 2 - (bbyState.stretch_up ? 1 : 0) + jumpset;
	const baseOffsetX = (SPRITE_W - SPRITE_W) / 2;
	const baseOffsetY = (SPRITE_H - SPRITE_H) / 2 + jumpset;

	ctx.drawImage(offscreenCanvas, offset_x, offset_y, stretch_x, stretch_y);

	ctx.filter = 'brightness(85%)';
	if (bbyState.cheeks_on) {
		ctx.drawImage(images.bbyCHEEKS, 0, 0, SPRITE_W, SPRITE_H, baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H);
	}
	const eyeSourceX = bbyState.eyes * SPRITE_W;
	for (let i = 0; i < 3 + (bbyState.tears_on ? 1 : 0); i++) {
		ctx.drawImage(images.bbyEYES, eyeSourceX, i * SPRITE_H, SPRITE_W, SPRITE_H, baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H);
	}
	const mouthSourceX = Math.max(0, Math.min(bbyState.mouth, numMouthStyles - 1)) * SPRITE_W;
	ctx.drawImage(images.bbyMOUTH, mouthSourceX, 0, SPRITE_W, SPRITE_H, baseOffsetX, baseOffsetY, SPRITE_W, SPRITE_H);
	ctx.filter = 'none';
	ctx.restore();
};

onMounted(async () => {
	if (!bbyCanvas.value) return;
	ctx = bbyCanvas.value.getContext('2d');
	try {
		const [body, cheeks, eyes, mouth] = await Promise.all([ loadImage(bbyBodyUrl), loadImage(bbyCheeksUrl), loadImage(bbyEyesUrl), loadImage(bbyMouthUrl) ]);
		images.bbyBODY = body; images.bbyCHEEKS = cheeks; images.bbyEYES = eyes; images.bbyMOUTH = mouth;
		fitCanvas();
		draw();
		const ro = new ResizeObserver(() => { fitCanvas(); draw(); });
		ro.observe(bbyCanvas.value.parentElement!);
		window.addEventListener('resize', () => { fitCanvas(); draw(); });
	} catch (error) {
		console.error("failed to load bby sprites:", error);
	}
});

// UPDATED: Also watch the paint data to trigger a redraw
watch([bbyState, currentColour, tintStrength, paintOverlayData], () => {
	fitCanvas();
	draw();
}, { deep: true });
</script>