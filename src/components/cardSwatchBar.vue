<script setup lang="ts">
import { getPrimaryStampUrl, sortCardsByColour, type StampCard } from '@/utils/cards';
import { computed } from 'vue';

const props = defineProps<{
  cards: StampCard[];
  selectedCardLabel: string | null;
  label: string;
}>();

const emit = defineEmits<{ (e: 'select', label: string): void }>();

// sorted copy of the cards prop
const sortedCards = computed(() => sortCardsByColour(props.cards));

function stampSrc(card: StampCard): string {
  const url = getPrimaryStampUrl(card);
  if (!url) {
    console.warn('[cardSwatchBar] Missing stamp for card:', card.label);
    return '';
  }
  return url;
}
</script>

<template>
  <div class="grp">
    <label class="section">{{ label }}</label>
    <div class="card-swatch-bar">
      <button
        v-for="card in sortedCards"
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