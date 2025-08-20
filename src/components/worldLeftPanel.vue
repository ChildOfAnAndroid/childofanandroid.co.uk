<template>
  <div class="world-left">
    <div class="vertical-panel">
      <h1 class="page-title">bbyWorld</h1>

      <div class="grp">
        <label class="section" for="board-size">board size</label>
        <div class="row3">
          <button class="action" @click="updateBoardSize(Math.max(minBoardSize, boardSize - 16))">-</button>
          <input id="board-size" type="number" :value="boardSize" @input="onBoardInput" :min="minBoardSize" step="16" />
          <button class="action" @click="updateBoardSize(Math.min(1024, boardSize + 16))">+</button>
        </div>
        <small style="opacity:.7">changing size clears the world</small>
      </div>

      <div class="grp">
        <label class="section">world</label>
        <button class="action" @click="emit('clear-world')">clear</button>
      </div>

      <div class="grp">
        <label class="section">{{ cardLabel }}</label>
        <div class="card-swatch-bar">
          <button
            v-for="card in cards"
            :key="card.label"
            class="card-swatch"
            :class="{ selected: selectedCardLabel === card.label }"
            @click="emit('select-card', card.label)"
          >
            <img :src="card.stamp_url || card.url" :alt="card.label" />
          </button>
        </div>
      </div>

      <slot name="stats" />
      <slot name="group-stats" />
      <slot name="selected-group" />
      <slot name="cell-info" />
      <slot name="cell-family" />
      <slot name="legend" />

      <div class="grp">
        <label class="section">speed ({{ ticksPerSecond }} TPS)</label>
        <div class="row2">
          <button class="action" @click="emit('slow-down')">-</button>
          <button class="action" @click="emit('speed-up')">+</button>
        </div>
      </div>

      <div class="grp">
        <label class="section">zoom</label>
        <div class="row3">
          <button class="action" @click="emit('zoom-out')">-</button>
          <div class="zoom-display">{{ (zoomFactor*100).toFixed(0) }}%</div>
          <button class="action" @click="emit('zoom-in')">+</button>
        </div>
        <button class="action" @click="emit('toggle-scope')" :class="{active: scopeActive}">scope</button>
        <button class="action" @click="emit('reset-view')">reset view</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';

interface Card { label: string; url: string; stamp_url?: string }

defineProps({
  boardSize: { type: Number, required: true },
  minBoardSize: { type: Number, default: 16 },
  cards: { type: Array as PropType<Card[]>, default: () => [] },
  selectedCardLabel: { type: String as PropType<string | null>, default: null },
  cardLabel: { type: String, default: 'select a bby to place:' },
  ticksPerSecond: { type: Number, required: true },
  zoomFactor: { type: Number, required: true },
  scopeActive: { type: Boolean, default: false }
});
const emit = defineEmits(['update:boardSize','clear-world','select-card','slow-down','speed-up','zoom-in','zoom-out','reset-view','toggle-scope']);

function updateBoardSize(val: number) {
  emit('update:boardSize', val);
}

function onBoardInput(e: Event) {
  const target = e.target as HTMLInputElement;
  updateBoardSize(Number(target.value));
}
</script>

<style scoped>
/* styles rely on existing global classes */
</style>
