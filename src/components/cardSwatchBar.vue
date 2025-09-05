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
        <img :src="card.stamp_url || card.url" :alt="card.label" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  cards: { label: string; url: string; stamp_url?: string }[];
  selectedCardLabel: string | null;
  label: string;
}>();
const emit = defineEmits<{ (e: 'select', label: string): void }>();
</script>
