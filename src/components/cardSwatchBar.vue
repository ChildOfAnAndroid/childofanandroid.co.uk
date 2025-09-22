<template>
  <div class="grp">
    <label class="section">{{ label }}</label>
    <div class="card-swatch-bar">
      <button
        v-for="card in cards"
        :key="card.label"
        class="card-swatch"
        :class="{ selected: selectedCardLabel?.toLowerCase() === card.label.toLowerCase() }"
        @click="emit('select', card.label)"
      >
        <img :src="stampSrc(card)" :alt="card.label" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getPrimaryStampUrl, type StampCard } from '@/utils/cards';

defineProps<{
  cards: StampCard[];
  selectedCardLabel: string | null;
  label: string;
}>();
const emit = defineEmits<{ (e: 'select', label: string): void }>();

function stampSrc(card: StampCard): string {
  const url = getPrimaryStampUrl(card);
  if (!url) {
    console.warn('[cardSwatchBar] Missing stamp for card:', card.label);
    return '';
  }
  return url;
}
</script>
