<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
  <div class="fader-box">
    <label class="fader-label">{{ label }}</label>
    <input
      type="range"
      class="fader"
      :min="min"
      :max="max"
      :value="modelValue"
      @input="onInput"
      @dblclick="reset"
      orient="vertical"
    />
    <div class="fader-value">{{ formatted }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  modelValue: number;
  min?: number;
  max?: number;
  label?: string;
  defaultValue?: number;
}>(), {
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
.fader-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 80px;
  /* 
    Make the box take the full height of its parent.
    The parent element must have a defined height for this to work.
  */
  height: 100%;
}

.fader-label {
  /* Pushes the slider down a bit */
  margin-bottom: 10px;
}

.fader-value {
  /* Pushes the slider up a bit */
  margin-top: 10px;
}

.fader {
  -webkit-appearance: slider-vertical; /* For WebKit browsers */
  writing-mode: bt-lr; /* For IE */
  width: 8px;
  padding: 0 5px;
  /* 
    Remove fixed height and allow the slider to grow 
    and fill the available space in the flex container.
  */
  flex-grow: 1;
}

/* For Firefox */
input[type=range][orient=vertical] {
    writing-mode: bt-lr;
    /* Allow it to grow in Firefox as well */
    flex-grow: 1;
}
</style>