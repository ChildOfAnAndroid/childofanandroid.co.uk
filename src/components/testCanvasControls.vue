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
    <select :value="resolution" @change="onResolutionChange" class="res-select">
      <option v-for="r in resolutions" :key="r" :value="r">{{ r }}x{{ r }}</option>
    </select>
    <button class="action danger" @click="$emit('clear')">Clear</button>
  </div>
</template>

<script setup lang="ts">
const { size, resolution } = defineProps<{ size: number; resolution: number }>();
const emit = defineEmits<{
  (e: 'update:size', value: number): void;
  (e: 'update:resolution', value: number): void;
  (e: 'clear'): void;
}>();

const resolutions = [2, 4, 6, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 69, 420, 42069];

function onSizeInput(e: Event) {
  const target = e.target as HTMLInputElement;
  emit('update:size', Number(target.value));
}

function onResolutionChange(e: Event) {
  const target = e.target as HTMLSelectElement;
  emit('update:resolution', Number(target.value));
}
</script>

<style scoped>
.test-canvas-controls { display: flex; align-items: center; gap: var(--spacing); width: 100%; max-width: 400px; flex-wrap: wrap; }
.test-canvas-controls > label { font-size: var(--small-font-size); }
.test-canvas-controls > .size-slider { flex-grow: 1; }
.test-canvas-controls > .res-select { min-width: 80px; }
</style>
