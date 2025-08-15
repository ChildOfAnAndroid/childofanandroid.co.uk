<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
  <div class="page-container">
    <!-- bubbles -->
    <bubbleGraveyard />

    <div class="paint-page-layout">
      <div class="left-column-paint">
        <div class="vertical-panel">
          <h1>BBY<br>PAINT</h1>

          <!-- Canvas Toggle -->
          <div class="grp">
             <button @click="isDrawingOnTestCanvas = !isDrawingOnTestCanvas" class="action">
              {{ isDrawingOnTestCanvas ? 'Switch to BBY' : 'Switch to Test Canvas' }}
            </button>
          </div>

          <!-- tools -->
          <div class="grp">
            <label class="section">Tool</label>
            <div class="row3">
              <button @click="setMode('paint')" :class="modeBtn('paint')">PAINT</button>
              <button @click="setMode('blend')" :class="modeBtn('blend')">BLEND</button>
              <button @click="setMode('erase')" :class="modeBtn('erase')">ERASE</button>
            </div>
          </div>

          <!-- base colour -->
          <div class="grp">
            <label class="section">Base Colour</label>
            <div class="base-color-row">
              <input type="color" v-model="hexColor" class="colour-input-main" />
              <div class="base-color-tools">
                <button @click="setMode('eyedropper')" :class="['action', {active: currentMode==='eyedropper','eyedropper-active': currentMode==='eyedropper'}]" :style="eyedropperStyle" title="Eyedropper">EYE</button>
                <button @click="isScopeCursorActive = !isScopeCursorActive" :class="['action', {active: isScopeCursorActive}]" title="Zoom Cursor">ZOOM</button>
                <button @click="swatchesOpen = !swatchesOpen" :class="['action', {active: swatchesOpen}]" title="Swatches">▾</button>
              </div>
            </div>
            <swatchDrawer
              :swatches-open="swatchesOpen"
              :swatches="swatches"
              :bby-button-style="bbyButtonStyle"
              :user-button-style="userButtonStyle"
              :set-picker-to-bby-color="setPickerToBbyColor"
              :set-picker-to-user-color="setPickerToUserColor"
              :set-swatch-color="setSwatchColor"
            />
          </div>

          <!-- tempo + knobs -->
          <div class="grp controls-container">
            <tempoFader v-model="tempo" />
            <colourScope
              v-model:scopeLength="scopeLength"
              v-model:isScopeMinimized="isScopeMinimized"
              :hex-color="hexColor"
              :tempo="tempo"
              :active-eqs="activeEQs"
              :user-color-influence="userColorInfluence"
              :bby-influence="bbyInfluence"
              :red-influence="redInfluence"
              :green-influence="greenInfluence"
              :blue-influence="blueInfluence"
              :rainbow-influence="rainbowInfluence"
              :user-colour="userColour"
              :current-colour="currentColour"
            />

            <div class="mixer-column">
              <div class="knob-box">
                <div class="knob-bank">
                  <!-- R -->
                  <div class="dial-grp" :class="{active: activeEQs.has('red')}" :style="{'--knob-glow': '#ff4040'}">
                    <div class="dial-container" @mousedown.prevent="e => startDialDrag(e, 'red')" @dragover.prevent @drop="e => onKnobDrop(e, 'redInfluence')" @dblclick="clearLfo('redInfluence')">
                      <div class="dial-knob">
                        <div class="dial-needle" :style="{ transform: `rotate(${redInfluenceDialRotation}deg)` }"></div>
                        <div class="dial-label-area">
                          <label class="dial-label" @click.stop="toggleEQ('red')">R</label>
                          <input
                            class="dial-input-box"
                            :value="format2(redInfluence)"
                            @input="onNumberEdit($event, 'redInfluence')"
                            @wheel="onWheelAdjust($event, 'redInfluence')"
                            @keydown="onKeyAdjust($event, 'redInfluence')"
                            inputmode="decimal"
                          />
                        </div>
                        <div class="lfo-ghost" v-html="getWaveSvg(getLfoWaveform(lfoAssignments.redInfluence))"></div>
                      </div>
                    </div>
                  </div>

                  <!-- BBY -->
                  <div class="dial-grp" :class="{active: activeEQs.has('bby')}" :style="{'--knob-glow': bbyKnobColor}">
                    <div class="dial-container" @mousedown.prevent="e => startDialDrag(e, 'bby')" @dragover.prevent @drop="e => onKnobDrop(e, 'bbyInfluence')" @dblclick="clearLfo('bbyInfluence')">
                      <div class="dial-knob">
                        <div class="dial-needle" :style="{ transform: `rotate(${bbyInfluenceDialRotation}deg)` }"></div>
                        <div class="dial-label-area">
                          <label class="dial-label" @click.stop="toggleEQ('bby')">BBY</label>
                          <input
                            class="dial-input-box"
                            :value="format2(bbyInfluence)"
                            @input="onNumberEdit($event, 'bbyInfluence')"
                            @wheel="onWheelAdjust($event, 'bbyInfluence')"
                            @keydown="onKeyAdjust($event, 'bbyInfluence')"
                            inputmode="decimal"
                          />
                        </div>
                        <div class="lfo-ghost" v-html="getWaveSvg(getLfoWaveform(lfoAssignments.bbyInfluence))"></div>
                      </div>
                    </div>
                  </div>

                  <!-- G -->
                  <div class="dial-grp" :class="{active: activeEQs.has('green')}" :style="{'--knob-glow': '#40ff40'}">
                    <div class="dial-container" @mousedown.prevent="e => startDialDrag(e, 'green')" @dragover.prevent @drop="e => onKnobDrop(e, 'greenInfluence')" @dblclick="clearLfo('greenInfluence')">
                      <div class="dial-knob">
                        <div class="dial-needle" :style="{ transform: `rotate(${greenInfluenceDialRotation}deg)` }"></div>
                        <div class="dial-label-area">
                          <label class="dial-label" @click.stop="toggleEQ('green')">G</label>
                          <input
                            class="dial-input-box"
                            :value="format2(greenInfluence)"
                            @input="onNumberEdit($event, 'greenInfluence')"
                            @wheel="onWheelAdjust($event, 'greenInfluence')"
                            @keydown="onKeyAdjust($event, 'greenInfluence')"
                            inputmode="decimal"
                          />
                        </div>
                        <div class="lfo-ghost" v-html="getWaveSvg(getLfoWaveform(lfoAssignments.greenInfluence))"></div>
                      </div>
                    </div>
                  </div>

                  <!-- USER -->
                  <div class="dial-grp" :class="{active: activeEQs.has('user')}" :style="{'--knob-glow': userKnobColor}">
                    <div class="dial-container" @mousedown.prevent="e => startDialDrag(e, 'user')" @dragover.prevent @drop="e => onKnobDrop(e, 'userColorInfluence')" @dblclick="clearLfo('userColorInfluence')">
                      <div class="dial-knob">
                        <div class="dial-needle" :style="{ transform: `rotate(${userColorInfluenceDialRotation}deg)` }"></div>
                        <div class="dial-label-area">
                          <label class="dial-label" @click.stop="toggleEQ('user')">{{ userAcronym }}</label>
                          <input
                            class="dial-input-box"
                            :value="format2(userColorInfluence)"
                            @input="onNumberEdit($event, 'userColorInfluence')"
                            @wheel="onWheelAdjust($event, 'userColorInfluence')"
                            @keydown="onKeyAdjust($event, 'userColorInfluence')"
                            inputmode="decimal"
                          />
                        </div>
                        <div class="lfo-ghost" v-html="getWaveSvg(getLfoWaveform(lfoAssignments.userColorInfluence))"></div>
                      </div>
                    </div>
                  </div>

                  <!-- B -->
                  <div class="dial-grp" :class="{active: activeEQs.has('blue')}" :style="{'--knob-glow': '#4040ff'}">
                    <div class="dial-container" @mousedown.prevent="e => startDialDrag(e, 'blue')" @dragover.prevent @drop="e => onKnobDrop(e, 'blueInfluence')" @dblclick="clearLfo('blueInfluence')">
                      <div class="dial-knob">
                        <div class="dial-needle" :style="{ transform: `rotate(${blueInfluenceDialRotation}deg)` }"></div>
                        <div class="dial-label-area">
                          <label class="dial-label" @click.stop="toggleEQ('blue')">B</label>
                          <input
                            class="dial-input-box"
                            :value="format2(blueInfluence)"
                            @input="onNumberEdit($event, 'blueInfluence')"
                            @wheel="onWheelAdjust($event, 'blueInfluence')"
                            @keydown="onKeyAdjust($event, 'blueInfluence')"
                            inputmode="decimal"
                          />
                        </div>
                        <div class="lfo-ghost" v-html="getWaveSvg(getLfoWaveform(lfoAssignments.blueInfluence))"></div>
                      </div>
                    </div>
                  </div>

                  <!-- RBW -->
                  <div class="dial-grp" :class="{active: activeEQs.has('rainbow')}" :style="{'--knob-glow': '#e15aff'}">
                    <div class="dial-container" @mousedown.prevent="e => startDialDrag(e, 'rainbow')" @dragover.prevent @drop="e => onKnobDrop(e, 'rainbowInfluence')" @dblclick="clearLfo('rainbowInfluence')">
                      <div class="dial-knob rainbow-knob">
                        <div class="dial-needle" :style="{ transform: `rotate(${rainbowInfluenceDialRotation}deg)` }"></div>
                        <div class="dial-label-area">
                          <label class="dial-label" @click.stop="toggleEQ('rainbow')">RBW</label>
                          <input
                            class="dial-input-box"
                            :value="format2(rainbowInfluence)"
                            @input="onNumberEdit($event, 'rainbowInfluence')"
                            @wheel="onWheelAdjust($event, 'rainbowInfluence')"
                            @keydown="onKeyAdjust($event, 'rainbowInfluence')"
                            inputmode="decimal"
                          />
                        </div>
                        <div class="lfo-ghost" v-html="getWaveSvg(getLfoWaveform(lfoAssignments.rainbowInfluence))"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="mode-info-display"><span>{{ toolModeDescription }}</span></div>
            </div>
          </div>

          <!-- LFO section -->
          <div class="grp lfo-section">
            <div class="lfo-header">
              <label class="section">LFO</label>
              <div class="lfo-mode-toggles">
                <button class="action" :class="{active: lfoMode === 'shape'}" @click="lfoMode = 'shape'">Shape</button>
                <button class="action" :class="{active: lfoMode === 'pixel'}" @click="lfoMode = 'pixel'">Pixel</button>
              </div>
            </div>

            <div class="lfo-main-area">
              <!-- SHAPE: wave bank + shaper -->
              <div v-if="lfoMode === 'shape'" class="lfo-bank">
                <div class="wave-draggable" draggable="true" @dragstart="e => handleWaveBankDragStart(e, 'sine')" v-html="getWaveSvg('sine')"></div>
                <div class="wave-draggable" draggable="true" @dragstart="e => handleWaveBankDragStart(e, 'triangle')" v-html="getWaveSvg('triangle')"></div>
                <div class="wave-draggable" draggable="true" @dragstart="e => handleWaveBankDragStart(e, 'square')" v-html="getWaveSvg('square')"></div>
                <div class="wave-draggable" draggable="true" @dragstart="e => handleWaveBankDragStart(e, 'sawtooth')" v-html="getWaveSvg('sawtooth')"></div>
                <div class="wave-draggable" draggable="true" @dragstart="e => handleWaveBankDragStart(e, 'ramp')" v-html="getWaveSvg('ramp')"></div>
                <div class="wave-draggable" draggable="true" @dragstart="e => handleWaveBankDragStart(e, 'random')" v-html="getWaveSvg('random')"></div>
              </div>

              <div v-if="lfoMode === 'shape'" ref="lfoShaper" class="lfo-shaper" @dragover.prevent @drop="onShaperDrop">
                <div v-if="currentLfo.wave" class="shaper-content" :style="{width: currentLfo.width + 'px', height: currentLfo.height + 'px'}" draggable="true" @dragstart="handleShaperDragStart">
                  <div class="shaper-svg-wrapper">
                    <div class="shaper-svg-bg" v-html="getWaveSvg(currentLfo.wave)"></div>
                    <svg class="shaper-svg-animated" width="100%" height="100%">
                      <defs><clipPath id="lfoClip"><rect :width="`${currentLfo.animProgress * 100}%`" height="100%" /></clipPath></defs>
                      <g :clip-path="`url(#lfoClip)`" v-html="getWaveSvg(currentLfo.wave)"></g>
                    </svg>
                  </div>
                  <div class="resize-handle h-left" @mousedown.prevent="e => handleResizeMouseDown(e, 'left')"></div>
                  <div class="resize-handle h-right" @mousedown.prevent="e => handleResizeMouseDown(e, 'right')"></div>
                  <div class="resize-handle v-top" @mousedown.prevent="e => handleResizeMouseDown(e, 'top')"></div>
                  <div class="resize-handle v-bottom" @mousedown.prevent="e => handleResizeMouseDown(e, 'bottom')"></div>
                </div>
                <span v-else class="shaper-prompt">DRAG WAVE HERE TO SHAPE</span>
              </div>

              <!-- PIXEL: presets + drag handle + sequencer -->
              <div v-if="lfoMode === 'pixel'" class="lfo-bank">
                <button class="action preset-btn" v-for="wave in presetWaves" :key="wave" @click="applyPreset(wave)" :title="`Draw ${wave} shape`">
                  <div class="preset-svg" v-html="getWaveSvg(wave)"></div>
                </button>
                <button class="action preset-btn" @click="clearSequencer" title="Clear Grid">X</button>
                <!-- DRAG HANDLE to assign the current pixel grid -->
                <button class="action preset-btn drag-handle"
                        draggable="true"
                        style="-webkit-user-drag: element;"
                        @dragstart="handleSequencerDragStart"
                        title="Drag to a knob">
                  SEQ
                </button>
              </div>

              <div v-if="lfoMode === 'pixel'" class="sequencer-container">
                <div class="sequencer-wrapper">
                  <canvas ref="sequencerCanvas" class="sequencer-canvas"
                          draggable="true" @dragstart="handleSequencerDragStart"
                          @pointerdown="handleSequencerPointerDown"
                          @pointermove="handleSequencerPointerMove"
                          @pointerup="handleSequencerPointerUp"
                          @pointerleave="handleSequencerPointerUp"></canvas>
                </div>
                <div class="sequencer-res-toggles">
                  <button class="action" :class="{active: sequencerCols === 3 && sequencerRows === 2}"  @click="setSequencerResolution(3,2)">3x2</button>
                  <button class="action" :class="{active: sequencerCols === 6 && sequencerRows === 4}"  @click="setSequencerResolution(6,4)">6x4</button>
                  <button class="action" :class="{active: sequencerCols === 12 && sequencerRows === 8}" @click="setSequencerResolution(12,8)">12x8</button>
                </div>
              </div>
            </div>
          </div>

          <div class="flexspacer"></div>
          <div class="grp">
            <button class="action" @click="onSave" :disabled="saving || isDrawingOnTestCanvas">
              <span v-if="saving">saving…</span><span v-else>save look!</span>
            </button>
            <button v-if="!isDrawingOnTestCanvas" class="action danger" @click="handleClearClick">{{ clearButtonText }}</button>
          </div>
        </div>
      </div>

      <div class="right-column-paint">
        <!-- BBY Canvas -->
        <div v-if="!isDrawingOnTestCanvas" class="bby-stage">
          <bbyPixels
            ref="bbyPixelsRef"
            :mode="currentMode"
            :is-scope-cursor-active="isScopeCursorActive"
            :active-e-qs="activeEQs"
            :hex-color="hexColor"
            :user-set-color="userColour"
            :bby-color="currentColour"
            :rainbow-influence="rainbowInfluence"
            :bby-influence="bbyInfluence"
            :user-color-influence="userColorInfluence"
            :red-influence="redInfluence"
            :green-influence="greenInfluence"
            :blue-influence="blueInfluence"
            :tempo="tempo"
            :blend-opacity="blendOpacity"
            @color-picked="handleColorPicked"
            @color-hovered="handleColorHovered"
          />
        </div>

        <!-- Test Canvas -->
        <div v-else class="test-canvas-stage" :style="{ width: testCanvasSize + '%' }">
          <div class="test-canvas-wrapper">
            <bbyPixels
              ref="testSquareRef"
              :key="testCanvasResolution"
              :sprite-width="testCanvasResolution"
              :sprite-height="testCanvasResolution"
              :is-test-canvas="true"
              :resolution="testCanvasResolution"
              :mode="currentMode"
              :is-scope-cursor-active="isScopeCursorActive"
              :active-e-qs="activeEQs"
              :hex-color="hexColor"
              :user-set-color="userColour"
              :bby-color="currentColour"
              :rainbow-influence="rainbowInfluence"
              :bby-influence="bbyInfluence"
              :user-color-influence="userColorInfluence"
              :red-influence="redInfluence"
              :green-influence="greenInfluence"
              :blue-influence="blueInfluence"
              :tempo="tempo"
              :blend-opacity="blendOpacity"
              @color-picked="handleColorPicked"
              @color-hovered="handleColorHovered"
            />
          </div>
          <div class="test-controls-bar">
            <button class="action mini" @click="testControlsMinimized = !testControlsMinimized">
              {{ testControlsMinimized ? 'Show Controls' : 'Hide Controls' }}
            </button>
            <template v-if="!testControlsMinimized">
              <testCanvasControls
                v-model:size="testCanvasSize"
                v-model:resolution="testCanvasResolution"
                @clear="handleClearTestSquareClick"
              />
              <div class="save-group">
                <input
                  v-if="saveConfirmClicks > 0"
                  v-model="saveLabel"
                  placeholder="name (optional)"
                />
                <button class="action" @click="handleSaveTestSquareClick">
                  {{ saveButtonText }}
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <div v-if="toast" class="save-toast">{{ toast }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, onBeforeUnmount, reactive } from 'vue';
import bbyPixels from '@/components/bbyPixels.vue';
import testCanvasControls from '@/components/testCanvasControls.vue';
import swatchDrawer from '@/components/swatchDrawer.vue';
import colourScope from '@/components/colourScope.vue';
import { bbyUse } from '@/composables/bbyUse.ts';
import bubbleGraveyard from '@/components/bubbleGraveyard.vue';
import tempoFader from '@/components/tempoFader.vue';
const { currentColour, saveCompositeToServer, pollActivityForAutosnap, userColour, author, saveTestGridImage } = bbyUse();

