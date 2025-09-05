<template>
  <div class="test-canvas-controls">
    <label>Size</label>
    <input
      type="range"
      min="25"
      max="100"
      :value="size"
      @input="onSizeInput"
      class="size-slider"
    />

    <label>Resolution</label>
    <div class="res-wrap">
      <!-- Big wide slider -->
      <input
        type="range"
        :min="RES_MIN"
        :max="RES_MAX"
        step="1"
        v-model.number="resLocal"
        @input="onResInput"
        class="res-slider"
      />

      <!-- Precise numeric entry -->
      <input
        class="res-number"
        type="number"
        :min="RES_MIN"
        :max="RES_MAX"
        step="1"
        v-model.number="resLocal"
        @change="onResInput"
      />

      <!-- Quick nudge buttons -->
      <div class="nudge">
        <button class="pill" @click="nudge(-8)" title="-8">−8</button>
        <button class="pill" @click="nudge(-1)" title="-1">−1</button>
        <button class="pill" @click="nudge(1)" title="+1">+1</button>
        <button class="pill" @click="nudge(8)" title="+8">+8</button>
      </div>

      <!-- Optional presets (power-of-two etc.) -->
      <details class="presets">
        <summary>Presets</summary>
        <div class="preset-grid">
          <button
            v-for="p in PRESETS"
            :key="p"
            class="preset"
            @click.prevent="setPreset(p)"
          >
            {{ p }}×{{ p }}
          </button>
        </div>
      </details>
    </div>

    <button
      class="action"
      title="Fill the canvas with the current colour"
      @click="$emit('fill')"
    >FILL</button>
    <button
      class="action danger"
      title="Clear the canvas"
      @click="$emit('clear')"
    >CLEAR</button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { clamp } from '@/utils/math';

const { size, resolution } = defineProps<{ size: number; resolution: number }>();
const emit = defineEmits<{
  (e: 'update:size', value: number): void;
  (e: 'update:resolution', value: number): void;
  (e: 'clear'): void;
  (e: 'fill'): void;
}>();

// Bounds (tweak as you like)
const RES_MIN = 2;
const RES_MAX = 8192;
const PRESETS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16, 18, 32, 64, 69, 128, 256, 384, 420, 512, 768, 1024, 1536, 2048, 3072, 4096];
const resLocal = ref<number>(resolution);

// keep local in sync if parent changes resolution externally
watch(() => resolution, (v) => { if (v !== resLocal.value) resLocal.value = v; });

function clampResolution(n: number, lo = RES_MIN, hi = RES_MAX) {
  return clamp(Math.round(n), lo, hi);
}

function onSizeInput(e: Event) {
  const target = e.target as HTMLInputElement;
  emit('update:size', Number(target.value));
}

function onResInput() {
  const val = clampResolution(resLocal.value);
  resLocal.value = val;
  emit('update:resolution', val);
}

function nudge(delta: number) {
  resLocal.value = clampResolution(resLocal.value + delta);
  onResInput();
}

function setPreset(p: number) {
  resLocal.value = clampResolution(p);
  onResInput();
}
</script>

<style scoped>
.test-canvas-controls {
  display: flex;
  align-items: center;
  gap: calc(var(--spacing) * .5);
  flex: 1;
  flex-wrap: wrap;
  min-width: 0; /* allow children to shrink */
}

.test-canvas-controls > label {
  font-size: var(--small-font-size);
  white-space: nowrap;
  opacity: .8;
}

.size-slider {
  flex: 1 1 140px;
  min-width: 120px;
}

.res-wrap {
  display: grid;
  align-items: center;
  grid-template-columns: 1fr auto auto;
  grid-template-areas:
    "slider number nudge"
    "presets presets presets";
  gap: .5rem;
  flex: 2 1 320px;
  min-width: 240px;
}

.res-slider {
  grid-area: slider;
  width: 100%;
}

.res-number {
  grid-area: number;
  width: 88px;
  padding: .3rem .5rem;
  font-variant-numeric: tabular-nums;
}

.nudge {
  grid-area: nudge;
  display: flex;
  gap: .25rem;
}

.pill {
  padding: .2rem .5rem;
  border: 1px solid var(--border-color, #444);
  background: var(--button-bg, #222);
  border-radius: 999px;
  font-size: 0.85rem;
  line-height: 1.1;
}

.presets {
  grid-area: presets;
}

.preset-grid {
  margin-top: .5rem;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: .25rem;
}

.preset {
  padding: .25rem .35rem;
  border: 1px solid var(--border-color, #444);
  background: var(--button-bg, #1b1b1b);
  border-radius: .35rem;
  font-size: .8rem;
}

@media (max-width: 800px) {
  .res-wrap {
    grid-template-columns: 1fr auto;
    grid-template-areas:
      "slider slider"
      "number nudge"
      "presets presets";
  }
}
</style>
