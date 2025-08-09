<!-- 
CHARIS CAT // CHILD OF AN ANDROID - 2025 
src/pages/bbyIndex.vue 
-->

<template>
  <!-- padding and boundaries of the page -->
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
          'backgroundColor': ghost.bgColor,
          'borderColor': ghost.borderColor,
        }"
      >
        <span v-html="ghost.text"></span>
        <strong class="bubble-author"> {{ ghost.author }}</strong>
      </div>
    </div>

    <!-- two-column layout -->
    <div class="left-column">
      <bbyBubble class="bubble-area" />
      <div class="controls-panel">
        <div class="input-group">
          <input v-model="textToSay" @keyup.enter="handleSayClick" placeholder="type a message..." class="text-input" />
          <button @click="handleSayClick" class="action-button" :disabled="!textToSay">send</button>
          <button @click="sayRandomFact" class="action-button">fact</button>
        </div>
        <div class="input-group button-row">
          <input id="color-picker" type="color" v-model="colorInput" @input="updateTargetColor" class="color-input" />
          <button @click="randomiseColor" class="action-button">colour</button>
          <button @click="handleUsernameUpdate" class="action-button" :disabled="!usernameInput">name</button>
          <input v-model="usernameInput" @keyup.enter="handleUsernameUpdate" placeholder="enter username..." class="name-input"/>
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
import bbyBubble from '@/components/bbyBubble.vue';

const { bbyState, say, requestStateChange, sayRandomFact, author, setUsername, clearBubbles } = bbyUse();
const textToSay = ref('');
const colorInput = ref('#85efee');
const usernameInput = ref(author.value);
const handleSayClick = () => {
  say(textToSay.value, usernameInput.value); 
  textToSay.value = '';
};
const handleUsernameUpdate = () => {
  setUsername(usernameInput.value);
};
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
/* Scoped styles to prevent them from leaking */
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