type Mode = 'paint' | 'blend' | 'erase' | 'eyedropper';
type RgbColor = { r: number; g: number; b: number };
type RgbaColor = { r: number; g: number; b: number; a: number };
type EQType = 'user' | 'bby' | 'red' | 'green' | 'blue' | 'rainbow';
type LfoWaveform = 'sine' | 'triangle' | 'square' | 'sawtooth' | 'ramp' | 'random' | 'sequence';
type InfluenceTarget = 'rainbowInfluence' | 'bbyInfluence' | 'userColorInfluence' | 'redInfluence' | 'greenInfluence' | 'blueInfluence';
type ResizeDirection = 'left' | 'right' | 'top' | 'bottom';

let animationFrameId: number | null = null;
const LFO_DURATION_MIN = 0.1;
const LFO_DURATION_MAX = 4.0;

const isDrawingOnTestCanvas = ref(false);
const testCanvasSize = ref(80);
const testCanvasResolution = ref(32);
const testControlsMinimized = ref(false);
const currentMode = ref<Mode>('paint');
const isScopeCursorActive = ref(false);
const isScopeMinimized = ref(false);
const activeEQs = ref(new Set<EQType>());

// Number of future pixel colours to preview
const scopeLength = ref(32);

const hexColor = ref('#88aaff');
const swatchesOpen = ref(false);
const swatches = ['#FFFFFF','#C2C2C2','#858585','#474747','#000000','#2E1A47','#FF5A5A','#FF965A','#FFD25A','#FFF05A','#C8FF5A','#78FF5A','#5AFFC8','#5AFFFF','#5AC8FF','#5A78FF','#965AFF','#E15AFF'];
const bbyPixelsRef = ref<InstanceType<typeof bbyPixels> | null>(null);
const testSquareRef = ref<InstanceType<typeof bbyPixels> | null>(null);
const saving = ref(false);
const toast = ref('');
const saveLabel = ref('');
const saveConfirmClicks = ref(0);
const saveButtonText = computed(() =>
  saveConfirmClicks.value === 0 ? 'Save to Gallery' : 'Click again to save'
);
const eyedropperHoverColor = ref<string | null>(null);

