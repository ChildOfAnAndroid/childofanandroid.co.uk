<!-- 
CHARIS CAT // CHILD OF AN ANDROID - 2025 
src/pages/bbyTest.vue 
-->

<template>
  <div class="page-container">
    <div class="left-column">
      <div class="controls-panel">
        <div class="input-group button-row">
          <input id="color-picker" type="color" v-model="colorInput" @input="updateTargetColor" class="color-input" />
          <button @click="randomiseColor" class="action-button">colour</button>
          <button @click="requestStateChange({ jumping: true })" class="action-button">jump</button>
          <button @click="requestStateChange({ cheeks_on: !bbyState.cheeks_on })" class="action-button">blush</button>
          <button @click="requestStateChange({ stretch_up: true })" class="action-button">stretch</button>
          <button @click="clearBubbles" class="action-button">pop</button>
        </div>
      </div>
    </div>
    <div class="right-column">
      <div class="bby-stage">
        <bbySprite />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { bbyUse } from '@/composables/bbyUse.ts';
import bbySprite from '@/components/bbySprite.vue';

const { bbyState, requestStateChange, clearBubbles } = bbyUse();
const colorInput = ref('#85efee');
const updateTargetColor = () => {
  const hex = colorInput.value.replace('#', '');
  if (hex.length === 6) {
    const R = parseInt(hex.substring(0, 2), 16);
    const G = parseInt(hex.substring(2, 4), 16);
    const B = parseInt(hex.substring(4, 6), 16);
    requestStateChange({ R, G, B });
  }
};
const randomiseColor = () => {
  const R = Math.floor(Math.random() * 256);
  const G = Math.floor(Math.random() * 256);
  const B = Math.floor(Math.random() * 256);
  colorInput.value = `#${[R, G, B].map(x => x.toString(16).padStart(2, '0')).join('')}`;
  requestStateChange({ R, G, B });
};
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: var(--full-height);
  padding: var(--paddding);
  box-sizing: border-box;
  position: relative;
}
</style>