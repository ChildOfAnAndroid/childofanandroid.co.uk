<template>
  <div class="grp">
    <label class="section">speed ({{ ticksPerSecond }} TPS)</label>
    <div :class="rowClass">
      <button class="action" @click="slowDown">-</button>
      <button v-if="togglePause" class="action" @click="togglePause">
        {{ isPaused ? 'play' : 'pause' }}
      </button>
      <button class="action" @click="speedUp">+</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  ticksPerSecond: number;
  speedUp: () => void;
  slowDown: () => void;
  isPaused?: boolean;
  togglePause?: () => void;
}>();

const rowClass = computed(() => props.togglePause ? 'row3' : 'row2');
</script>