const tempo = ref(120);
const userColorInfluence = ref(0);
const bbyInfluence = ref(0);
const redInfluence = ref(0);
const greenInfluence = ref(0);
const blueInfluence = ref(0);
const rainbowInfluence = ref(0);

const lfoMode = ref<'shape'|'pixel'>('shape');
type LfoConfig = { wave: LfoWaveform, rate: number, depth: number } | { sequence: number[][] };
const lfoAssignments = reactive<Record<InfluenceTarget, LfoConfig | null>>({
  rainbowInfluence: null, bbyInfluence: null, userColorInfluence: null, redInfluence: null, greenInfluence: null, blueInfluence: null
});
const initialInfluenceValues = reactive<Record<InfluenceTarget, number>>({
  rainbowInfluence: 0, bbyInfluence: 0, userColorInfluence: 0, redInfluence: 0, greenInfluence: 0, blueInfluence: 0
});

// Shape LFO box
const currentLfo = reactive<{wave: LfoWaveform | null, width: number, height: number, rate: number, depth: number, animProgress: number}>({
  wave: null, width: 80, height: 40, rate: 1, depth: 0.5, animProgress: 0
});
const lfoShaper = ref<HTMLDivElement | null>(null);

// Pixel LFO
const sequencerCols = ref(3);
const sequencerRows = ref(2);
const sequencerGrid = ref(
  Array.from({ length: sequencerCols.value }, () =>
    Array(sequencerRows.value).fill(0)
  )
);
const sequencerCanvas = ref<HTMLCanvasElement | null>(null);
let isDrawingOnSequencer = false;

