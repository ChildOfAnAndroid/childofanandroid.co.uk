<template>
  <div class="test-canvas-controls">
    <label>Size</label>
    <input
      type="range"
      min="25"
      max="100"
      :value="size"
      @input="onInput"
      class="size-slider"
    />
    <button class="action danger" @click="$emit('clear')">Clear</button>
  </div>
</template>

<script setup lang="ts">
const { size } = defineProps<{ size: number }>();
const emit = defineEmits<{
  (e: 'update:size', value: number): void;
  (e: 'clear'): void;
}>();

function onInput(e: Event) {
  const target = e.target as HTMLInputElement;
  emit('update:size', Number(target.value));
}
</script>

<style scoped>
.test-canvas-controls { display: flex; align-items: center; gap: var(--spacing); width: 100%; max-width: 400px; }
.test-canvas-controls > label { font-size: var(--small-font-size); }
.test-canvas-controls > .size-slider { flex-grow: 1; }
</style>
