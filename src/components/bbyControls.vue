<template>
  <div class="controls-panel">
    <chatControls @send="handleSend" @fact="handleFactClick" />
    <div class="input-group button-row">
      <input id="color-picker" type="color" v-model="colourInput" @input="updateUserColourAndTint" class="colour-input" />
      <input v-model="usernameInput" @keyup="handleUsernameUpdate" placeholder="enter username..." class="name-input"/>
      <button @click="randomiseUserColourAndTint" class="action-button">random colour</button>
      <button @click="requestStateChange({ jumping: true })" class="action-button">jump</button>
      <button @click="requestStateChange({ cheeks_on: !bbyState.cheeks_on })" class="action-button">blush</button>
      <button @click="requestStateChange({ stretch_up: true })" class="action-button">stretch</button>
      <button @click="clearBubbles" class="action-button">pop</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { bbyUse } from '@/composables/bbyUse.ts';
import chatControls from '@/components/chatControls.vue';
import { hexToRGB, rgbToHex } from '@/utils/colourEngine';

const { bbyState, say, requestStateChange, sayRandomFact, author, setUsername, clearBubbles, userColour, setUserColour, setBbyTintColour } = bbyUse();

const colourInput = ref(rgbToHex(userColour.value.r, userColour.value.g, userColour.value.b));
const usernameInput = ref(author.value);

const handleFactClick = () => {
  sayRandomFact();
};

const handleSend = (message: string) => {
  say(message, usernameInput.value, userColour.value);
};

const handleUsernameUpdate = () => {
  setUsername(usernameInput.value);
};

const updateUserColourAndTint = () => {
  try {
    const { r, g, b } = hexToRGB(colourInput.value);
    setUserColour(r, g, b); // Set for future bubbles
    setBbyTintColour(r, g, b); // Set for BBY tint right now
  } catch {
    /* ignore invalid colour */
  }
};

const randomiseUserColourAndTint = () => {
  const R = Math.floor(Math.random() * 256);
  const G = Math.floor(Math.random() * 256);
  const B = Math.floor(Math.random() * 256);
  colourInput.value = rgbToHex(R, G, B);
  setUserColour(R, G, B);
  setBbyTintColour(R, G, B);
};
</script>

<style scoped>
/* styles for controls panel are defined in src/styles/_components.css */
</style>