// helpers
const clamp = (v:number, mi:number, ma:number)=>Math.max(mi, Math.min(ma, v));
const clampByte = (x:number)=>Math.max(0, Math.min(255, Math.round(x)));
const rgbToHex = (r:number,g:number,b:number)=>"#"+[r,g,b].map(x=>{const h=clampByte(x).toString(16);return h.length===1?'0'+h:h;}).join('');
const hexToRGB = (hx:string): RgbColor => { const h=hx.replace('#',''); return {r:parseInt(h.slice(0,2),16), g:parseInt(h.slice(2,4),16), b:parseInt(h.slice(4,6),16)}; };
const isColorDark = ({ r, g, b }: RgbColor): boolean => (r * 0.299 + g * 0.587 + b * 0.114) < 128;

// number formatting + controls
function format2(n:number|{value:number}){ const v=typeof n==='number'?n:(n as any).value; return (Math.round(v*100)/100).toFixed(2); }
function stepForEvent(e: WheelEvent | KeyboardEvent) {
  // Shift=0.1, Alt=5, default=1
  const k = (e as KeyboardEvent).key;
  if (k === 'ArrowUp' || k === 'ArrowDown') {
    if ((e as KeyboardEvent).shiftKey) return 0.1;
    if ((e as KeyboardEvent).altKey) return 5;
    return 1;
  }
  if ((e as WheelEvent).shiftKey) return 0.1;
  if ((e as WheelEvent).altKey) return 5;
  return 1;
}
function setInfluence(target: InfluenceTarget, next:number) { influenceRefs[target].value = Math.round(clamp(next, -100, 100)*100)/100; }
function onWheelAdjust(e:WheelEvent, target:InfluenceTarget){ e.preventDefault(); const dir = e.deltaY>0?-1:1; const step=stepForEvent(e); setInfluence(target, influenceRefs[target].value + dir*step); }
function onKeyAdjust(e:KeyboardEvent, target:InfluenceTarget){
  if(e.key!=='ArrowUp'&&e.key!=='ArrowDown') return;
  e.preventDefault();
  const dir = e.key==='ArrowUp'?1:-1; const step=stepForEvent(e);
  setInfluence(target, influenceRefs[target].value + dir*step);
}
function onNumberEdit(e:Event, target:InfluenceTarget){
  const t=e.target as HTMLInputElement;
  const parsed=parseFloat(t.value.replace(/[^\d.-]/g,''));
  const val=isNaN(parsed)?0:clamp(parsed,-100,100);
  setInfluence(target, val);
}

const blendOpacity = computed(() => {
  const total = Math.abs(userColorInfluence.value)+Math.abs(bbyInfluence.value)+Math.abs(redInfluence.value)+Math.abs(greenInfluence.value)+Math.abs(blueInfluence.value);
  return clamp(total / 5, 0, 100);
});

const modeBtn = (m: Mode) => ['action', {active: currentMode.value === m}];
const bbyButtonStyle = computed(() => { const rgb = {r: Math.round(currentColour.r), g: Math.round(currentColour.g), b: Math.round(currentColour.b)}; return { backgroundColor: `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`, color: isColorDark(rgb) ? '#FFF' : '#000', textShadow: '1px 1px 2px rgba(0,0,0,0.7)' } });
const userButtonStyle = computed(() => { const {r,g,b} = userColour.value; return { backgroundColor: `rgb(${r}, ${g}, ${b})`, color: isColorDark({r,g,b}) ? '#FFF' : '#000', textShadow: '1px 1px 2px rgba(0,0,0,0.7)' } });
const eyedropperStyle = computed(() => { if (currentMode.value === 'eyedropper' && eyedropperHoverColor.value) { const color = hexToRGB(eyedropperHoverColor.value); return { backgroundColor: eyedropperHoverColor.value, color: isColorDark(color) ? '#FFF' : '#000' }; } return {}; });

const userKnobColor = computed(() => `rgb(${userColour.value.r},${userColour.value.g},${userColour.value.b})`);
const bbyKnobColor = computed(() => `rgb(${Math.round(currentColour.r)},${Math.round(currentColour.g)},${Math.round(currentColour.b)})`);
const userAcronym = computed(() => { const name = author.value || 'USER'; if (name.length > 4) { const words = name.split(/[\s-]+/); return words.map(w => w[0]).join('').toUpperCase().slice(0, 4); } return name.toUpperCase(); });

const toolModeDescription = computed(() => {
  if (currentMode.value === 'paint') return "EQs control colour drift";
  if (currentMode.value === 'blend') return "Mix brush colour with existing pixel; EQs & Tempo control strength";
  if (currentMode.value === 'erase') return "EQs & Tempo control erase strength";
  if (currentMode.value === 'eyedropper') return "Hover canvas to sample colour";
  return "";
});

function setMode(mode: Mode) { currentMode.value = mode; if (mode !== 'eyedropper') eyedropperHoverColor.value = null; if (mode === 'eyedropper') activeEQs.value.clear(); }
function setPickerToBbyColor() { hexColor.value = rgbToHex(Math.round(currentColour.r), Math.round(currentColour.g), Math.round(currentColour.b)); }
function setPickerToUserColor() { hexColor.value = rgbToHex(userColour.value.r, userColour.value.g, userColour.value.b); }

