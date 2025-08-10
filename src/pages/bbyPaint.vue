<!-- 
CHARIS CAT // CHILD OF AN ANDROID - 2025 
src/pages/bbyPaint.vue 
-->

<template>
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

    <div class="paint-page-layout">
      <div class="left-column-paint">
        <div class="controls-panel vertical-panel">
          <h1>bby paint</h1>
          <div class="input-group">
            <button @click="mode = 'paint'" class="action-button" :class="{ active: mode === 'paint' }">Paint</button>
            <button @click="mode = 'erase'" class="action-button" :class="{ active: mode === 'erase' }">Erase</button>
            <button @click="mode = 'eyedropper'" class="action-button" :class="{ active: mode === 'eyedropper' }">Dropper</button>
          </div>

          <div class="input-group">
            <label for="color-picker-paint">Colour</label>
            <input id="color-picker-paint" type="color" v-model="hexColor" class="colour-input" />
          </div>
          
          <div class="input-group">
            <label>Size: <span>{{ brushSize }}</span></label>
            <input type="range" min="1" max="8" step="1" v-model.number="brushSize" class="slider" />
          </div>

          <div class="input-group">
            <label>Swatches</label>
            <div class="swatch-grid">
              <div
                v-for="swatch in swatches"
                :key="swatch"
                class="swatch"
                :style="{ backgroundColor: swatch }"
                @click="setSwatchColor(swatch)"
              ></div>
            </div>
          </div>
          <div style="flex-grow: 1;"></div>
          <div class="input-group">
            <button 
              @click="handleClearClick" 
              class="action-button clear-button"
              :class="{ 'confirm-active': isConfirmingClear }"
            >
              {{ isConfirmingClear ? 'Confirm Clear' : 'Clear Canvas' }}
            </button>
          </div>
        </div>
      </div>

      <div class="right-column-paint">
        <div class="bby-stage">
          <bbyPixels
            ref="bbyPixelsRef"
            :mode="mode"
            :hex-color="hexColor"
            :brush-size="brushSize"
            @color-picked="handleColorPicked"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import bbyPixels from '@/components/bbyPixels.vue';
import { bbyUse } from '@/composables/bbyUse.ts';

const { bbyState } = bbyUse();

const mode = ref<'paint' | 'erase' | 'eyedropper'>('paint');
const hexColor = ref('#ff00ff');
const brushSize = ref(1);
const bbyPixelsRef = ref<InstanceType<typeof bbyPixels> | null>(null);

const isConfirmingClear = ref(false);
let confirmTimeout: ReturnType<typeof setTimeout> | null = null;

const swatches = [
  '#FFFFFF', '#C2C2C2', '#858585', '#474747', '#000000', '#2E1A47',
  '#FF5A5A', '#FF965A', '#FFD25A', '#FFF05A', '#C8FF5A', '#78FF5A',
  '#5AFFC8', '#5AFFFF', '#5AC8FF', '#5A78FF', '#965AFF', '#E15AFF'
];

const handleClearClick = () => {
  if (isConfirmingClear.value) {
    if (confirmTimeout) clearTimeout(confirmTimeout);
    bbyPixelsRef.value?.clearOverlay();
    isConfirmingClear.value = false;
  } else {
    isConfirmingClear.value = true;
    confirmTimeout = setTimeout(() => {
      isConfirmingClear.value = false;
    }, 3000);
  }
};

const setSwatchColor = (color: string) => {
  hexColor.value = color;
  mode.value = 'paint';
};

const handleColorPicked = (color: string) => {
  hexColor.value = color;
  mode.value = 'paint';
};
</script>

<style scoped>
.page-container, .paint-page-layout {
  display: flex;
  width: 100%;
  height: var(--full-height);
  box-sizing: border-box;
}
.page-container { padding: var(--padding); }
.paint-page-layout { gap: var(--spacing); }

.right-column-paint {
  flex-grow: 1;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.right-column-paint > .bby-stage { width: 100%; height: 100%; }

.left-column-paint {
  width: 10%;
  flex-shrink: 0;
  height: 100%;
  display: flex;
}

.vertical-panel {
  padding: var(--padding);
  background-color: var(--panel-colour);
  border: var(--border);
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: calc(var(--spacing) * 1.5);
}

.vertical-panel h1 {
  margin-top: 0;
  text-align: center;
}

.vertical-panel .input-group {
  display: flex;
  flex-direction: column;
  align-items: stretch; /* make children fill width fear */
  gap: calc(var(--spacing) / 2);
}

.vertical-panel .input-group label {
  font-size: var(--small-font-size);
  text-align: center;
  opacity: 0.8;
}

.vertical-panel .action-button.active {
  background-color: var(--accent-hover);
  border-color: var(--accent-colour);
}

.colour-input {
	flex-grow: 1;
	max-width: none;
	width: 100%;
	height: 4rem;
	cursor: pointer;
	padding: 0;
	border: var(--border);
	border-radius: var(--border-radius);
	box-shadow: var(--box-shadow);
	-webkit-appearance: none;
	appearance: none;
	background-color: var(--bby-colour-black);
}
.colour-input::-webkit-color-swatch-wrapper { padding: 0; }
.colour-input::-webkit-color-swatch { border: none; border-radius: calc(var(--border-radius) * 0.8); }


.slider-container {
	flex-direction: column;
	align-items: flex-start;
}
.slider-container label span {
	font-weight: bold;
	color: var(--accent-colour);
}
.slider {
	width: 100%;
}

.swatch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(1.5rem, 1fr));
  gap: calc(var(--padding) / 2);
}
.swatch {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  cursor: pointer;
  border: var(--border-width) solid var(--bby-colour-dark);
  box-shadow: var(--box-shadow);
  transition: all 0.1s ease-out;
}
.swatch:hover {
  transform: scale(1.1);
  border-color: var(--accent-colour);
}

.clear-button {
  background-color: var(--bby-colour-dark);
}
.clear-button.confirm-active {
  background-color: #e94560;
  border-color: #FFFFFF;
  color: #FFFFFF;
  font-weight: bold;
}
</style>