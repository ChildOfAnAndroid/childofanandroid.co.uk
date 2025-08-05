<template>
  <div id="app-container">

    <!-- UI to left -->
    <div class="left-column">

      <!-- bubble stack -->
      <bbyBubble class="bubble-area" />

      <!-- control panel -->
      <div class="controls-panel">
        <h3 class="panel-title">--[ BBY_CTRL ]--</h3>

        <div class="input-group">
          <input
            v-model="usernameInput"
            @keyup.enter="handleUsernameUpdate"
            placeholder="enter username..."
            class="text-input"
          />
          <button @click="handleUsernameUpdate" class="action-button">SET NAME</button>
        </div>

        <div class="input-group">
          <input
            v-model="textToSay"
            @keyup.enter="handleSayClick"
            placeholder="type a message..."
            class="text-input"
          />
          <button @click="handleSayClick" class="action-button">SAY</button>
        </div>

        <div class="input-group">
          <label for="color-picker">TARGET_COLOUR:</label>
          <input
            id="color-picker"
            type="color"
            v-model="colorInput"
            @input="updateTargetColor"
            class="color-input"
          />
        </div>

        <div class="input-group button-row">
          <button @click="requestStateChange({ jumping: true })" class="action-button">JUMP</button>
          <button @click="requestStateChange({ cheeks_on: !bbyState.cheeks_on })" class="action-button">CHEEKS</button>
          <button @click="requestStateChange({ stretch_up: true })" class="action-button">STRETCH</button>
          <button @click="sayRandomFact" class="action-button">RANDOM FACT</button>
        </div>
      </div>
    </div>

    <!-- bby on right -->
    <div class="right-column">
      <div class="bby-stage">
        <bbySprite />
      </div>
    </div>

    <!-- GLOBAL GHOST GRAVEYARD -->
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { bbyUse } from './composables/bbyUse.ts';
import bbySprite from './components/bbySprite.vue';
import bbyBubble from './components/bbyBubble.vue';

const { bbyState, say, requestStateChange, sayRandomFact, username, setUsername } = bbyUse();

const textToSay = ref('');
const colorInput = ref('#85efee');
const usernameInput = ref(username.value);

const handleSayClick = () => {
  say(textToSay.value);
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
</script>

<style>

</style>