// knob mapping (fixes USER)
const eqToTarget: Record<EQType, InfluenceTarget> = {
  user: 'userColorInfluence',
  bby: 'bbyInfluence',
  red: 'redInfluence',
  green: 'greenInfluence',
  blue: 'blueInfluence',
  rainbow: 'rainbowInfluence',
};
const influenceRefs: {[k in InfluenceTarget]: typeof rainbowInfluence} = { rainbowInfluence, bbyInfluence, userColorInfluence, redInfluence, greenInfluence, blueInfluence };

function toggleEQ(eq: EQType) {
  const target = eqToTarget[eq];
  if (activeEQs.value.has(eq)) { activeEQs.value.delete(eq); influenceRefs[target].value = 0; }
  else { activeEQs.value.add(eq); if (influenceRefs[target].value === 0) influenceRefs[target].value = 5; } // jump to 5
}
watch(currentMode, (newMode) => { if (newMode === 'eyedropper') activeEQs.value.clear(); });

// rotations (only the needle uses these)
const rainbowInfluenceDialRotation = computed(() => (rainbowInfluence.value / 100) * 135);
const userColorInfluenceDialRotation = computed(() => (userColorInfluence.value / 100) * 135);
const bbyInfluenceDialRotation = computed(() => (bbyInfluence.value / 100) * 135);
const redInfluenceDialRotation = computed(() => (redInfluence.value / 100) * 135);
const greenInfluenceDialRotation = computed(() => (greenInfluence.value / 100) * 135);
const blueInfluenceDialRotation = computed(() => (blueInfluence.value / 100) * 135);

let dragStartY = 0, dragStartValue = 0;
let activeDial: InfluenceTarget | null = null;

function startDialDrag(e: MouseEvent, dial: EQType) {
  const target = eqToTarget[dial];
  if (!activeEQs.value.has(dial)) return;
  activeDial = target; dragStartY = e.clientY;
  dragStartValue = influenceRefs[target].value;
  window.addEventListener('mousemove', onDialDrag); window.addEventListener('mouseup', stopDialDrag);
}
function onDialDrag(e: MouseEvent) {
  if (!activeDial) return;
  const newValue = dragStartValue - (e.clientY - dragStartY);
  setInfluence(activeDial, newValue);
}
function stopDialDrag() { activeDial = null; window.removeEventListener('mousemove', onDialDrag); window.removeEventListener('mouseup', stopDialDrag); }

// LFO SVGs + drag
const waveSVGs: Record<LfoWaveform, string> = {
  sine: `<svg viewBox="0 0 100 100"><path d="M 0 50 C 25 0, 75 100, 100 50" stroke="currentColor" fill="none" stroke-width="12" stroke-linecap="round"/></svg>`,
  triangle: `<svg viewBox="0 0 100 100"><path d="M 0 100 L 50 0 L 100 100" stroke="currentColor" fill="none" stroke-width="12" stroke-linejoin="round" stroke-linecap="round"/></svg>`,
  square: `<svg viewBox="0 0 100 100"><path d="M 0 0 L 50 0 L 50 100 L 100 100" stroke="currentColor" fill="none" stroke-width="12" stroke-linecap="round"/></svg>`,
  sawtooth: `<svg viewBox="0 0 100 100"><path d="M 0 100 L 100 0" stroke="currentColor" fill="none" stroke-width="12" stroke-linecap="round"/></svg>`,
  ramp: `<svg viewBox="0 0 100 100"><path d="M 0 0 L 100 100" stroke="currentColor" fill="none" stroke-width="12" stroke-linecap="round"/></svg>`,
  random: `<svg viewBox="0 0 100 100"><path d="M 0 50 L 10 20 L 20 80 L 30 30 L 40 70 L 50 10 L 60 90 L 70 40 L 80 60 L 90 20 L 100 50" stroke="currentColor" fill="none" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"/></svg>`,
  sequence: `<svg viewBox="0 0 16 16" stroke="currentColor" stroke-width="1.5" fill="none"><path d="M2.25 4.25h5.5M2.25 8.25h11.5M2.25 12.25h3.5"/></svg>`
};
const presetWaves: LfoWaveform[] = ['sine','triangle','square','sawtooth','ramp','random'];
function getWaveSvg(wave?: LfoWaveform | null) { return wave ? waveSVGs[wave] : ''; }
function handleWaveBankDragStart(e: DragEvent, wave: LfoWaveform) { if(e.dataTransfer) e.dataTransfer.setData('text/plain', wave); }
function handleShaperDragStart(e: DragEvent) { if(e.dataTransfer) e.dataTransfer.setData('application/json', JSON.stringify({wave: currentLfo.wave, rate: currentLfo.rate, depth: currentLfo.depth})); }
function handleSequencerDragStart(e: DragEvent) { if(e.dataTransfer) { e.dataTransfer.setData('application/json', JSON.stringify({ sequence: sequencerGrid.value })); e.dataTransfer.effectAllowed = 'copy'; e.dataTransfer!.setData('text/plain', 'sequence');} e.dataTransfer!.setDragImage(sequencerCanvas.value!, 0, 0);}
function onShaperDrop(e: DragEvent) { if(e.dataTransfer) { const wave = e.dataTransfer.getData('text/plain') as LfoWaveform; if(wave) { currentLfo.wave = wave; currentLfo.width = 80; currentLfo.height = 40; updateLfoFromDimensions(); } } }
function onKnobDrop(e: DragEvent, target: InfluenceTarget) {
  if(!e.dataTransfer) return;
  const configStr = e.dataTransfer.getData('application/json');
  const text = e.dataTransfer.getData('text/plain');
  if (configStr) {
    const config = JSON.parse(configStr);
    if (lfoAssignments[target] === null) initialInfluenceValues[target] = influenceRefs[target].value;
    lfoAssignments[target] = config; // { sequence: grid }
  } else if (text) {
    // wave from bank
    const wave = text as LfoWaveform;
    if (lfoAssignments[target] === null) initialInfluenceValues[target] = influenceRefs[target].value;
    lfoAssignments[target] = { wave, rate: currentLfo.rate || 1, depth: currentLfo.depth || 0.5 };
  }
}
function clearLfo(target: InfluenceTarget) { if (lfoAssignments[target] !== null) { influenceRefs[target].value = initialInfluenceValues[target] ?? 0; lfoAssignments[target] = null; } }

