<!-- 
CHARIS CAT // CHILD OF AN ANDROID - 2025 
src/pages/bbyIndex.vue 
-->

<template>
  <!-- padding and boundaries -->
  <div class="page-container">
    <div class="bubble-graveyard-global">
      <div
        v-for="ghost in bbyState.graveyardBubbles"
        :key="ghost.id"
        class="ghost-bubble"
        :style="{
          top: ghost.startY,
          left: ghost.startX,
          width: ghost.width,
          '--dest-x': ghost.ghostX,
          '--dest-y': ghost.ghostY,
          '--dest-r': ghost.ghostR,
          '--ghost-duration': ghost.duration,
          '--ghost-easing': ghost.easing,
          '--ghost-delay': ghost.delay,
          '--ghost-opacity1': ghost.ghostOpacity1,
          '--ghost-opacity2': ghost.ghostOpacity2,
          '--ghost-blur': ghost.ghostBlur,
          'backgroundColor': ghost.bgColour,
          'borderColor': ghost.borderColour,
        }"
      >
        <span v-html="ghost.text"></span>
        <strong class="bubble-author"> {{ ghost.author }}</strong>
      </div>
    </div>

    <!-- two column layout -->
    <div class="left-column">
    </div>
    
    <div class="big-bby">
      <div class="bby-stage">
        <bbySprite />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { bbyUse } from '@/composables/bbyUse.ts';
import bbySprite from '@/components/bbySprite.vue';

const { bbyState } = bbyUse();

</script>

<style scoped>
/* scoped styles to prevent them from leaking */
.page-container {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: var(--full-height);
  padding: var(--padding);
  box-sizing: border-box;
  position: relative;
}
</style>