// src/composables/bbyUse.ts

import { reactive, readonly, ref, watch } from 'vue';
import _ from 'lodash';

interface Bubble {
  id: string;
  text: string;
  ghostX?: string;
  ghostY?: string;
  ghostR?: string;
  startX?: string;
  startY?: string;
  width?: string;
  duration?: string;
  easing?: string;
  delay?: string;
  bgColor?: string;
  borderColor?: string;
}

const bbyState = reactive({
  // BBY SERVER
  eyes: 5, mouth: 1, cheeks_on: false, tears_on: false, jumping: false,
  stretch_left: false, stretch_right: false, stretch_up: false, stretch_down: false,
  squish_left: false, squish_right: false, squish_up: false, squish_down: false,
  isSpeaking: false,
  speechText: '', 
  
  // BBY CLIENT
  bubbles: [] as Bubble[],
  graveyardBubbles: [] as Bubble[],
});

const targetColour = reactive({ r: 133, g: 239, b: 238 });
const currentColour = reactive({ r: 133, g: 239, b: 238 });
const tintStrength = ref(1.0);

const bbyFacts = ref<Record<string, { value: string, author: string }>>({});

let isClientRunning = false;

async function fetchBbyFacts() {
  try {
    const response = await fetch('https://bbyapi.childofanandroid.co.uk/api/bbybook');
    if (!response.ok) return;
    bbyFacts.value = await response.json();
    console.log(`Loaded ${Object.keys(bbyFacts.value).length} bbyfacts!`);
  } catch (error) {
    console.error("Could not fetch bbybook:", error);
  }
}

function startClient() {
  if (isClientRunning) return;
  isClientRunning = true;

  fetchBbyFacts();

  setInterval(async () => {
    try {
      const response = await fetch('https://bbyapi.childofanandroid.co.uk/api/state');
      if (!response.ok) return;
      
      const serverState = await response.json();
      
      Object.assign(bbyState, serverState);
      
      if (serverState.R !== undefined) {
        targetColour.r = serverState.R;
        targetColour.g = serverState.G;
        targetColour.b = serverState.B;
      }
    } catch (error) { /* ignore */ }
  }, 50);

  function colourAnimationLoop() {
    currentColour.r += (targetColour.r - currentColour.r) * 0.02;
    currentColour.g += (targetColour.g - currentColour.g) * 0.01;
    currentColour.b += (targetColour.b - currentColour.b) * 0.02;
    requestAnimationFrame(colourAnimationLoop);
  }
  requestAnimationFrame(colourAnimationLoop);
}

async function requestStateChange(updates: object) {
  try {
    await fetch('https://bbyapi.childofanandroid.co.uk/api/set', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
  } catch (error) { console.error("Failed to send state change:", error); }
}

async function say(text: string) {
  if (!text) return;

  const randw = (min: number, max: number) => `${Math.random() * (max - min) + min}vw`;
  const randh = (min: number, max: number) => `${Math.random() * (max - min) + min}vh`;

  const userBubble: Bubble = {
    id: `bubble-user-${Date.now()}`,
    text,
    ghostX: randw(-50, 50),
    ghostY: randh(-50, 50),
    ghostR: `${Math.random() * 1440 - 1440}deg`,
  };
  bbyState.bubbles.push(userBubble);
  setTimeout(() => removeBubble(userBubble.id), 55000 + Math.random() * 55000);

  try {
    const response = await fetch('https://bbyapi.childofanandroid.co.uk/api/say', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text }),
    });

    if (!response.ok) throw new Error(`Server responded with ${response.status}`);

    const data = await response.json();
    const reply = data.reply;

    if (reply) {
      const replyBubble: Bubble = {
        id: `bubble-bby-${Date.now()}`,
        text: reply,
        ghostX: randw(-50, 50),
        ghostY: randh(-50, 50),
        ghostR: `${Math.random() * 1440 - 1360}deg`,
      };

      setTimeout(() => {bbyState.bubbles.push(replyBubble);
        setTimeout(() => removeBubble(replyBubble.id), 55000 + Math.random() * 55000);
      }, 300 + Math.random() * 500);
    }

  } catch (error) {
    console.error("Failed to talk to Baby:", error);
  }
}