type RD = ResizeDirection;
let resizeDirection: RD | null = null;
let startX=0, startY=0, startW=0, startH=0;
function handleResizeMouseDown(e: MouseEvent, dir: RD) {
  resizeDirection = dir; startX = e.clientX; startY = e.clientY; startW = currentLfo.width; startH = currentLfo.height;
  window.addEventListener('mousemove', handleResizeMouseMove); window.addEventListener('mouseup', handleResizeMouseUp);
}
function handleResizeMouseMove(e: MouseEvent) {
  if (!resizeDirection || !lfoShaper.value) return;
  const dx = e.clientX - startX, dy = e.clientY - startY;
  const shaperWidth = lfoShaper.value.clientWidth, shaperHeight = lfoShaper.value.clientHeight;
  if (resizeDirection === 'right') currentLfo.width = clamp(startW + dx, 20, shaperWidth);
  if (resizeDirection === 'left')  currentLfo.width = clamp(startW - dx, 20, shaperWidth);
  if (resizeDirection === 'bottom') currentLfo.height = clamp(startH + dy, 10, shaperHeight);
  if (resizeDirection === 'top')   currentLfo.height = clamp(startH - dy, 10, shaperHeight);
  updateLfoFromDimensions();
}
function handleResizeMouseUp() { resizeDirection = null; window.removeEventListener('mousemove', handleResizeMouseMove); window.removeEventListener('mouseup', handleResizeMouseUp); }
function updateLfoFromDimensions() {
  if (!lfoShaper.value) return;
  const wNorm = (currentLfo.width / lfoShaper.value.clientWidth); // 0..1
  const hNorm = (currentLfo.height / lfoShaper.value.clientHeight); // 0..1
  const duration = LFO_DURATION_MIN + wNorm * (LFO_DURATION_MAX - LFO_DURATION_MIN);
  currentLfo.rate = 1 / duration; // feel-normal mapping
  currentLfo.depth = hNorm;
}

function getLfoWaveform(config: LfoConfig | null): LfoWaveform | null { if (!config) return null; return 'sequence' in config ? 'sequence' : config.wave; }

function lfoLoop(time: number) {
  const t = time / 1000;
  if (currentLfo.wave) currentLfo.animProgress = (t * currentLfo.rate) % 1;

  for (const key in lfoAssignments) {
    const target = key as InfluenceTarget;
    const config = lfoAssignments[target];
    if (!config) continue;

    let lfoValue = 0; // 0..1
    if ('sequence' in config) {
      const beatsPerSecond = tempo.value / 60;
      const totalBeats = t * beatsPerSecond;
      const seq: number[][] = config.sequence;
      const stepCount = seq.length;                 // columns = steps
      const stepDuration = 4 / stepCount;           // 4-beat loop
      const currentStep = Math.floor((totalBeats % 4) / stepDuration);
      const column = seq[clamp(currentStep,0,stepCount-1)];
      let yIndex = -1;
      if (column) { yIndex = column.findIndex(v => v > 0); }
      // top row = 1 → value=1; bottom row = res-1 → value~0
      lfoValue = yIndex === -1 ? 0.5 : 1 - (yIndex / (sequencerRows.value - 1));
    } else {
      const phase = (t * config.rate) % 1;
      switch(config.wave) {
        case 'sine':     lfoValue = (Math.sin(phase * 2 * Math.PI) + 1) / 2; break;
        case 'triangle': lfoValue = 1 - Math.abs(2 * phase - 1); break;
        case 'square':   lfoValue = phase < 0.5 ? 1 : 0; break;
        case 'sawtooth': lfoValue = 1 - phase; break;
        case 'ramp':     lfoValue = phase; break;
        case 'random':   lfoValue = Math.random(); break;
      }
    }
    const depth = ('depth' in (config as any)) ? (config as any).depth : 1;
    const modulation = (lfoValue - 0.5) * 2 * 100 * depth;
    influenceRefs[target].value = Math.round(clamp((initialInfluenceValues[target] ?? 0) + modulation, -100, 100) * 100) / 100;
  }
  animationFrameId = requestAnimationFrame(lfoLoop);
}

