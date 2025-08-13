<template>
  <div class="controls-panel">
    <div class="input-group">
      <input v-model="textToSay" @keyup.enter="handleSayClick" placeholder="type a message..." class="text-input" />
      <button @click="handleSayClick" class="action-button" :disabled="!textToSay">send</button>
      <button @click="handleFactClick" class="action-button">fact</button>
    </div>
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

const { bbyState, say, requestStateChange, sayRandomFact, author, setUsername, clearBubbles, userColour, setUserColour, setBbyTintColour } = bbyUse();

const textToSay = ref('');
const toHex = (c: {r: number, g: number, b: number}) => `#${[c.r, c.g, c.b].map(x => x.toString(16).padStart(2, '0')).join('')}`;
const colourInput = ref(toHex(userColour.value));
const usernameInput = ref(author.value);

const handleSayClick = () => {
  say(textToSay.value, usernameInput.value, userColour.value);
  textToSay.value = '';
};
const handleFactClick = () => {
  sayRandomFact();
};

const handleUsernameUpdate = () => {
  setUsername(usernameInput.value);
};

const updateUserColourAndTint = () => {
  const hex = colourInput.value.replace('#', '');
  if (hex.length === 6) {
    const R = parseInt(hex.substring(0, 2), 16);
    const G = parseInt(hex.substring(2, 4), 16);
    const B = parseInt(hex.substring(4, 6), 16);
    setUserColour(R, G, B); // Set for future bubbles
    setBbyTintColour(R, G, B); // Set for BBY tint right now
  }
};

const randomiseUserColourAndTint = () => {
  const R = Math.floor(Math.random() * 256);
  const G = Math.floor(Math.random() * 256);
  const B = Math.floor(Math.random() * 256);
  colourInput.value = `#${[R, G, B].map(x => x.toString(16).padStart(2, '0')).join('')}`;
  setUserColour(R, G, B);
  setBbyTintColour(R, G, B);
};
</script>

<style scoped>
/* styles for controls panel are defined in src/styles/_components.css */
</style>
