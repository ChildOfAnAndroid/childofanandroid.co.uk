<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
  <div class="page-container">
    <bubbleGraveyard />
    <div class="book-gallery">
      <div v-for="(card, idx) in cards" :key="idx" class="book-card">
        <img :src="card.url" alt="bbybook image" />
        <div class="fact">{{ card.fact }}</div>
        <div class="authors">
          <span v-if="card.imageAuthor">img: {{ card.imageAuthor }}</span>
          <span v-if="card.factAuthor">fact: {{ card.factAuthor }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import bubbleGraveyard from '@/components/bubbleGraveyard.vue';
import { bbyUse } from '@/composables/bbyUse.ts';

const { bbyFacts, fetchTestGridGallery } = bbyUse();

interface GalleryItem { url: string; author?: string; label?: string }
const images = ref<GalleryItem[]>([]);

const cards = computed(() => {
  return images.value
    .filter((img): img is GalleryItem & { label: string } => !!img.label && !!bbyFacts.value[img.label])
    .map(img => ({
      url: img.url,
      fact: bbyFacts.value[img.label].value,
      factAuthor: bbyFacts.value[img.label].author,
      imageAuthor: img.author,
    }));
});

onMounted(async () => {
  images.value = await fetchTestGridGallery();
});
</script>

<style scoped>
.page-container{display:flex;flex-direction:column;width:100%;height:var(--full-height);padding:var(--padding);box-sizing:border-box;overflow-y:auto;}
.book-gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:var(--spacing);width:100%;}
.book-card{display:flex;flex-direction:column;align-items:center;gap:4px;padding:var(--padding);border:var(--border);border-radius:var(--border-radius);background:var(--panel-colour);}
.book-card img{width:100%;image-rendering:pixelated;border:var(--border);border-radius:var(--border-radius);}
.fact{text-align:center;font-size:var(--small-font-size);}
.authors{font-size:var(--small-font-size);opacity:.8;display:flex;flex-direction:column;align-items:center;}
</style>