// Sequencer
function drawSequencer(totalBeats?: number) {
  const canvas = sequencerCanvas.value; if (!canvas) return;
  const ctx = canvas.getContext('2d'); if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  const resX = sequencerCols.value;
  const resY = sequencerRows.value;

  canvas.width = canvas.clientWidth * dpr;
  canvas.height = canvas.clientHeight * dpr;
  ctx.setTransform(dpr,0,0,dpr,0,0);

  const w = canvas.clientWidth, h = canvas.clientHeight;
  const cellW = w / resX, cellH = h / resY;

  ctx.clearRect(0,0,w,h);
  ctx.strokeStyle = "rgba(255,255,255,0.1)";
  for(let i=1;i<resX;i++){ ctx.beginPath(); ctx.moveTo(i*cellW,0); ctx.lineTo(i*cellW,h); ctx.stroke(); }
  for(let i=1;i<resY;i++){ ctx.beginPath(); ctx.moveTo(0,i*cellH); ctx.lineTo(w,i*cellH); ctx.stroke(); }

  for(let x=0;x<resX;x++){
    for(let y=0;y<resY;y++){
      const val = sequencerGrid.value[x][y];
      if(val>0){
        ctx.fillStyle="var(--accent-colour)";
        ctx.globalAlpha = val;
        ctx.fillRect(x*cellW, y*cellH, cellW, cellH);
      }
    }
  }
  ctx.globalAlpha=1;

  if (totalBeats !== undefined) {
    const stepDuration = 4 / resX;
    const currentStep = Math.floor((totalBeats % 4) / stepDuration);
    ctx.fillStyle = "rgba(255,255,255,0.3)";
    ctx.fillRect(currentStep * cellW, 0, cellW, h);
  }
}
function applyPreset(wave: LfoWaveform) {
  const resX = sequencerCols.value;
  const resY = sequencerRows.value;
  const grid = Array.from({ length: resX }, () => Array(resY).fill(0));
  for(let x=0;x<resX;x++){
    const phase = x/(resX-1); let yNorm=0;
    switch(wave){
      case 'sine':     yNorm = (Math.sin(phase*2*Math.PI)*-1+1)/2; break;
      case 'triangle': yNorm = 1 - Math.abs(2*(phase+0.25)-1); break;
      case 'square':   yNorm = (phase<0.5)?0:1; break;
      case 'sawtooth': yNorm = 1-phase; break;
      case 'ramp':     yNorm = phase; break;
      case 'random':   for(let y=0;y<resY;y++) grid[x][y] = Math.random()>0.5?1:0; continue;
    }
    const y = Math.floor(yNorm*(resY-1));
    if(y>=0&&y<resY) grid[x][y]=1;
  }
  sequencerGrid.value = grid;
  drawSequencer();
}
function clearSequencer(){
  const cols = sequencerCols.value, rows = sequencerRows.value;
  sequencerGrid.value = Array.from({length:cols},()=>Array(rows).fill(0));
  drawSequencer();
}
function setSequencerResolution(cols:number, rows:number){
  sequencerCols.value=cols;
  sequencerRows.value=rows;
  clearSequencer();
}
function handleSequencerPointerDown(e:PointerEvent){ isDrawingOnSequencer=true; updateSequencerFromPointer(e); }
function handleSequencerPointerMove(e:PointerEvent){ if(isDrawingOnSequencer) updateSequencerFromPointer(e); }
function handleSequencerPointerUp(){ isDrawingOnSequencer=false; }
function updateSequencerFromPointer(e:PointerEvent){
  const canvas = sequencerCanvas.value; if(!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const resX = sequencerCols.value;
  const resY = sequencerRows.value;
  const x = e.clientX-rect.left, y = e.clientY-rect.top;
  const cellX = clamp(Math.floor(x/(rect.width/resX)),0,resX-1);
  const cellY = clamp(Math.floor(y/(rect.height/resY)),0,resY-1);
  sequencerGrid.value[cellX].fill(0);
  sequencerGrid.value[cellX][cellY]=1;
  drawSequencer();
}
onMounted(() => { animationFrameId = requestAnimationFrame(lfoLoop); drawSequencer(); });
onBeforeUnmount(() => { if (animationFrameId) cancelAnimationFrame(animationFrameId); });

// actions
function showToast(msg:string, ms=1500){ toast.value=msg; setTimeout(()=>toast.value='', ms); }
async function onSave(){ if(saving.value) return; saving.value=true; try{ const label=prompt('Label for this look? (optional)','')||'manual'; const url=await saveCompositeToServer(label); showToast('saved — opening…'); window.open(url,'_blank'); }catch(e){console.error(e); showToast('not saved :(',2000);} finally{saving.value=false;} }
onMounted(()=>{ pollActivityForAutosnap(); });
let clearResetTimer: ReturnType<typeof setTimeout> | null = null;
const clearConfirmClicks = ref(0);
const clearButtonText = computed(() => { switch (clearConfirmClicks.value) { case 0: return 'Clear canvas'; case 1: return 'Are you sure?'; case 2: return 'Final click to clear!'; default: return 'Clear canvas'; } });
function handleClearClick() {
  if (clearResetTimer) clearTimeout(clearResetTimer);
  clearConfirmClicks.value++;
  if (clearConfirmClicks.value >= 3) { bbyPixelsRef.value?.clearOverlay(); showToast('Canvas Cleared!', 2000); clearConfirmClicks.value = 0; }
  else { showToast(clearConfirmClicks.value === 1 ? 'First click! Are you sure?' : 'SECOND CLICK! One more erases all!', 3000); clearResetTimer = setTimeout(() => { clearConfirmClicks.value = 0; showToast('Clear cancelled.', 1500); }, 3000); }
}
function handleClearTestSquareClick() {
  testSquareRef.value?.clearOverlay();
  showToast('Test Square Cleared!', 1500);
}
async function handleSaveTestSquareClick() {
  if (!testSquareRef.value) return;
  if (saveConfirmClicks.value === 0) {
    saveConfirmClicks.value = 1;
    showToast('Add a name and click again to save', 3000);
    return;
  }
  try {
    const canvas = testSquareRef.value.exportCanvas();
    if (!canvas) return;
    const url = await saveTestGridImage(
      canvas,
      author.value,
      saveLabel.value || `test-${testCanvasResolution.value}x${testCanvasResolution.value}` // Use the input, with a fallback
    );
    showToast('Saved to gallery!', 2000);
    window.open(url, '_blank');
  } catch (e: any) {
    console.error('[gallery/save] failed:', e?.message || e);
    showToast('Save failed :(  (check console)', 2500);
  } finally {
    saveConfirmClicks.value = 0;
    saveLabel.value = '';
  }
}

function setSwatchColor(c:string){ hexColor.value=c; if (currentMode.value !== 'paint') setMode('paint'); }
function handleColorPicked(c:string){ hexColor.value=c; if (currentMode.value === 'eyedropper') setMode('paint'); }
function handleColorHovered(color: RgbaColor | null) { if (color && color.a > 0) { eyedropperHoverColor.value = rgbToHex(color.r, color.g, color.b); } else { eyedropperHoverColor.value = null; } }
</script>

<style scoped>
.page-container{display:flex;width:100%;height:var(--full-height);box-sizing:border-box;padding:var(--padding)}
.paint-page-layout{display:flex;flex-direction:row;width:100%;height:100%;gap:var(--spacing);overflow:hidden}
.left-column-paint{flex:1 1 320px;min-width:280px;height:100%;display:flex;flex-direction:column}
.vertical-panel{position: relative; width:100%;height:100%;overflow-y:auto;padding:var(--padding);background:var(--panel-colour);border:var(--border);border-radius:var(--border-radius);box-shadow:var(--box-shadow);display:flex;flex-direction:column;gap:calc(var(--spacing)*1.1)}
.right-column-paint{flex:0 1 var(--full-height);display:flex;align-items:center;justify-content:center;height:100%;max-width:var(--full-height);min-width:0}

.bby-stage {display:flex;align-items:center;justify-content:center;width:100%;height:auto;max-width:100%;max-height:100%;aspect-ratio:1/1;}
.test-canvas-stage {display:flex;flex-direction:column;align-items:center;justify-content:center;width:80%;max-width:100%;max-height:100%;gap:var(--spacing);aspect-ratio:1/1;transition: width .3s ease;}
.test-canvas-wrapper { width: 100%; aspect-ratio: 1/1; border: var(--border); border-radius: var(--border-radius); overflow: hidden; }
.test-controls-bar{display:flex;align-items:center;gap:.5rem;width:100%;flex-wrap:nowrap;justify-content:center;}
.bby-stage > *, .test-canvas-wrapper > * {max-width:100%;max-height:100%}

.vertical-panel h1{margin:0;text-align:center;line-height:1.05}
.grp{display:flex;flex-direction:column;gap:.5rem}
.save-group{display:flex;align-items:center;gap:.5rem}
.save-group input{padding:.4rem;border:var(--border);border-radius:var(--border-radius);}
.section{font-size:var(--small-font-size);text-align:center;opacity:.85;letter-spacing:.1em;text-transform: uppercase;}
.row3{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem}
.action{display:block;width:100%; padding:.4rem .5rem; transition: all 0.2s ease-out; text-align:center;}
.action.active, .action:active, .action.eyedropper-active {background:var(--accent-hover);border-color:var(--accent-colour) !important}
.action.eyedropper-active { background-color: v-bind(eyedropperHoverColor); }
.action.mini { padding: 2px 6px; font-size: .65rem; }
.base-color-row { display: flex; gap: .5rem; align-items: stretch; }
.colour-input-main { flex-grow: 1; min-width: 0; height: auto; border: var(--border); border-radius: var(--border-radius); box-shadow: var(--box-shadow); background: var(--bby-colour-black); padding: 0; cursor: pointer; -webkit-appearance: none; appearance: none; }
.colour-input-main::-webkit-color-swatch-wrapper { padding: 0 }
.colour-input-main::-webkit-color-swatch { border: none; border-radius: calc(var(--border-radius) * .8) }
.base-color-tools { display: flex; gap: .5rem; }
.flexspacer{flex:1 1 auto}
.action.danger{background:#e94560;border-color:#fff;color:#fff;font-weight:900}
@media (max-width:720px){.paint-page-layout{flex-direction:column}.left-column-paint{width:100%;flex-basis:auto;height:auto}.vertical-panel{overflow-y:visible}.right-column-paint{width:100%;max-width:none;flex:0 0 auto}}
.controls-container { display: flex; gap: var(--spacing); flex-direction: row; max-height: 60vh;}
.fader-box { flex: 0 0 auto; background: var(--bby-colour-black); padding: var(--spacing); border-radius: var(--border-radius); border: var(--border); display: flex; flex-direction: column; align-items: center; gap: calc(var(--spacing)/2); }
.fader-value { font-size: 0.7rem; background: var(--bby-colour-dark); padding: 2px 4px; border-radius: 4px; }
.mixer-column { display: flex; flex-direction: column; gap: var(--spacing); flex: 1 1 auto; min-width: 0; }
.knob-box { flex: 1 1 auto; background: var(--bby-colour-black); padding: var(--spacing); border-radius: var(--border-radius); border: var(--border); display: flex; flex-direction: column; gap: var(--spacing); }
.fader-label { font-size: 0.7rem; font-weight: bold; writing-mode: vertical-rl; transform: rotate(180deg); color: rgba(255,255,255,0.7); }
.fader { -webkit-appearance: slider-vertical; appearance: slider-vertical; width: 10px; height: 100%; background: var(--bby-colour-dark); outline: none; border-radius: 5px; cursor: ns-resize; }

.knob-bank { display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: auto; gap: var(--spacing); justify-items: center; }
.dial-grp { display: flex; flex-direction: column; align-items: center; gap: .25rem; color: rgba(255, 255, 255, 0.4); transition: color 0.2s ease-out; }
.dial-grp.active { color: #fff; }
.dial-grp:not(.active) .dial-container, .dial-grp:not(.active) .dial-input-box { pointer-events: none; filter: grayscale(50%); opacity: 0.6; }
.dial-grp.active .dial-knob { border-color: var(--knob-glow); box-shadow: 0 0 12px var(--knob-glow), inset 0 0 8px rgba(0,0,0,0.5); }
.dial-grp.active .dial-label { color: var(--knob-glow); text-shadow: 0 0 4px var(--knob-glow); font-weight: bold; }

.dial-container { position: relative; width: min(100%, 200px); aspect-ratio: 1/1; flex-shrink: 0; border-radius: 50%; }
.dial-knob { width: 100%; height: 100%; border: 6px solid var(--bby-colour-dark); border-radius: 50%; background-color: var(--bby-colour-black); position: relative; display:flex; align-items:center; justify-content:center; }
.dial-knob.rainbow-knob { background-image: linear-gradient(to right, #ff5a5a, #ffd25a, #c8ff5a, #5affc8, #5a78ff, #e15aff); }
.dial-needle { position:absolute; top:6px; left:50%; width:4px; height:12px; background: var(--accent-colour); border-radius:2px; transform-origin: 50% 100%; translate: -50% 0; }

.dial-label-area { display:flex; flex-direction:column; align-items:center; z-index:1; pointer-events:all; }
.dial-label { font-size:var(--font-size); text-align:center; letter-spacing:.1em; text-transform: uppercase; transition: all 0.2s ease-out; line-height: 1.1; cursor: pointer; }
.dial-input-box { width: 72%; background: transparent; border: none; color: inherit; font-size: 0.65rem; text-align: center; padding: 0; }
.dial-input-box:focus { outline: none; }

.mode-info-display { background: var(--bby-colour-darker, #111); color: rgba(255,255,255,0.7); text-align: center; padding: 4px; border-radius: 4px; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; border: 1px solid var(--bby-colour-dark); }

.lfo-section { background: var(--bby-colour-black); padding: var(--spacing); border-radius: var(--border-radius); border: var(--border); }
.lfo-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--spacing); }
.lfo-mode-toggles { display: flex; background: var(--bby-colour-dark); border-radius: var(--border-radius); padding: 2px; }
.lfo-mode-toggles > .action { padding: 2px 8px; font-size: 0.7rem; background: transparent; border-color: transparent; }
.lfo-mode-toggles > .action.active { background: var(--accent-colour); }
.lfo-main-area { display: flex; gap: var(--spacing); min-height: 136px; }
.lfo-bank { display: flex; flex-direction: column; gap: var(--spacing); max-height: 136px; /* (40px * 3) + (spacing * 2) */ overflow-y: auto; padding-right: var(--spacing); }

.preset-btn { padding: 4px; width: 40px; height: 40px; flex-shrink: 0; font-weight: bold; }
.preset-svg { width: 100%; height: 100%; color: var(--font-colour); }
.wave-draggable { background: var(--bby-colour-dark); border-radius: var(--border-radius); padding: 4px; width: 40px; height: 40px; color: var(--font-colour); cursor: grab; transition: all .2s ease; flex-shrink: 0; }
.wave-draggable:hover { background: var(--bby-colour); transform: scale(1.05); }
.wave-draggable:active { cursor: grabbing; background: var(--accent-hover); }

.lfo-shaper, .sequencer-container { flex-grow: 1; background: var(--bby-colour-dark); border-radius: var(--border-radius); display: flex; align-items: center; justify-content: center; position: relative; height: 100%; min-height: 0; overflow: hidden; }
.sequencer-container { flex-direction: column; gap: var(--spacing); padding: var(--spacing); }
.sequencer-wrapper { width: 100%; height: 100%; max-width: 100%; max-height: 100%; aspect-ratio: 1/1; cursor: grab; }
.sequencer-wrapper:active { cursor: grabbing; }
.sequencer-canvas { width: 100%; height: 100%; cursor: crosshair; }
.sequencer-res-toggles { display: flex; gap: var(--spacing); width: 100%; }
.sequencer-res-toggles > .action { flex: 1; padding: 2px; font-size: 0.7rem; }

.shaper-prompt { font-size: 0.7rem; text-align: center; color: rgba(255,255,255,0.3); pointer-events: none; }
.shaper-content { position: relative; display: flex; align-items: center; justify-content: center; cursor: grab; }
.shaper-content:active { cursor: grabbing; }
.shaper-svg-wrapper { width: 100%; height: 100%; position: relative; }
.shaper-svg-bg { position: absolute; inset: 0; color: var(--font-colour); opacity: 0.2; }
.shaper-svg-animated { position: absolute; inset: 0; color: var(--accent-colour); }
.shaper-svg-animated :deep(svg), .shaper-svg-bg :deep(svg) { width: 100%; height: 100%; }

.resize-handle { position: absolute; background: rgba(255,255,255,0.5); }
.resize-handle:hover { background: white; }
.h-left, .h-right { width: 6px; height: 50%; top: 25%; cursor: ew-resize; }
.h-left { left: -3px; } .h-right { right: -3px; }
.v-top, .v-bottom { height: 6px; width: 50%; left: 25%; cursor: ns-resize; }
.v-top { top: -3px; } .v-bottom { bottom: -3px; }
.lfo-ghost { position: absolute; width: 40%; height: 40%; color: white; opacity: 0; animation: lfo-flicker 1s infinite; pointer-events: none; }
@keyframes lfo-flicker { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.7; } }
.lfo-ghost:deep(svg) { width: 100%; height: 100%; filter: drop-shadow(0 0 3px black); }
</style>