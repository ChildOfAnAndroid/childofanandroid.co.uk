// src/composables/bbyUse.ts

import { reactive, readonly, ref, watch } from 'vue';
import _ from 'lodash';

interface Bubble {
  id: string;
  text: string;
  author?: string;
  ghostX?: string;
  ghostY?: string;
  ghostR?: string;
  startX?: string;
  startY?: string;
  width?: string;
  height?: string;
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
  isSpeaking: false, speechText: '', 
  
  // BBY CLIENT
  bubbles: [] as Bubble[],
  graveyardBubbles: [] as Bubble[],
});

const targetColour = reactive({ r: 133, g: 239, b: 238 });
const currentColour = reactive({ r: 133, g: 239, b: 238 });
const tintStrength = ref(1.0);
const author = ref(localStorage.getItem('bbyUsername') || 'kevinonline420');
function setUsername(name: string) {author.value = name; localStorage.setItem('bbyUsername', name);}
const bbyFacts = ref<Record<string, { value: string, author: string }>>({});
let isClientRunning = false;

async function fetchBbyFacts() {
  try {
    const response = await fetch('https://bbyapi.childofanandroid.co.uk/api/bbybook', {
      cache: 'no-store',
    });
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
      const response = await fetch('https://bbyapi.childofanandroid.co.uk/api/state', {
        cache: 'no-store',
      });
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
  setInterval(async () => {
    try {
      const response = await fetch('https://bbyapi.childofanandroid.co.uk/api/chat_history', {
        cache: 'no-store',
      });
      if (!response.ok) return;
      
      const serverHistory: { id: string; author: string; text: string }[] = await response.json();
      serverHistory.forEach(message => {
        const bubbleExists = bbyState.bubbles.some(b => b.id === message.id);
        const ghostExists = bbyState.graveyardBubbles.some(g => g.id === `ghost-${message.id}`);
        if (!bubbleExists && !ghostExists) {
          const randw = (min: number, max: number) => `${Math.random() * (max - min) + min}vw`;
          const randh = (min: number, max: number) => `${Math.random() * (max - min) + min}vh`;
          const r = Math.round(currentColour.r);
          const g = Math.round(currentColour.g);
          const b = Math.round(currentColour.b);
          const stampedBgColor = `rgba(${r}, ${g}, ${b}, 0.9)`;
          const stampedBorderColor = `rgb(${Math.max(0, r - 30)}, ${Math.max(0, g - 30)}, ${Math.max(0, b - 30)})`;
          const baseTime = (Math.random() * 32000);           // 32s
          const timePerChar = (Math.random() * 3200);         // 3.2s/char
          const maxTime = (Math.random() * 320000);           // 320s cap
          const textLength = message.text.length;
          let timeout = Math.min(baseTime + textLength * timePerChar, maxTime);
          const jitter = Math.random() * 3000 - 1500;

          const newBubble: Bubble = {
            id: message.id,
            text: message.text,
            author: message.author,
            ghostX: randw(-50, 50),
            ghostY: randh(-50, 50),
            ghostR: `${Math.random() * 1440 * (Math.random()>0.5?1:-1)}deg`,
            bgColor: stampedBgColor,
            borderColor: stampedBorderColor,
          };

          bbyState.bubbles.push(newBubble);
          setTimeout(() => removeBubble(newBubble.id), timeout + jitter);
        }
      });
    } catch (error) {console.error("failed to fetch chat history:", error); }
  }, 1500);

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
      cache: 'no-store',
      body: JSON.stringify(updates),
    });
  } catch (error) { console.error("failed to send state change:", error); }
}

async function say(text: string, author: string) {
  const trimmed = text.trim();
  if (!trimmed) return;
  const MAX_ATTEMPTS = 3;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
      const response = await fetch('https://bbyapi.childofanandroid.co.uk/api/say', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
        body: JSON.stringify({ text: trimmed, author: author}),
      });

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      return; // success
    } catch (error) {
      if (attempt === MAX_ATTEMPTS) {
        console.error("failed to talk to baby:", error);
      } else {
        await new Promise(resolve => setTimeout(resolve, attempt * 1000));
      }
    }
  }
}

