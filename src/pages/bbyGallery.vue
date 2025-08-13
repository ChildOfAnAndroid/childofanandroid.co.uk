<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
  <div class="page-container">
    <bubbleGraveyard />
    <div class="gallery">
      <div v-for="(item, idx) in images" :key="idx" class="gallery-item">
        <img :src="item.url" alt="Test grid image" />
        <div v-if="item.author" class="author">by {{ item.author }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import bubbleGraveyard from '@/components/bubbleGraveyard.vue';
import { bbyUse } from '@/composables/bbyUse.ts';

const { fetchTestGridGallery } = bbyUse();

interface GalleryItem { url: string; author?: string; }
const images = ref<GalleryItem[]>([]);

onMounted(async () => {
  images.value = await fetchTestGridGallery();
});
</script>

<style scoped>
.page-container { display:flex; flex-direction:column; width:100%; height:var(--full-height); padding:var(--padding); box-sizing:border-box; overflow-y:auto; }
.gallery { display:grid; grid-template-columns:repeat(auto-fill,minmax(128px,1fr)); gap:var(--spacing); width:100%; }
.gallery-item { display:flex; flex-direction:column; align-items:center; gap:4px; }
.gallery-item img { width:100%; image-rendering:pixelated; border:var(--border); border-radius:var(--border-radius); }
.author { font-size:var(--small-font-size); opacity:.8; }
</style>