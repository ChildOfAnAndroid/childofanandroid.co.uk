<template>
  <div class="grp">
    <div class="section-header">
      <label class="section">Colour Scope</label>
      <div class="scope-controls">
        <button
          class="action mini"
          @click="$emit('update:scopeLength', Math.max(1, props.scopeLength - 1))"
          title="Show fewer colours"
        >
          -
        </button>
        <button
          class="action mini"
          @click="$emit('update:scopeLength', props.scopeLength + 1)"
          title="Show more colours"
        >
          +
        </button>
        <button
          class="action mini"
          @click="$emit('update:isScopeMinimized', !props.isScopeMinimized)"
          :title="props.isScopeMinimized ? 'Expand' : 'Minimize'"
        >
          {{ props.isScopeMinimized ? '▢' : '≡' }}
        </button>
      </div>
    </div>
    <div class="scope-display" :class="{ minimized: props.isScopeMinimized }">
      <canvas ref="scopeCanvas" class="scope-layer"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { throttle } from 'lodash';

type EQType = 'user' | 'bby' | 'red' | 'green' | 'blue' | 'rainbow';
type RgbColor = { r: number; g: number; b: number };

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

const scopeCanvas = ref<HTMLCanvasElement | null>(null);

function clampByte(x: number) {
  return Math.max(0, Math.min(255, Math.round(x)));
}
function rgbToHsv(r: number, g: number, b: number) {
  r /= 255; g /= 255; b /= 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d) {
    if (mx === r) h = ((g - b) / d) % 6;
    else if (mx === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
    if (h < 0) h += 360;
  }
  const s = mx === 0 ? 0 : d / mx;
  return { h, s, v: mx };
}
function hsvToRgb(h: number, s: number, v: number) {
  const c = v * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = v - c;
  let r = 0, g = 0, b = 0;
  h %= 360; if (h < 0) h += 360;
  if (0 <= h && h < 60) [r, g, b] = [c, x, 0];
  else if (60 <= h && h < 120) [r, g, b] = [x, c, 0];
  else if (120 <= h && h < 180) [r, g, b] = [0, c, x];
  else if (180 <= h && h < 240) [r, g, b] = [0, x, c];
  else if (240 <= h && h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];
  return {
    r: clampByte((r + m) * 255),
    g: clampByte((g + m) * 255),
    b: clampByte((b + m) * 255)
  };
}
function hexToRGB(hx: string): RgbColor {
  const h = hx.replace('#', '');
  return { r: parseInt(h.slice(0, 2), 16), g: parseInt(h.slice(2, 4), 16), b: parseInt(h.slice(4, 6), 16) };
}

const updateColorScope = throttle(() => {
  if (!scopeCanvas.value) return;
  const TOTAL_STEPS = Math.max(1, Math.round(props.scopeLength));
  const colors: RgbColor[] = [];
  let c = hexToRGB(props.hexColor);

  for (let i = 0; i < TOTAL_STEPS; i++) {
    let hsv = rgbToHsv(c.r, c.g, c.b);
    const speed = (props.tempo / 100) * 0.002;
    const rVec = { r: 255 - c.r, g: -c.g, b: -c.b };
    const gVec = { r: -c.r, g: 255 - c.g, b: -c.b };
    const bVec = { r: -c.r, g: -c.g, b: 255 - c.b };
    const uVec = { r: props.userColour.r - c.r, g: props.userColour.g - c.g, b: props.userColour.b - c.b };
    const bbyVec = { r: props.currentColour.r - c.r, g: props.currentColour.g - c.g, b: props.currentColour.b - c.b };
    const rainbowVecTarget = hsvToRgb((hsv.h + 20) % 360, hsv.s, hsv.v);
    const rainbowVec = { r: rainbowVecTarget.r - c.r, g: rainbowVecTarget.g - c.g, b: rainbowVecTarget.b - c.b };
    let dR = 0, dG = 0, dB = 0;
    if (props.activeEqs.has('user')) { dR += uVec.r * (props.userColorInfluence / 100); dG += uVec.g * (props.userColorInfluence / 100); dB += uVec.b * (props.userColorInfluence / 100); }
    if (props.activeEqs.has('bby')) { dR += bbyVec.r * (props.bbyInfluence / 100); dG += bbyVec.g * (props.bbyInfluence / 100); dB += bbyVec.b * (props.bbyInfluence / 100); }
    if (props.activeEqs.has('red')) { dR += rVec.r * (props.redInfluence / 100); dG += rVec.g * (props.redInfluence / 100); dB += rVec.b * (props.redInfluence / 100); }
    if (props.activeEqs.has('green')) { dR += gVec.r * (props.greenInfluence / 100); dG += gVec.g * (props.greenInfluence / 100); dB += gVec.b * (props.greenInfluence / 100); }
    if (props.activeEqs.has('blue')) { dR += bVec.r * (props.blueInfluence / 100); dG += bVec.g * (props.blueInfluence / 100); dB += bVec.b * (props.blueInfluence / 100); }
    if (props.activeEqs.has('rainbow')) { dR += rainbowVec.r * (props.rainbowInfluence / 100); dG += rainbowVec.g * (props.rainbowInfluence / 100); dB += rainbowVec.b * (props.rainbowInfluence / 100); }
    c.r += dR * speed; c.g += dG * speed; c.b += dB * speed;
    c = { r: clampByte(c.r), g: clampByte(c.g), b: clampByte(c.b) };
    colors.push(c);
  }

  const canvas = scopeCanvas.value;
  const ctx = canvas.getContext('2d'); if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = canvas.clientWidth * dpr;
  canvas.height = canvas.clientHeight * dpr;
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const numPixels = colors.length;
  const pixelHeight = canvas.height / numPixels;
  for (let y = 0; y < numPixels; y++) {
    const color = colors[y];
    ctx.fillStyle = `rgb(${color.r},${color.g},${color.b})`;
    ctx.fillRect(0, y * pixelHeight, canvas.width, pixelHeight);
  }
}, 50);

watch(
  () => [
    props.hexColor,
    props.tempo,
    props.activeEqs,
    props.userColorInfluence,
    props.bbyInfluence,
    props.redInfluence,
    props.greenInfluence,
    props.blueInfluence,
    props.rainbowInfluence,
    props.userColour,
    props.currentColour,
    props.isScopeMinimized,
    props.scopeLength
  ],
  updateColorScope,
  { deep: true, immediate: true }
);

onMounted(() => {
  new ResizeObserver(updateColorScope).observe(scopeCanvas.value!);
  updateColorScope();
});
</script>

<style scoped>
.section-header { display: flex; justify-content: center; align-items: center; position: relative; gap: .5rem; }
.scope-controls { position: absolute; right: .25rem; top: 50%; transform: translateY(-50%); display: flex; gap: .25rem; }
.scope-display { max-height: 100%; width: 16px; height: 100px; border: var(--border); border-radius: var(--border-radius); background: var(--bby-colour-black); overflow: hidden; margin: 0 auto; }
.scope-display.minimized { width: 0; height: 0; border-width: 0; }
.scope-layer { width: 100%; height: 100%; image-rendering: crisp-edges; image-rendering: pixelated; }
</style>