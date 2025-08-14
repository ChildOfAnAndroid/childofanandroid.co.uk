<!-- src/components/colourScope.vue -->
<template>
  <div class="scope-box">
    <label class="scope-label">SCOPE</label>
    <div ref="scopeDisplay" class="scope-display" :class="{ minimized: props.isScopeMinimized }" title="Next brush colours">
      <canvas ref="scopeCanvas" class="scope-layer"></canvas>
    </div>
    <div class="scope-controls">
      <button class="action mini" @click="decrementScope" title="Show fewer colours">-</button>
      <button class="action mini" @click="incrementScope" title="Show more colours">+</button>
      <button
        class="action mini"
        @click="emit('update:isScopeMinimized', !props.isScopeMinimized)"
        :title="props.isScopeMinimized ? 'Expand' : 'Minimize'"
      >{{ props.isScopeMinimized ? '▢' : '≡' }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { throttle } from 'lodash';
import { computeNextColours } from '@/utils/colourEngine';
import type { EQType, RgbColor } from '@/utils/colourEngine';

const props = defineProps<{
  scopeLength: number;
  isScopeMinimized: boolean;
  hexColor: string;
  tempo: number;
  activeEqs: Set<EQType>;
  userColorInfluence: number;
  bbyInfluence: number;
  redInfluence: number;
  greenInfluence: number;
  blueInfluence: number;
  rainbowInfluence: number;
  userColour: RgbColor;
  currentColour: RgbColor;
}>();

const emit = defineEmits<{
  (e: 'update:scopeLength', v: number): void;
  (e: 'update:isScopeMinimized', v: boolean): void;
}>();

const scopeCanvas = ref<HTMLCanvasElement | null>(null);
const scopeDisplay = ref<HTMLDivElement | null>(null);

function getMaxSteps() {
  if (!scopeDisplay.value) return 1;
  // Aim for chunky rows
  const minRow = 16; // px
  return Math.max(1, Math.floor(scopeDisplay.value.clientHeight / minRow));
}
function decrementScope() { emit('update:scopeLength', Math.max(1, props.scopeLength - 1)); }
function incrementScope() { emit('update:scopeLength', Math.min(props.scopeLength + 1, getMaxSteps())); }

// rounded-rect helper
function rr(ctx: CanvasRenderingContext2D, x:number, y:number, w:number, h:number, r:number){
  const rad = Math.min(r, h*0.5, w*0.5);
  ctx.beginPath();
  ctx.moveTo(x+rad, y);
  ctx.arcTo(x+w, y,   x+w, y+h, rad);
  ctx.arcTo(x+w, y+h, x,   y+h, rad);
  ctx.arcTo(x,   y+h, x,   y,   rad);
  ctx.arcTo(x,   y,   x+w, y,   rad);
  ctx.closePath();
}

const draw = throttle(() => {
  if (!scopeCanvas.value || !scopeDisplay.value) return;

  // 1) Build colour steps with the SAME math as the brush
  const maxSteps = getMaxSteps();
  if (props.scopeLength > maxSteps) emit('update:scopeLength', maxSteps);
  const TOTAL = Math.max(1, Math.min(Math.round(props.scopeLength), maxSteps));

  const colours = computeNextColours(TOTAL, props.hexColor, {
    activeEqs: props.activeEqs,
    userColour: props.userColour,
    bbyColour: props.currentColour,
    tempo: props.tempo,
    userColorInfluence: props.userColorInfluence,
    bbyInfluence: props.bbyInfluence,
    redInfluence: props.redInfluence,
    greenInfluence: props.greenInfluence,
    blueInfluence: props.blueInfluence,
    rainbowInfluence: props.rainbowInfluence,
    // keep these in lock-step with the brush engine:
    baseStep: 0.05,
    rainbowHueStep: 20,
  });

  // 2) Render thicc “radio display” bars
  const canvas = scopeCanvas.value;
  const display = scopeDisplay.value;
  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(1, display.clientWidth);
  const height = Math.max(1, display.clientHeight);

  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  const ctx = canvas.getContext('2d'); if (!ctx) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.imageSmoothingEnabled = false;

  // backglass
  ctx.clearRect(0, 0, width, height);
  const glass = ctx.createLinearGradient(0, 0, 0, height);
  glass.addColorStop(0,   'rgba(255,255,255,0.03)');
  glass.addColorStop(0.1, 'rgba(255,255,255,0.06)');
  glass.addColorStop(0.5, 'rgba(0,0,0,0.00)');
  glass.addColorStop(1,   'rgba(0,0,0,0.20)');
  ctx.fillStyle = 'rgba(0,0,0,0.85)';
  ctx.fillRect(0, 0, width, height);
  ctx.globalCompositeOperation = 'soft-light';
  ctx.fillStyle = glass;
  ctx.fillRect(0, 0, width, height);
  ctx.globalCompositeOperation = 'source-over';

  // geometry
  const pitch = height / colours.length;
  const gap   = Math.max(2, Math.floor(pitch * 0.2));
  const rowH  = Math.max(10, pitch - gap);
  const padX  = Math.round(Math.min(8, width * 0.18));
  const rowW  = Math.max(8, width - padX * 2);
  const rad   = Math.min(6, Math.floor(rowH * 0.35));

  for (let i = 0; i < colours.length; i++) {
    const { r, g, b } = colours[i];
    const y = i * pitch + gap / 2;

    // base
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    rr(ctx, padX, y, rowW, rowH, rad);
    ctx.fill();

    // glow
    ctx.save();
    ctx.shadowColor = `rgba(${r},${g},${b},0.65)`;
    ctx.shadowBlur = 10;
    ctx.fillStyle = `rgba(${r},${g},${b},0.45)`;
    rr(ctx, padX, y, rowW, rowH, rad);
    ctx.fill();
    ctx.restore();

    // core
    ctx.fillStyle = `rgb(${r},${g},${b})`;
    rr(ctx, padX, y, rowW, rowH, rad);
    ctx.fill();

    // bevel
    const bevel = ctx.createLinearGradient(0, y, 0, y + rowH);
    bevel.addColorStop(0.0, 'rgba(255,255,255,0.22)');
    bevel.addColorStop(0.25,'rgba(255,255,255,0.10)');
    bevel.addColorStop(0.5, 'rgba(255,255,255,0.04)');
    bevel.addColorStop(0.75,'rgba(0,0,0,0.15)');
    bevel.addColorStop(1.0, 'rgba(0,0,0,0.25)');
    ctx.globalCompositeOperation = 'overlay';
    rr(ctx, padX, y, rowW, rowH, rad);
    ctx.fillStyle = bevel;
    ctx.fill();
    ctx.globalCompositeOperation = 'source-over';

    // edge
    ctx.strokeStyle = 'rgba(0,0,0,0.55)';
    ctx.lineWidth = 1;
    rr(ctx, padX + 0.5, y + 0.5, rowW - 1, rowH - 1, Math.max(0, rad - 1));
    ctx.stroke();
  }

  // scanlines
  ctx.fillStyle = 'rgba(0,0,0,0.06)';
  for (let sy = 0; sy < height; sy += 2) ctx.fillRect(0, sy, width, 1);
}, 50);

// Re-draw when inputs change.
// NOTE: Sets aren’t deeply reactive → convert to a string signature.
watch(
  () => [
    props.hexColor,
    props.tempo,
    Array.from(props.activeEqs.values()).sort().join(','), // <- track membership
    props.userColorInfluence,
    props.bbyInfluence,
    props.redInfluence,
    props.greenInfluence,
    props.blueInfluence,
    props.rainbowInfluence,
    props.userColour.r, props.userColour.g, props.userColour.b,
    props.currentColour.r, props.currentColour.g, props.currentColour.b,
    props.isScopeMinimized,
    props.scopeLength,
  ],
  () => draw(),
  { deep: false, immediate: true }
);

onMounted(() => {
  if (scopeDisplay.value) new ResizeObserver(() => draw()).observe(scopeDisplay.value);
  draw();
});
</script>

<style scoped>
.scope-box{
  flex: 0 0 auto;
  width: 140px;
  height: 100%;
  background: var(--bby-colour-black);
  padding: var(--spacing);
  border: var(--border);
  border-radius: var(--border-radius);
  display: flex; flex-direction: column; align-items: center;
  gap: calc(var(--spacing)/2);
}
.scope-label { font-size: 0.7rem; font-weight: bold; color: rgba(255,255,255,0.7); }

.scope-display{
  flex: 1 1 auto;
  width: 84px;
  height: 100%;
  border-radius: 8px;
  background:
    radial-gradient(120% 140% at 50% 0%, rgba(255,255,255,0.08), rgba(255,255,255,0) 50%),
    linear-gradient(180deg, rgba(0,0,0,0.95), rgba(0,0,0,0.85));
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow:
    inset 0 2px 8px rgba(255,255,255,0.05),
    inset 0 -4px 14px rgba(0,0,0,0.6), 
    0 4px 18px rgba(0,0,0,0.45);
  overflow: hidden;
}
.scope-display.minimized{ width: 0; border-width: 0; }
.scope-layer{ width:100%; height:100%; image-rendering: pixelated; image-rendering: crisp-edges; }

.scope-controls { display: flex; gap: .25rem; }
.action.mini{ padding:2px 6px; font-size:.65rem; }
</style>
