<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
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
        backgroundColor: ghost.bgColour,
        borderColor: ghost.borderColour,
      }"
    >
      <span v-html="ghost.text"></span>
      <strong class="bubble-author"> {{ ghost.author }}</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import { bbyUse } from '@/composables/bbyUse.ts';

const { bbyState } = bbyUse();
</script>