<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
  <div class="fader-box">
    <label class="fader-label">{{ label }}</label>
    <div class="fader-value">{{ formatted }}</div>
    <input
      type="range"
      class="fader"
      :min="min"
      :max="max"
      :value="modelValue"
      @input="onInput"
      @dblclick="reset"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{modelValue: number; min?: number; max?: number; label?: string; defaultValue?: number;}>(), {
  min: 30,
  max: 200,
  label: 'TEMPO',
  defaultValue: 120,
});

const emit = defineEmits<{ (e: 'update:modelValue', value: number): void }>();

const formatted = computed(() => (Math.round(props.modelValue * 100) / 100).toFixed(2));

function onInput(e: Event) {
  const target = e.target as HTMLInputElement;
  emit('update:modelValue', Number(target.value));
}

function reset() {
  emit('update:modelValue', props.defaultValue);
}
</script>

<style scoped>
/* styles for fader come from global component styles */
</style>