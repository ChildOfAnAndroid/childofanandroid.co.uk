<template>
	<div class="lab-wrap">
		<div ref="stack" class="stack">
			<BbySprite ref="spriteComp" /> 
			<canvas
				ref="overlay"
				class="overlay"
				@pointerdown="onDown"
				@pointermove="onPointerMove"
				@pointerup="onUp"
				@pointerleave="onPointerLeave"
			></canvas>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, defineProps, defineExpose, watch, defineEmits } from 'vue';
import { throttle } from 'lodash';
import BbySprite from '@/components/bbySprite.vue';
import { bbyUse } from '@/composables/bbyUse.ts';

const props = defineProps<{
	hexColor: string;
	mode: 'paint' | 'erase' | 'eyedropper';
	brushSize: number;
}>();

const emit = defineEmits(['color-picked']);

const SPRITE_W = 64
const SPRITE_H = 64

defineExpose({ clearOverlay });

const { bbyState, sendBbyPaintColour, paintOverlayData, sendPixelUpdate } = bbyUse(); 

const throttledReactionUpdate = throttle((r: number, g: number, b: number) => {
	sendBbyPaintColour(r, g, b);
}, 300);

let pixelUpdateBatch: {x:number, y:number, r:number, g:number, b:number, a:number}[] = [];
const throttledSendBatch = throttle(() => {
	if (pixelUpdateBatch.length > 0) {
		sendPixelUpdate(pixelUpdateBatch);
		pixelUpdateBatch = [];
	}
}, 100);

const highlightedPixel = ref<{x: number, y: number} | null>(null);
let isDown = false;
let octx: CanvasRenderingContext2D|null = null;
const spriteComp = ref<InstanceType<typeof BbySprite>|null>(null);
const overlay = ref<HTMLCanvasElement|null>(null);
let ro: ResizeObserver | null = null;
const dpr = window.devicePixelRatio || 1;

function clearOverlay() {
	if (!paintOverlayData.value) return;

	const pixelsToClear = [];
	const data = paintOverlayData.value.data;
	for (let i = 0; i < data.length; i += 4) {
			data[i] = 0;
			data[i+1] = 0;
			data[i+2] = 0;
			data[i+3] = 0;
	}
	for (let y = 0; y < SPRITE_H; y++) {
		for (let x = 0; x < SPRITE_W; x++) {
			pixelsToClear.push({ x, y, r: 0, g: 0, b: 0, a: 0 });
		}
	}
	
	paintOverlayData.value = new ImageData(data, SPRITE_W, SPRITE_H);
	sendPixelUpdate(pixelsToClear);
}

function setPixel(x:number, y:number, r:number, g:number, b:number, a:number) {
	if (!paintOverlayData.value) return;
	if (x < 0 || y < 0 || x >= SPRITE_W || y >= SPRITE_H) return; // Bounds check

	const i = (y * SPRITE_W + x) * 4;
	const d = paintOverlayData.value.data;
	if (d[i] === r && d[i+1] === g && d[i+2] === b && d[i+3] === a) return;

	d[i] = r; d[i+1] = g; d[i+2] = b; d[i+3] = a;
	
	pixelUpdateBatch.push({ x, y, r, g, b, a });
	throttledSendBatch();
}

function paint(e: PointerEvent) {
	const p = cssToPixel(e.clientX, e.clientY);
	if (!p) return;

	if (props.mode === 'eyedropper') {
		if (!paintOverlayData.value) return;
		const i = (p.y * SPRITE_W + p.x) * 4;
		const d = paintOverlayData.value.data;
		if (d[i+3] > 0) {
			const pickedHex = `#${[d[i], d[i+1], d[i+2]].map(x => x.toString(16).padStart(2, '0')).join('')}`;
			emit('color-picked', pickedHex);
		}
		return;
	}

	const offset = Math.floor((props.brushSize - 1) / 2);
	for (let dy = -offset; dy <= offset; dy++) {
		for (let dx = -offset; dx <= offset; dx++) {
			const targetX = p.x + dx;
			const targetY = p.y + dy;
			
			if (props.mode === 'erase') {
				setPixel(targetX, targetY, 0, 0, 0, 0);
			} else {
				const { r,g,b } = hexToRGB(props.hexColor);
				setPixel(targetX, targetY, r, g, b, 255);
				throttledReactionUpdate(r, g, b);
			}
		}
	}
}

