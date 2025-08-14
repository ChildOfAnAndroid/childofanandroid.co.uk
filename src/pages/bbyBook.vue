<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
  <div class="page-container">
    <bubbleGraveyard />
    <div class="book-gallery">
      <div v-for="card in cards" :key="card.factData.id" class="book-card">
        
        <div class="card-header">
          <h2 class="fact-name">{{ card.factName }}</h2>
          <div class="id-badge" title="Production Number">#{{ card.factData.id }}</div>
        </div>

        <img :src="card.url" :alt="`Image for the fact: ${card.factName}`" />

        <p class="fact-value">"{{ card.factData.value }}"</p>
        
        <div class="card-footer">
          <div class="stats-grid">
            <div class="stat-item" title="Base Value">
              <span class="stat-label">value</span>
              <span class="stat-value">ᛒ {{ formatBonus(card.factData.teach_bonus) }}</span>
            </div>
            <div class="stat-item" title="Total Allowed In World">
              <span class="stat-label">max allowed</span>
              <span class="stat-value">{{ card.factData.num_produced }}</span>
            </div>
          </div>
          <div class="authors">
            <span>art by: <strong>{{ card.imageAuthor || '???' }}</strong></span>
            <span>fact by: <strong>{{ card.factData.author }}</strong></span>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import bubbleGraveyard from '@/components/bubbleGraveyard.vue';
import { bbyUse } from '@/composables/bbyUse.ts';

const { fetchBbyBookGallery } = bbyUse();

interface BookCard {
  url: string;
  imageAuthor?: string;
  factName: string;
  factData: {
    value: string;
    author: string;
    timestamp: number;
    teach_bonus: number;
    num_produced: number;
    id: number;
  };
}
const cards = ref<BookCard[]>([]);

function formatBonus(bonus: number): string {
    if (bonus === undefined || bonus === null) return 'N/A';
    return bonus.toFixed(0); // Using toFixed(0) for a cleaner, whole number look
}

onMounted(async () => {
  cards.value = await fetchBbyBookGallery();
});
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: var(--full-height);
  padding: var(--padding);
  box-sizing: border-box;
  overflow-y: auto; /* Allows scrolling through the gallery */
}

.book-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); /* Wider cards */
  gap: var(--spacing);
  width: 100%;
}

.book-card {
  display: flex;
  flex-direction: column;
  padding: var(--padding);
  border: var(--border-width) solid var(--bby-colour-dark);
  border-radius: var(--border-radius);
  background: var(--panel-colour);
  box-shadow: var(--box-shadow);
  align-self: start;
  position: relative; /* Needed for positioning the ID badge */
  overflow: hidden; /* Keeps the badge corners neat */
}

.card-header {
  display: flex;
  justify-content: center; /* Center the title */
  align-items: center;
  padding: 4px;
  border-bottom: var(--border-width) solid var(--bby-colour-dark);
  position: relative;
}

.fact-name {
  font-size: var(--font-size);
  color: var(--accent-colour);
  margin: 0;
  text-align: center;
  font-weight: bold;
  word-break: break-word;
  line-height: 1.2; /* Tighter line height for long names */
}

.id-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: var(--bby-colour-black);
  color: var(--font-colour);
  padding: 2px 6px;
  font-size: var(--small-font-size);
  font-weight: bold;
  border-bottom-left-radius: var(--border-radius);
  border-left: var(--border);
  border-bottom: var(--border);
}

.book-card img {
  width: 100%;
  aspect-ratio: 1 / 1; /* Keep images square */
  image-rendering: pixelated;
  border-radius: calc(var(--border-radius) / 2);
  margin-top: calc(var(--spacing) / 2);
}

.fact-value {
  text-align: center;
  font-size: var(--small-font-size);
  font-style: italic;
  color: #c0c0c0; /* Slightly dimmer text for flavor */
  margin: var(--spacing) 0;
  flex-grow: 1; /* Pushes the footer down */
  min-height: 3em; /* Ensures a minimum space for text */
}

.card-footer {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
  background: var(--bby-colour-black);
  padding: var(--padding);
  border-radius: calc(var(--border-radius) / 2);
  border-top: var(--border);
}

.stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--padding);
}

.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: var(--bby-colour-dark);
    padding: 4px;
    border-radius: 4px;
}

.stat-label {
    font-size: 0.7rem;
    font-weight: bold;
    opacity: 0.7;
    text-transform: uppercase;
}

.stat-value {
    font-size: var(--font-size);
    color: var(--bby-colour-black);
    font-weight: bold;
}

.authors {
  font-size: 0.7rem;
  opacity: .8;
  display: flex;
  justify-content: space-between; /* Spreads out the authors */
  padding: 0 4px;
}

.authors strong {
    color: var(--font-colour);
    font-weight: bold;
}
</style>