const MAX_GHOSTS = 421;

function removeBubble(id: string) {
  const bubbleEl = document.querySelector(`[data-bubble-id="${id}"]`);
  const bubbleIndex = bbyState.bubbles.findIndex(b => b.id === id);

  if (bubbleEl && bubbleIndex !== -1) {
    const rect = bubbleEl.getBoundingClientRect();
    const originalBubble = bbyState.bubbles[bubbleIndex];

    const r = Math.round(currentColour.r);
    const g = Math.round(currentColour.g);
    const b = Math.round(currentColour.b);
    const stampedBgColor = `rgba(${r}, ${g}, ${b}, 0.9)`;
    const stampedBorderColor = `rgb(${Math.max(0, r - 30)}, ${Math.max(0, g - 30)}, ${Math.max(0, b - 30)})`;
    
    const duration = Math.random() * 1500 + 15;
    const delay = Math.random() * 2;
    const easings = ['ease-in-out', 'ease-in', 'ease-out', 'linear', 'cubic-bezier(0.25, 1, 0.5, 1)', 'cubic-bezier(0.4, 0, 0.2, 1)'];
    const easing = easings[Math.floor(Math.random() * easings.length)];

    const ghostBubble: Bubble = {
      id: `ghost-${originalBubble.id}`,
      text: originalBubble.text,
      startX: `${rect.left}px`,
      startY: `${rect.top}px`,
      width: `${rect.width}px`,
      ghostX: originalBubble.ghostX,
      ghostY: originalBubble.ghostY,
      ghostR: originalBubble.ghostR,
      duration: `${duration}s`,
      easing: easing,
      delay: `${delay}s`,
      bgColor: stampedBgColor,
      borderColor: stampedBorderColor,
    };

    bbyState.graveyardBubbles.push(ghostBubble);
    if (bbyState.graveyardBubbles.length > MAX_GHOSTS) {
      bbyState.graveyardBubbles.shift(); 
    }
    bbyState.bubbles.splice(bubbleIndex, 1);
  } else if (bubbleIndex !== -1) {
    bbyState.bubbles.splice(bubbleIndex, 1);
  }
}

function sayRandomFact() {
  const factKeys = Object.keys(bbyFacts.value);
  if (factKeys.length === 0) {
    say("I don't know any facts yet...");
    return;
  }

  const randomKey = factKeys[Math.floor(Math.random() * factKeys.length)];
  const fact = bbyFacts.value[randomKey];

  if (fact && fact.value) {
    const message = `hey bby, did you know that ${randomKey} is ${fact.value}?`;
        say(message);
  }
}

watch(currentColour, (newColour) => {
  // Get the clean RGB values
  const r = Math.round(newColour.r);
  const g = Math.round(newColour.g);
  const b = Math.round(newColour.b);

  const root = document.documentElement;

  // Set the background color variable, including the 90% transparency from your original style.
  root.style.setProperty('--bubble-bg', `rgba(${r}, ${g}, ${b}, 0.9)`);
  
  // As a bonus, let's also set the border to be a darker version of the main color.
  const borderR = Math.max(0, r - 30);
  const borderG = Math.max(0, g - 30);
  const borderB = Math.max(0, b - 30);
  root.style.setProperty('--bubble-border', `rgb(${borderR}, ${borderG}, ${borderB})`);

}, { 
  deep: true,      // Needed to watch for changes inside an object
  immediate: true  // Runs the watcher immediately on component load, setting the initial color
});

watch(() => bbyState.isSpeaking, (isSpeaking) => {
    if(!isSpeaking) return;

    const mouthInterval = setInterval(() => {
        if(!bbyState.isSpeaking) {
            clearInterval(mouthInterval);
            bbyState.mouth = 1;
            return;
        }
        bbyState.mouth = 55 + Math.floor(Math.random() * 11);
    }, 120);
});

export function bbyUse() {
  startClient();
  return {
    bbyState: readonly(bbyState),
    currentColour: readonly(currentColour),
    tintStrength: readonly(tintStrength),
    requestStateChange,
    say,
    removeBubble,
    sayRandomFact,
  };
}