function getBabyCanvas(): HTMLCanvasElement | null {
	const el = spriteComp.value?.$el as HTMLElement | undefined;
	if (!el) return null;
	return (el.tagName === 'CANVAS' ? (el as HTMLCanvasElement) : null);
}
function setupOverlay() {
	const baby = getBabyCanvas();
	if (!baby || !overlay.value) return;
	const cssW = baby.clientWidth, cssH = baby.clientHeight;
	overlay.value.style.width = cssW + 'px';
	overlay.value.style.height = cssH + 'px';
	overlay.value.width	= Math.round(cssW * dpr);
	overlay.value.height = Math.round(cssH * dpr);
	octx = overlay.value.getContext('2d', { alpha: true });
	if (!octx) throw new Error('overlay 2D ctx failed');
	octx.imageSmoothingEnabled = false;
	redrawOverlay();
}
function redrawOverlay() {
	const baby = getBabyCanvas();
	if (!octx || !overlay.value || !baby) return;
	const cssW = baby.clientWidth, cssH = baby.clientHeight;
	const s = Math.min(cssW / SPRITE_W, cssH / SPRITE_H) || 1;
	octx.setTransform(s * dpr, 0, 0, s * dpr, 0, 0);
	octx.clearRect(-1e5, -1e5, 2e5, 2e5);
	
	if (highlightedPixel.value) {
		const { x, y } = highlightedPixel.value;
		const stretch_x = SPRITE_W + (bbyState.stretch_left ? 1 : 0) + (bbyState.stretch_right ? 1 : 0) - (bbyState.squish_left ? 1 : 0)	- (bbyState.squish_right ? 1 : 0);
		const stretch_y = SPRITE_H + (bbyState.stretch_up ? 1 : 0) + (bbyState.stretch_down ? 1 : 0) - (bbyState.squish_up ? 1 : 0)	- (bbyState.squish_down ? 1 : 0);
		const jumpset = bbyState.jumping ? -4 : 0;
		const offset_x = (SPRITE_W - stretch_x) / 2 - (bbyState.stretch_left ? 1 : 0);
		const offset_y = (SPRITE_H - stretch_y) / 2 - (bbyState.stretch_up ? 1 : 0) + jumpset;
		const offset = Math.floor((props.brushSize - 1) / 2);
		const hx = x - offset;
		const hy = y - offset;
		const hw = props.brushSize;

		octx.fillStyle = props.mode === 'eyedropper' 
			? 'rgba(255, 255, 255, 0.7)' 
			: props.mode === 'erase' ? 'rgba(255, 255, 255, 0.4)' : props.hexColor + '80';
		
		octx.fillRect(
			offset_x + hx * (stretch_x / SPRITE_W), 
			offset_y + hy * (stretch_y / SPRITE_H), 
			hw * (stretch_x / SPRITE_W), 
			hw * (stretch_y / SPRITE_H)
		);
	}
}

function cssToPixel(clientX:number, clientY:number) {
		const baby = getBabyCanvas();
		if (!baby) return null;
		const rect = baby.getBoundingClientRect();
		const lx = clientX - rect.left, ly = clientY - rect.top;
		const stretch_x = SPRITE_W + (bbyState.stretch_left ? 1 : 0) + (bbyState.stretch_right ? 1 : 0) - (bbyState.squish_left ? 1 : 0) - (bbyState.squish_right ? 1 : 0);
		const stretch_y = SPRITE_H + (bbyState.stretch_up ? 1 : 0) + (bbyState.stretch_down ? 1 : 0) - (bbyState.squish_up ? 1 : 0) - (bbyState.squish_down ? 1 : 0);
		const jumpset = bbyState.jumping ? -4 : 0;
		const offset_x = (SPRITE_W - stretch_x) / 2 - (bbyState.stretch_left ? 1 : 0);
		const offset_y = (SPRITE_H - stretch_y) / 2 - (bbyState.stretch_up ? 1 : 0) + jumpset;
		const scale_x = rect.width / SPRITE_W, scale_y = rect.height / SPRITE_H;
		const canvas_x = lx / scale_x, canvas_y = ly / scale_y;
		const px = Math.floor((canvas_x - offset_x) * (SPRITE_W / stretch_x));
		const py = Math.floor((canvas_y - offset_y) * (SPRITE_H / stretch_y));
		if (px < 0 || py < 0 || px >= SPRITE_W || py >= SPRITE_H) return null;
		return { x: px, y: py };
}
function onDown(e: PointerEvent) {
	overlay.value?.setPointerCapture(e.pointerId); isDown = true; paint(e);
}
function onPointerMove(e: PointerEvent) {
	highlightedPixel.value = cssToPixel(e.clientX, e.clientY); if (isDown) { paint(e); } redrawOverlay();
}
function onUp(e: PointerEvent) {
	try { overlay.value?.releasePointerCapture(e.pointerId); } catch {} isDown = false;
}
function onPointerLeave() {
	highlightedPixel.value = null; redrawOverlay();
}
function hexToRGB(hex:string) {
	const h = hex.replace('#','');
	return { r: parseInt(h.slice(0,2),16), g: parseInt(h.slice(2,4),16), b: parseInt(h.slice(4,6),16) };
}
onMounted(async () => {
	await nextTick();
	setupOverlay();
	const baby = getBabyCanvas();
	if (baby) { ro = new ResizeObserver(() => { setupOverlay(); redrawOverlay(); }); ro.observe(baby); }
	window.addEventListener('resize', () => { setupOverlay(); redrawOverlay(); });
});
onBeforeUnmount(() => {
	const baby = getBabyCanvas();
	if (ro && baby) ro.unobserve(baby);
	window.removeEventListener('resize', setupOverlay);
});
watch(bbyState, () => { redrawOverlay(); }, { deep: true });

</script>

<style scoped>
.lab-wrap, .stack { width: 100%; height: 100%; }
.stack { display: grid; align-items: center; justify-content: center; image-rendering: pixelated; }
.stack > :deep(canvas), .overlay { grid-area: 1 / 1; }
.overlay { touch-action: none; cursor: crosshair; }
</style>