const MAX_GHOSTS = 1000;
function removeBubble(id: string) {
  const bubbleEl = document.querySelector(`[data-bubble-id="${id}"]`);
  const bubbleIndex = bbyState.bubbles.findIndex(b => b.id === id);

  if (bubbleEl && bubbleIndex !== -1) {
    const rect = bubbleEl.getBoundingClientRect();
    const originalBubble = bbyState.bubbles[bubbleIndex];
    
    const duration = Math.random() * 8000 + 60;
    const delay = Math.random() * 2;
    const easings = ['ease-in-out', 'ease-in', 'ease-out', 'linear', 'cubic-bezier(0.25, 1, 0.5, 1)', 'cubic-bezier(0.4, 0, 0.2, 1)'];
    const easing = easings[Math.floor(Math.random() * easings.length)];

    // this is where all things are copied from main bubbles
    const ghostBubble: Bubble = {
      id: `ghost-${originalBubble.id}`,
      text: originalBubble.text,
      startX: `${rect.left + window.scrollX}px`,
      startY: `${rect.top + window.scrollY}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
      ghostX: originalBubble.ghostX,
      ghostY: originalBubble.ghostY,
      ghostR: originalBubble.ghostR,
      author: originalBubble.author,
      duration: `${duration}s`,
      easing: easing,
      delay: `${delay}s`,
      bgColor: originalBubble.bgColor,
      borderColor: originalBubble.borderColor,
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

function clearBubbles() {bbyState.bubbles = []; }

function sayRandomFact() {
  const factKeys = Object.keys(bbyFacts.value);
  if (factKeys.length === 0) {
    say("I don't know any facts yet...", author.value);
    return;
  }

  const randomKey = factKeys[Math.floor(Math.random() * factKeys.length)];
  const fact = bbyFacts.value[randomKey];

  if (fact && fact.value) {
    const message = `hey bby, did you know that ${randomKey} is ${fact.value}?`;
    say(message, author.value); 
  }
}

watch(currentColour, (newColour) => {
  const r = Math.round(newColour.r);
  const g = Math.round(newColour.g);
  const b = Math.round(newColour.b);

  const root = document.documentElement;
  // sets a root style property that changes every time it is watched, allowing fast colour changes on the bubbles etc
  root.style.setProperty('--bby-colour', `rgba(${r}, ${g}, ${b}, 0.9)`);
  
  const borderR = Math.max(0, r - 30);
  const borderG = Math.max(0, g - 30);
  const borderB = Math.max(0, b - 30);
  root.style.setProperty('--bby-colour-dark', `rgb(${borderR}, ${borderG}, ${borderB})`);

}, { 
  deep: true,      // watch for changes inside an object
  immediate: true  // runs watcher on component load
});

let mouthInterval: ReturnType<typeof setInterval> | null = null;
  watch(() => bbyState.isSpeaking, (isSpeaking) => {
    if (mouthInterval) {clearInterval(mouthInterval); mouthInterval = null;}
    if (!isSpeaking) {bbyState.mouth = 1; return;}

    mouthInterval = setInterval(() => {
      if (!bbyState.isSpeaking) {
        clearInterval(mouthInterval!);
        mouthInterval = null;
        bbyState.mouth = 1;
        return;
      }
      bbyState.mouth = 75 + Math.floor(Math.random() * 11);
    }, 120);
  });

export function bbyUse() {
  startClient();
  return {
    bbyState: readonly(bbyState),
    currentColour: readonly(currentColour),
    tintStrength: readonly(tintStrength),
    author: readonly(author),
    setUsername,
    requestStateChange,
    say,
    removeBubble,
    sayRandomFact,
    clearBubbles,
  };
}