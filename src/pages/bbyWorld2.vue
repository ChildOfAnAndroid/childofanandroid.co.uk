<!-- CHARIS CAT // bbyWorld — 2025 -->
<template>
  <div class="page-container bbyworld-page">
    <div class="world-layout">
      <div class="world-left">
        <div class="vertical-panel">
          <h1 class="page-title">bbyWorld</h1>

          <div class="grp">
            <label class="section" for="board-size">board size</label>
            <div class="row3">
              <button class="action" @click="boardSize = Math.max(16, boardSize - 16)">-</button>
              <input id="board-size" type="number" v-model.number="boardSize" min="16" step="16" />
              <button class="action" @click="boardSize = Math.min(1024, boardSize + 16)">+</button>
            </div>
            <small style="opacity:.7">changing size clears the world</small>
          </div>

          <div class="grp">
            <label class="section">world</label>
            <button class="action" @click="clearWorld">clear</button>
          </div>

          <div class="grp">
            <label class="section">select a bby to place:</label>
            <div class="card-swatch-bar">
              <button
                v-for="card in cards"
                :key="card.label"
                class="card-swatch"
                :class="{ selected: selectedCardLabel === card.label }"
                @click="selectCard(card.label)"
              >
                <img :src="card.stamp_url || card.url" :alt="card.label" />
              </button>
            </div>
          </div>

          <div class="grp">
            <label class="section">stats</label>
            <div class="world-stats">
              <span>TIME: {{ elapsedTimeDisplay }}</span>
              <span>CELLS: {{ livingCells.length }}</span>
              <span>WAR: {{ stats.warDeaths }}</span>
              <span>BBY: {{ stats.babyMerges }}</span>
              <span>SQUISH: {{ stats.squishDeaths }}</span>
              <span>FADE: {{ stats.fadedDeaths }}</span>
              <span>AVG LIFE: {{ avgLifespan }}</span>
            </div>
          </div>

          <div class="grp">
            <label class="section">colour groups</label>
            <div class="group-stats">
              <div class="group-row header">
                <span>colour</span>
                <span>count</span>
                <span>%</span>
                <span>age</span>
                <span>energy</span>
                <span>strength</span>
              </div>
              <div
                class="group-row"
                v-for="g in sortedGroupStats"
                :key="g.colour"
                :class="{selected: highlightedGroup === g.colour}"
                @click="selectGroup(g.colour)"
              >
                <div class="group-bar" :style="{ background: g.colour, width: g.percentage + '%' }"></div>
                <span class="colour-cell">
                  <span class="colour-swatch" :style="{ background: g.colour }"></span>
                  {{ g.colour }}
                </span>
                <span>{{ g.count }}</span>
                <span>{{ g.percentage.toFixed(1) }}%</span>
                <span>{{ formatTicks(g.avgAge) }}</span>
                <span>{{ g.avgEnergy.toFixed(1) }}</span>
                <span>{{ g.avgStrength.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <div class="grp" v-if="selectedGroupInfo">
            <label class="section">group insight</label>
            <div class="group-insight">
              <span class="colour-swatch" :style="{ background: selectedGroupInfo.colour }"></span>
              <span>{{ selectedGroupInfo.message }}</span>
            </div>
          </div>

          <div class="grp" v-if="selectedCell">
            <label class="section">cell {{ selectedCell.id }} info</label>
            <div class="cell-stats">
              <div class="cell-colour">
                <span
                  class="colour-swatch"
                  :style="{ background: `rgba(${selectedCell.r},${selectedCell.g},${selectedCell.b},${selectedCell.a/255})` }"
                ></span>
                <span>{{ selectedCell.r }},{{ selectedCell.g }},{{ selectedCell.b }},{{ selectedCell.a }}</span>
              </div>
              <div>pos: {{ selectedCell.x }}, {{ selectedCell.y }}</div>
              <div>age: {{ formatTicks(selectedCell.age) }}</div>
              <div>energy: {{ selectedCell.energy.toFixed(1) }}</div>
              <div>strength: {{ selectedCell.strength.toFixed(2) }}</div>
              <div>aggr: {{ selectedCell.aggression.toFixed(2) }}</div>
              <div>fert: {{ selectedCell.fertility.toFixed(2) }}</div>
              <div>met: {{ selectedCell.metabolism.toFixed(2) }}</div>
              <div>cargo: {{ selectedCell.cargo.toFixed(1) }}</div>
              <div>solid cargo: {{ selectedCell.solidCargo.toFixed(2) }}</div>
              <div>spd: {{ selectedCell.speed }}</div>
            </div>
          </div>

          <div class="grp" v-if="selectedCell">
            <label class="section">cell {{ selectedCell.id }} family</label>
            <div class="family-tree">
              <div>
                parents:
                <template v-if="selectedFamily.parents.length">
                  <span
                    v-for="p in selectedFamily.parents"
                    :key="p.id"
                    class="family-link"
                    @click="selectCellById(p.id)"
                  >#{{ p.id }}</span>
                </template>
                <span v-else>none</span>
              </div>
              <div>
                children:
                <template v-if="selectedFamily.children.length">
                  <span
                    v-for="c in selectedFamily.children"
                    :key="c.id"
                    class="family-link"
                    @click="selectCellById(c.id)"
                  >#{{ c.id }}</span>
                </template>
                <span v-else>none</span>
              </div>
            </div>
          </div>

          <div class="grp">
            <label class="section" style="cursor:pointer" @click="showLegend = !showLegend">legend</label>
            <div class="legend" v-show="showLegend">
              <p><strong>physics:</strong> blue flows downward, red burns through terrain, green grows upwards</p>
              <p><strong>genetics:</strong> red bbys born fast, blue bbys born light, green bbys born strong</p>
              <p><strong>rules:</strong> blue gains energy in groups, red just wants to be on fire, green drinks from water</p>
              <p><strong>norms:</strong> green passes up, blue carries along, red destroys all</p>
              <p><strong>bbys:</strong> when two cells make un bby, they're a mixture of their parents. the little flashes on screen are them being born!</p>
              <p><strong>jobs:</strong> cells move toward the resources they need on the board.</p>
              <p><strong>stats:</strong> % shows each colour's share of living cells, age and energy group averages.</p>
            </div>
          </div>

          <div class="grp">
            <label class="section">speed ({{ ticksPerSecond }} TPS)</label>
            <div class="row3">
              <button class="action" @click="slowDown">-</button>
              <button class="action" @click="togglePause">{{ isPaused ? 'play' : 'pause' }}</button>
              <button class="action" @click="speedUp">+</button>
            </div>
          </div>

          <div class="grp">
            <label class="section">zoom</label>
            <div class="row3">
              <button class="action" @click="zoomOut">-</button>
              <div class="zoom-display">{{ (zoomFactor*100).toFixed(0) }}%</div>
              <button class="action" @click="zoomIn">+</button>
            </div>
            <button class="action" @click="scopeActive = !scopeActive" :class="{active: scopeActive}">scope</button>
            <button class="action" @click="resetView">reset view</button>
          </div>
        </div>
      </div>

      <div class="world-right">
        <div
          class="world-stage"
          ref="stageEl"
          @mousedown="startPan"
          @mousemove="onMouseMove"
          @mouseup="endPan"
          @mouseleave="endPan"
          @wheel.prevent="onWheelZoom"
          @contextmenu.prevent
        >
          <div class="stack">
            <canvas
              ref="gameCanvas"
              :width="boardSize"
              :height="boardSize"
              @click="placeImage"
              :style="canvasStyle"
            />
            <div v-show="scopeActive" ref="scopeBox" class="zoom-scope">
              <canvas ref="scopeCanvas"></canvas>
              <div class="scope-info">
                <div>{{ hoverEnv.x }},{{ hoverEnv.y }}</div>
                <div>
                  H {{ hoverEnv.heat.toFixed(2) }}
                  M {{ hoverEnv.moisture.toFixed(2) }}
                  N {{ hoverEnv.nutrient.toFixed(2) }}
                </div>
                <div v-if="hoverCell">
                  Age {{ formatTicks(hoverCell.age) }}
                  E {{ hoverCell.energy.toFixed(1) }}
                  S {{ hoverCell.strength.toFixed(2) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, onUnmounted, watch } from "vue";
import { throttle } from 'lodash';
import { bbyUse } from '@/composables/bbyUse.ts';

// pull Baby’s currentColour + gallery
const { fetchBbyBookGallery, currentColour } = bbyUse();

// world time constants
const TICKS_PER_DAY = 69;
const DAYS_PER_YEAR = 420;

function formatTicks(ticks: number) {
  const totalDays = Math.floor(ticks / TICKS_PER_DAY);
  const year = Math.floor(totalDays / DAYS_PER_YEAR);
  const day = totalDays % DAYS_PER_YEAR;
  return `Year ${year} Day ${day}`;
}

/* ============== BOARD SIZE (dynamic) ============== */
const boardSize = ref<number>(64);            // default 64×64
function S(){ return boardSize.value; }       // size getter everywhere

/* ===================== UI/Viewport ===================== */
const gameCanvas = ref<HTMLCanvasElement | null>(null);
const stageEl = ref<HTMLDivElement | null>(null);
const scopeCanvas = ref<HTMLCanvasElement | null>(null);
const scopeBox = ref<HTMLDivElement | null>(null);
const hoverCell = ref<GridCell | null>(null);
const hoverEnv = ref({ x: 0, y: 0, heat: 0, moisture: 0, nutrient: 0 });
let lastMouseEvent: MouseEvent | null = null;

const pan = ref({ x: 0, y: 0 });

// “fit” scale (computed vs stage), and user zoom factor (1.0 = fit)
const baseScale = ref(1);          // computed to fit canvas in stage
const zoomFactor = ref(1);         // user-controlled, relative to fit
const scopeActive = ref(false);
const showLegend = ref(false);

// total scale applied to canvas
const totalScale = computed(() => {
  return Math.max(1, Math.round(baseScale.value * zoomFactor.value));
});

// style for canvas transform
const canvasStyle = computed(() => ({
  transform: `translate(${Math.round(pan.value.x)}px, ${Math.round(pan.value.y)}px) scale(${totalScale.value})`,
  transformOrigin: "top left",
}));

function zoomIn()  { zoomFactor.value = Math.min(8, zoomFactor.value * 1.25); }
function zoomOut() { zoomFactor.value = Math.max(0.25, zoomFactor.value / 1.25); }
function onWheelZoom(e: WheelEvent) { e.deltaY < 0 ? zoomIn() : zoomOut(); }

/* Pan controls */
let isPanning = false;
let lastPan = { x: 0, y: 0 };
function startPan(e: MouseEvent) {
  if (e.button !== 1 && e.button !== 2) return;
  isPanning = true;
  lastPan = { x: e.clientX, y: e.clientY };
}
function onMouseMove(e: MouseEvent) {
  if (isPanning) {
    pan.value.x += e.clientX - lastPan.x;
    pan.value.y += e.clientY - lastPan.y;
    lastPan = { x: e.clientX, y: e.clientY };
  }
  lastMouseEvent = e;
  updateScope(e);
}
function endPan() { isPanning = false; }

/* ===================== Speed ===================== */
const ticksPerSecond = ref(30);
const tickInterval = computed(() => 1000 / ticksPerSecond.value);
const isPaused = ref(false);
function speedUp() { ticksPerSecond.value = Math.min(240, ticksPerSecond.value + 10); }
function slowDown() { ticksPerSecond.value = Math.max(1, ticksPerSecond.value - 10); }
function togglePause() { isPaused.value = !isPaused.value; }

/* ===================== Cards / Stamps ===================== */
const cards = ref<{ label: string; url: string; stamp_url?: string }[]>([]);
const selectedCardLabel = ref<string | null>(null);
let loadedImageData: ImageData | null = null;

function selectCard(label: string) {
  selectedCardLabel.value = label;
}

/* ===================== Cell / World Types ===================== */
type Heading = 0|1|2|3;
const HEADING_VECS: [number,number][] = [[1,0],[-1,0],[0,1],[0,-1]];

type GridCell = {
  id:number;
  r:number; g:number; b:number; a:number;
  x:number; y:number;
  energy:number; alive:boolean; birthTick:number; age:number;
  aggression:number; fertility:number; metabolism:number;
  strength:number;         // alpha→weight 0..1
  speed:number;            // movement steps per tick
  heading: Heading;        // chain direction
  turnBias:number;         // smoothness (smaller = straighter)
  coop:number;             // cooperation affinity
  cargo:number;            // carried nutrients
  solidCargo: number;      // Carried terrain material for erosion
  friends: Record<number, number>; // pairwise affinity
  decayRate:number;        // alpha loss per tick
  lifespan: number;        // randomized lifespan in ticks
  rootId: number;          // root id for sprouted plants
  attached: boolean;       // whether movement is locked to a parent plant
};

type ColourName = 'red' | 'green' | 'blue' | null;

/* ===================== World State ===================== */
const livingCells = ref<GridCell[]>([]);
let nextCellId = 1;
const cellById: Record<number, GridCell> = {};
const familyTree: Record<number, {parents:number[]; children:number[]}> = {};
let spatialMap: Array<GridCell | null> = [];

const stats = ref({
  warDeaths: 0, babyMerges: 0, squishDeaths: 0, fadedDeaths: 0,
  totalLifespan: 0, deadCount: 0,
});

interface ColourGroupStat {
  colour: string;
  count: number;
  percentage: number;
  avgAge: number;
  avgEnergy: number;
  avgStrength: number;
}

function rgbToHex(r: number, g: number, b: number) {
  return `#${[r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')}`;
}

function hexToRgb(hex: string) {
  const h = hex.replace('#', '');
  return { r: parseInt(h.slice(0, 2), 16), g: parseInt(h.slice(2, 4), 16), b: parseInt(h.slice(4, 6), 16) };
}

const GROUP_STEP = 48; // bucket size for colour grouping
const quant = (v: number) => Math.min(255, Math.round(v / GROUP_STEP) * GROUP_STEP);
function groupKeyFromRGB(r: number, g: number, b: number) {
  return rgbToHex(quant(r), quant(g), quant(b));
}
function groupKey(c: GridCell) {
  return groupKeyFromRGB(c.r, c.g, c.b);
}

const highlightedGroup = ref<string | null>(null);
function selectGroup(colour: string) {
  highlightedGroup.value = highlightedGroup.value === colour ? null : colour;
}

const selectedGroupInfo = computed(() => {
  if (!highlightedGroup.value) return null;
  const { r, g, b } = hexToRgb(highlightedGroup.value);
  const msgs: string[] = [];
  if (r > g && r > b) msgs.push('High red boosts aggression and heat-seeking.');
  if (g > r && g > b) msgs.push('Green fuels metabolism and nutrient hunger.');
  if (b > r && b > g) msgs.push('Blue increases moisture affinity and cooling.');
  if (!msgs.length) msgs.push('Balanced colours yield balanced behaviour.');
  return { colour: highlightedGroup.value, message: msgs.join(' ') };
});

const selectedCell = ref<GridCell | null>(null);
function selectCellById(id: number) {
  const c = cellById[id];
  if (c) selectedCell.value = c;
}
const selectedFamily = computed(() => {
  if (!selectedCell.value) return { parents: [] as GridCell[], children: [] as GridCell[] };
  const entry = familyTree[selectedCell.value.id] || { parents: [], children: [] };
  return {
    parents: entry.parents.map(id => cellById[id]).filter(Boolean),
    children: entry.children.map(id => cellById[id]).filter(Boolean),
  };
});

const groupStats = computed<ColourGroupStat[]>(() => {
  const base = {
    count: 0,
    totalStrength: 0,
    totalAge: 0,
    totalEnergy: 0,
  };
  const groups: Record<string, typeof base> = {};
  for (const c of livingCells.value) {
    const key = groupKey(c);
    const g = groups[key] || (groups[key] = { ...base });
    g.count++;
    g.totalStrength += c.strength;
    g.totalAge += c.age;
    g.totalEnergy += c.energy;
  }
  const total = livingCells.value.length;
  return Object.entries(groups).map(([colour, grp]) => ({
    colour,
    count: grp.count,
    percentage: total ? (grp.count / total) * 100 : 0,
    avgAge: grp.count ? grp.totalAge / grp.count : 0,
    avgEnergy: grp.count ? grp.totalEnergy / grp.count : 0,
    avgStrength: grp.count ? grp.totalStrength / grp.count : 0,
  }));
});

const sortedGroupStats = computed(() =>
  [...groupStats.value].sort((a, b) => b.count - a.count)
);

/* Tick bookkeeping */
let animationFrameId: number | null = null;
let lastTime = 0;
let timeSinceLastTick = 0;
const tickCount = ref(0);

/* Fields + solids (allocated per size) */
let heatField      = new Float32Array(S()*S());
let moistureField  = new Float32Array(S()*S());
let nutrientField  = new Float32Array(S()*S());
let solidGrid      = new Float32Array(S()*S());
let dyeRField      = new Float32Array(S()*S());
let dyeGField      = new Float32Array(S()*S());
let dyeBField      = new Float32Array(S()*S());

const BALANCE_RATE = 0.005; // environmental pressure toward colour parity

function I(x:number,y:number){ const s=S(); return ((x & (s-1)) + ((y & (s-1)) * s)) >>> 0; }

function colourDominance(v:number, o1:number, o2:number): number {
  const avg = (o1 + o2) / 2;
  const diff = v - avg;
  return diff * Math.abs(diff) * 0.5;
}

function colourIntensity(r:number, g:number, b:number): number {
  const maxC = Math.max(r, g, b);
  const minC = Math.min(r, g, b);
  return (maxC - minC) / 255;
}

function dominantFromRGB(r:number,g:number,b:number): ColourName {
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  if (max - min < 20) return null; // Increased threshold for stronger roles
  if (max === r) return 'red';
  if (max === g) return 'green';
  if (max === b) return 'blue';
  return null;
}

function dominantColour(c: GridCell): ColourName {
  return dominantFromRGB(c.r, c.g, c.b);
}

/* Renderer buffer */
let frame = new Uint8ClampedArray(0);
let frameImg: ImageData | null = null;

/* ===================== RNG ===================== */
let rng = mulberry32(0);
function mulberry32(a:number){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
function reseedRNG(seed?:number){
  let s = seed;
  if (s === undefined){
    if (typeof crypto !== "undefined" && "getRandomValues" in crypto){
      const buf = new Uint32Array(1);
      crypto.getRandomValues(buf);
      s = buf[0];
    } else {
      s = Math.floor(Math.random() * 0xffffffff);
    }
  }
  rng = mulberry32(s);
}
reseedRNG();
function rand(){ return rng(); }

/* ===================== Init / Resize ===================== */
function allocateWorldArrays(size:number){
  heatField      = new Float32Array(size*size);
  moistureField  = new Float32Array(size*size);
  nutrientField  = new Float32Array(size*size);
  solidGrid      = new Float32Array(size*size);
  dyeRField      = new Float32Array(size*size);
  dyeGField      = new Float32Array(size*size);
  dyeBField      = new Float32Array(size*size);
  spatialMap     = new Array(size*size).fill(null);
  const ctx = gameCanvas.value?.getContext("2d");
  if (ctx) {
    frameImg = ctx.createImageData(size, size);
    frame = frameImg.data;
  } else {
    frameImg = null;
    frame = new Uint8ClampedArray(size*size*4);
  }
}

function clearWorld(){
  livingCells.value.length = 0;
  spatialMap.fill(null);
  stats.value = { warDeaths:0, babyMerges:0, squishDeaths:0, fadedDeaths:0, totalLifespan:0, deadCount:0 };
  tickCount.value = 0;
  reseedRNG();
}

function applyBoardSize(){
  pan.value = {x:0, y:0};
  zoomFactor.value = 1;
  const canvas = gameCanvas.value;
  if (canvas){ canvas.width = S(); canvas.height = S(); }
  allocateWorldArrays(S());
  clearWorld();
  computeBaseScale();
}

function computeBaseScale(){
  const stage = stageEl.value;
  if (!stage) return;
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  const s = S();
  if (w <= 0 || h <= 0 || s <= 0) return;
  baseScale.value = Math.max(1, Math.floor(Math.min(w / s, h / s)));
}

function resetView(){
  pan.value = { x: 0, y: 0 };
  zoomFactor.value = 1;
  computeBaseScale();
}

/* stage resize observer */
let resizeObs: ResizeObserver | null = null;

/* ===================== Lifecycle ===================== */
onMounted(async () => {
  try {
    const gallery = await fetchBbyBookGallery();
    cards.value = gallery.map(card => ({
      label: card.factName,
      url: card.url,
      stamp_url: card.stamp_url,
    }));
    if (cards.value.length > 0) {
      selectedCardLabel.value = cards.value[0].label;
      loadSelectedImage();
    }
  } catch (error) {
    console.error("Failed to fetch bbyBook gallery:", error);
  }

  allocateWorldArrays(S());

  if (stageEl.value) {
    resizeObs = new ResizeObserver(() => computeBaseScale());
    resizeObs.observe(stageEl.value);
    computeBaseScale();
  }

  const scope = scopeCanvas.value;
  if (scope) {
    scope.width = 256;
    scope.height = 256;
  }

  animationFrameId = requestAnimationFrame(mainLoop);
});

onUnmounted(() => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  if (resizeObs && stageEl.value) resizeObs.disconnect();
});

watch(boardSize, () => applyBoardSize());
watch(selectedCardLabel, () => loadSelectedImage());

/* ===================== Main Loop ===================== */
const MAX_UPDATES_PER_FRAME = 5;

function mainLoop(timestamp: number) {
  const ctx = gameCanvas.value?.getContext("2d");
  if (!ctx) {
    animationFrameId = requestAnimationFrame(mainLoop);
    return;
  }

  const deltaTime = timestamp - lastTime;
  lastTime = timestamp;
  if (!isPaused.value) {
    timeSinceLastTick += deltaTime;

    let performed = 0;
    while (
      timeSinceLastTick >= tickInterval.value &&
      performed < MAX_UPDATES_PER_FRAME
    ) {
      update();
      timeSinceLastTick -= tickInterval.value;
      performed++;
    }

    if (performed === MAX_UPDATES_PER_FRAME) {
      timeSinceLastTick = 0;
    }
  }

  drawGrid(ctx);
  if (lastMouseEvent) updateScope(lastMouseEvent);
  animationFrameId = requestAnimationFrame(mainLoop);
}

/* ===================== Simulation ===================== */
function diffuseDecay(src:Float32Array, mix=0.25, decay=0.996){
  const s=S();
  for (let y=0;y<s;y++){
    for (let x=0;x<s;x++){
      const i = I(x,y);
      const nn = (src[I(x+1,y)] + src[I(x-1,y)] + src[I(x,y+1)] + src[I(x,y-1)]) * 0.25;
      src[i] = (1-mix)*src[i] + mix*nn;
      src[i] *= decay;
    }
  }
}

function erodeSolid(idx:number, amt:number){
  const current = solidGrid[idx];
  const take = Math.min(current, amt);
  if (take <= 0 || current <= 0) return 0;
  const frac = take / current;
  solidGrid[idx] -= take;
  dyeRField[idx] *= 1 - frac;
  dyeGField[idx] *= 1 - frac;
  dyeBField[idx] *= 1 - frac;
  return take;
}

function worldTick(totalR=0,totalG=0,totalB=0){
  let skyR = (Number(currentColour.r)||0)/255 * 0.004;
  let skyG = (Number(currentColour.g)||0)/255 * 0.004;
  let skyB = (Number(currentColour.b)||0)/255 * 0.004;

  const total = totalR + totalG + totalB;
  if (total > 0) {
    const ideal = total / 3;
    const adjR = ((ideal - totalR) / total) * BALANCE_RATE;
    const adjG = ((ideal - totalG) / total) * BALANCE_RATE;
    const adjB = ((ideal - totalB) / total) * BALANCE_RATE;
    skyR += adjR;
    skyG += adjG;
    skyB += adjB;
  }

  const base = 0.0008;
  const s=S();
  for (let y=0;y<s;y++){
    for (let x=0;x<s;x++){
      const i = I(x,y);
      if (solidGrid[i] > 0){
        nutrientField[i] += Math.min(0.02*solidGrid[i], 0.05);
        heatField[i]     += Math.min(0.01*solidGrid[i], 0.03);
      }
      heatField[i]     += skyR + base;
      moistureField[i] += skyB + base;
      nutrientField[i] += skyG + base;
    }
  }
  diffuseDecay(heatField,     0.20, 0.996);
  diffuseDecay(moistureField, 0.30, 0.997);
  diffuseDecay(nutrientField, 0.18, 0.996);
}

function update() {
  tickCount.value++;

  let totalR = 0, totalG = 0, totalB = 0;
  for (const c of livingCells.value) {
    totalR += c.r;
    totalG += c.g;
    totalB += c.b;
  }

  worldTick(totalR, totalG, totalB);

  for (let i = livingCells.value.length - 1; i >= 0; i--) {
    const c = livingCells.value[i];
    if (!c.alive) continue;

    const ii = I(c.x, c.y);
    const Rf = c.r/255, Gf = c.g/255, Bf = c.b/255;
    
    // --- Universal Cell Logic ---
    c.age += 1;
    c.energy -= c.metabolism;
    if (c.age > c.lifespan) {
        c.a = Math.max(0, c.a - c.decayRate * 5);
    } else {
        c.a = Math.max(0, c.a - c.decayRate);
    }
    c.strength = c.a / 255;
    if (c.a < VISIBLE_ALPHA) {
      recordDeath(c, "fade");
      continue;
    }
    
    // --- RESTRUCTURED PHYSICS: ENFORCE ECOLOGICAL ROLES ---
    const role = dominantColour(c);
    let gain = 0;

    switch (role) {
      case 'blue': {
        const domB = colourDominance(Bf, Rf, Gf);
        const blueGroup = countAdjacentBlue(c.x, c.y);
        const erosionPower = 0.007 * Bf * domB * (1 + blueGroup * 0.5);
        
        if (c.solidCargo < 1.0) {
            const take = Math.min(erosionPower, solidGrid[ii], 1.0 - c.solidCargo);
            if (take > 0) {
                erodeSolid(ii, take);
                c.solidCargo += take;
                c.energy -= take * 3;
            }
        }
        if (blueGroup >= 2) c.energy = Math.min(260, c.energy + blueGroup * 0.2);
        
        const take = Math.min(0.02 * domB, moistureField[ii]);
        moistureField[ii] -= take;
        gain += take * 10;
        break;
      }

      case 'green': {
        const domG = colourDominance(Gf, Rf, Bf);
        const heat = heatField[ii];
        const moisture = moistureField[ii];
        if (heat > 0.1 && moisture > 0.1) {
            const intake = Math.min(heat, moisture, 0.015) * domG;
            heatField[ii] -= intake;
            moistureField[ii] -= intake;
            c.energy = Math.min(260, c.energy + intake * 60);
        }
        break;
      }
      
      case 'red': {
        const domR = colourDominance(Rf, Bf, Gf);
        if (moistureField[ii] > 0.15) c.energy -= moistureField[ii] * 5;

        const fuel = Math.min(nutrientField[ii], 0.02 * domR);
        if (fuel > 0) {
            nutrientField[ii] -= fuel;
            c.energy = Math.min(260, c.energy + fuel * 30);
            heatField[ii] += fuel * 0.5;
        }

        for (const [dx, dy] of HEADING_VECS) {
            const neighbour = spatialMap[I((c.x + dx + S()) % S(), (c.y + dy + S()) % S())];
            if (neighbour?.alive) {
                const nDom = dominantColour(neighbour);
                if (nDom === 'green') {
                    const burn = Math.min(neighbour.energy, 15);
                    neighbour.energy -= burn;
                    c.energy = Math.min(260, c.energy + burn * 2.5);
                    if (neighbour.energy <= 0) recordDeath(neighbour, "war");
                }
                if (nDom === 'blue') c.energy -= 10;
            }
        }
        break;
      }

      default: { 
        // Balanced/mixed cells get no primary energy, only from synergies
        break;
      }
    }

    // --- UNIVERSAL: MIXED COLOR SYNERGIES (Applied to ALL cells) ---
    const mixRB = Math.min(Rf, Bf);
    if (mixRB > 0.3) {
      const take = Math.min(0.01*mixRB, moistureField[ii]);
      moistureField[ii] -= take; heatField[ii] += take*1.5; gain += take*5;
    }
    const mixBG = Math.min(Bf, Gf);
    if (mixBG > 0.3) {
      const take = Math.min(0.01*mixBG, nutrientField[ii]);
      nutrientField[ii] -= take; moistureField[ii] += take*1.5; gain += take*5;
    }
    const mixRG = Math.min(Rf, Gf);
    if (mixRG > 0.3) {
      const take = Math.min(0.01*mixRG, heatField[ii]);
      heatField[ii] -= take; nutrientField[ii] += take*1.5; gain += take*5;
    }

    c.energy = Math.min(c.energy + gain, 260);

    if (c.energy <= 0) {
      if (role === 'blue') {
        let pooled = false;
        for (const [dx, dy] of HEADING_VECS) {
          const neighbour = spatialMap[I((c.x + dx + S()) % S(), (c.y + dy + S()) % S())];
          if (neighbour?.alive && dominantColour(neighbour) === 'blue') { pooled = true; break; }
        }
        if (pooled) { c.energy = 1; continue; }
        const escape = findEmptyAdjacent(c.x, c.y);
        if (escape) { performMove(c, escape[0], escape[1]); c.energy = 5; continue; }
      }
      recordDeath(c, "squish");
    }
  }

  const updatesPerTick = Math.ceil(livingCells.value.length / 80) || 1;
  for (let i = 0; i < updatesPerTick; i++) {
    const cell = pickRandomLivingCell();
    if (cell?.alive) {
      const steps = cell.speed || 1;
      for (let s = 0; s < steps; s++) {
        const [dx, dy, newH] = chooseChainDir(cell);
        if (attemptMove(cell, dx, dy)) {
          cell.heading = newH;
          deposit(cell);
        } else {
          break;
        }
      }
    }
  }
}

/* ===================== Image / Stamping ===================== */
function loadSelectedImage() {
  const selected = cards.value.find(c => c.label === selectedCardLabel.value);
  if (!selected) return;

  const tryUrls: string[] = [];
  if (selected.stamp_url) tryUrls.push(selected.stamp_url);
  tryUrls.push(selected.url.replace(/\.png$/i, '.stamp.png'));
  tryUrls.push(selected.url);

  const img = new Image();
  img.crossOrigin = "Anonymous";
  let idx = 0;

  img.onload = () => {
    const scale = Math.min(1, 64 / Math.max(img.width, img.height));
    const outW = Math.max(1, Math.floor(img.width * scale));
    const outH = Math.max(1, Math.floor(img.height * scale));

    const tempCanvas = document.createElement("canvas");
    const ctx = tempCanvas.getContext("2d", { willReadFrequently: true })!;
    tempCanvas.width = outW; tempCanvas.height = outH;
    (ctx as any).imageSmoothingEnabled = false;

    ctx.drawImage(img, 0, 0, outW, outH);
    loadedImageData = ctx.getImageData(0, 0, outW, outH);
  };

  img.onerror = () => { idx++; if (idx < tryUrls.length) img.src = tryUrls[idx]; };
  img.src = tryUrls[idx];
}

const VISIBLE_ALPHA = 0.2 * 255
const GENETIC_COMPAT_THRESHOLD = 0.15
const FAMILY_PENALTY_THRESHOLD = 200
const REPRODUCTION_MIN_ENERGY = 80
const BIRTH_FLASH_TICKS = 8
const MIN_DECAY_RATE = 0.1
const MAX_DECAY_RATE = 0.3

function randomDecayRate(){
  return MIN_DECAY_RATE + rand() * (MAX_DECAY_RATE - MIN_DECAY_RATE);
}

function makeCell(px:number,py:number,r:number,g:number,b:number,a:number, parentLifespan?: number): GridCell {
  const A = Math.max(VISIBLE_ALPHA, a);
  const dom = dominantFromRGB(r, g, b);
  let strength = (A/255);
  let speed = 1 + Math.floor((255 - A) / 85);
  if (dom === 'green') strength *= 1.2;
  if (dom === 'blue') strength *= 0.8;
  if (dom === 'red')  speed += 1;
  let energy = 60 + strength*140;
  let metabolism = 0.18 + (g/255)*0.20;
  let aggression  = (r/255)*0.9;
  let fertility   = 0;

  const heading = (Math.floor(rand()*4) as Heading);
  const baseLifespan = parentLifespan || (TICKS_PER_DAY * 10 + rand() * TICKS_PER_DAY * 20);
  const lifespan = (baseLifespan + (rand() - 0.5) * (TICKS_PER_DAY * 5)) * 200;

  const id = nextCellId++;
  const cell: GridCell = {
    id, r, g, b, a: A, x: px, y: py, energy, alive: true, birthTick: tickCount.value, age: 0,
    aggression, fertility, metabolism, strength, speed,
    heading, turnBias: 0.3 + (1 - strength) * 0.4,
    coop: 0, cargo: 0, solidCargo: 0,
    friends: {}, decayRate: randomDecayRate(), lifespan, rootId: id, attached: false,
  };
  cellById[cell.id] = cell;
  familyTree[cell.id] = {parents: [], children: []};

  const idx = I(px, py);
  const Rf = r/255, Gf = g/255, Bf = b/255;
  heatField[idx]     += 0.1 + 0.2*Rf;
  moistureField[idx] += 0.1 + 0.2*Bf;
  nutrientField[idx] += 0.1 + 0.2*Gf;

  return cell;
}

function placeImage(event: MouseEvent) {
  const canvas = gameCanvas.value; if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  const clickX = (event.clientX - rect.left) * (canvas.width / rect.width);
  const clickY = (event.clientY - rect.top) * (canvas.height / rect.height);

  const mouseGridX = Math.floor(clickX);
  const mouseGridY = Math.floor(clickY);

  const existing = spatialMap[I(mouseGridX, mouseGridY)];
  if (existing) {
    selectedCell.value = existing;
    return;
  }

  if (!loadedImageData) return;

  const W = loadedImageData.width;
  const H = loadedImageData.height;
  const pixels = loadedImageData.data;

  const startGridX = mouseGridX - Math.floor(W/2);
  const startGridY = mouseGridY - Math.floor(H/2);

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4;
      const a = pixels[i + 3];
      if (a > VISIBLE_ALPHA) {
        const newX = startGridX + x;
        const newY = startGridY + y;
        if (newX>=0 && newX<S() && newY>=0 && newY<S()) {
          const key = I(newX, newY);
          if (!spatialMap[key]) {
            const cell = makeCell(newX, newY, pixels[i], pixels[i+1], pixels[i+2], a);
            livingCells.value.push(cell);
            spatialMap[key] = livingCells.value[livingCells.value.length - 1];
          }
        }
      }
    }
  }
  lastTime = performance.now();
  timeSinceLastTick = 0;
}

/* ===================== Movement / Chains ===================== */
function shuffleArray(array: any[]) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(rand() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function chooseChainDir(cell:GridCell): [number,number,Heading] {
  const prefs: {h:Heading, score:number}[] = [];
  const headings: Heading[] = [0, 1, 2, 3];
  shuffleArray(headings);

  let bestMate: GridCell | null = null;
  let bestComp = 0;
  if (cell.energy > REPRODUCTION_MIN_ENERGY) {
    for (const other of livingCells.value) {
      if (other.id === cell.id || !other.alive) continue;
      const comp = compatibility(cell, other);
      if (comp > bestComp) { bestComp = comp; bestMate = other; }
    }
  }

  const board = S();
  let mateDx = 0, mateDy = 0, fertFactor = 0;
  if (bestMate) {
    mateDx = bestMate.x - cell.x; mateDy = bestMate.y - cell.y;
    if (mateDx > board / 2) mateDx -= board; if (mateDx < -board / 2) mateDx += board;
    if (mateDy > board / 2) mateDy -= board; if (mateDy < -board / 2) mateDy += board;
    fertFactor = (cell.fertility + bestMate.fertility) / 2;
  }

  for (const h of headings) {
    const [dx,dy] = HEADING_VECS[h];
    const nx = (cell.x + dx + S()) % S();
    const ny = (cell.y + dy + S()) % S();
    const i = I(nx,ny);
    const neighbour = spatialMap[i];

    const heat = heatField[i], wet = moistureField[i], nut = nutrientField[i];
    const Rf = cell.r/255, Bf = cell.b/255, Gf = cell.g/255;
    let want = 0;
    
    const hDiff = solidGrid[i] - solidGrid[I(cell.x, cell.y)];
    const role = dominantColour(cell);

    switch(role) {
      case 'blue':
        want += wet * Bf;
        if (hDiff > 0) want -= hDiff * (Bf * colourDominance(Bf,Rf,Gf) + cell.solidCargo * 2);
        else if (hDiff < 0) want += (-hDiff) * Bf * colourDominance(Bf,Rf,Gf) * 1.5;
        break;
      case 'green':
        want += (heat + wet) * 0.8 * Gf;
        want += hDiff * 0.8 * Gf; // Strong desire to climb
        break;
      case 'red':
        want += heat * Rf;
        want += (nut - wet) * colourDominance(Rf,Bf,Gf) * 0.5;
        if (hasNearbyGreen(nx, ny, 2)) want += 0.6 * colourDominance(Rf,Bf,Gf);
        break;
      default:
        want = heat*Rf + wet*Bf + nut*Gf;
        break;
    }

    let solidPenalty = solidGrid[i] * (1 - cell.strength);
    if (role === 'red') solidPenalty *= 0.1;
    if (Math.abs(Rf - Gf) < 0.1 && Math.abs(Gf - Bf) < 0.1) solidPenalty *= 0.3;
    
    const turnPenalty = (h === cell.heading ? 0 : cell.turnBias);
    let score = want - solidPenalty - turnPenalty + (h === cell.heading ? 0.15 : 0);
    
    if (neighbour?.alive) {
      const comp = compatibility(cell, neighbour);
      score += (comp > 0.6) ? comp * 0.2 : -(1 - comp) * 0.2;
    }
    
    score += (rand()-0.5)*0.1;

    if (bestMate) {
      const currentDist = Math.abs(mateDx) + Math.abs(mateDy);
      let ndx = mateDx - dx; let ndy = mateDy - dy;
      if (ndx > board / 2) ndx -= board; if (ndx < -board / 2) ndx += board;
      if (ndy > board / 2) ndy -= board; if (ndy < -board / 2) ndy += board;
      const newDist = Math.abs(ndx) + Math.abs(ndy);
      if (newDist < currentDist) score += bestComp * fertFactor;
    }

    prefs.push({h, score});
  }
  prefs.sort((a,b)=>b.score - a.score);
  const best = prefs[0];
  const [dx,dy] = HEADING_VECS[best.h];
  return [dx,dy,best.h];
}

function findEmptyAdjacent(x:number,y:number): [number,number] | null {
  const dirs:[number,number][] = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
  shuffleArray(dirs);
  for (const [dx,dy] of dirs) {
    const nx = (x + dx + S()) % S();
    const ny = (y + dy + S()) % S();
    if (!spatialMap[I(nx, ny)]) return [nx, ny];
  }
  return null;
}

function countAdjacentBlue(x:number,y:number): number {
  let c=0;
  for (const [dx,dy] of HEADING_VECS){
    const n=spatialMap[I((x+dx+S())%S(),(y+dy+S())%S())];
    if (n?.alive && dominantColour(n)==='blue') c++;
  }
  return c;
}

function hasNearbyGreen(x:number,y:number,dist=2): boolean {
  for (let dy=-dist; dy<=dist; dy++){
    for (let dx=-dist; dx<=dist; dx++){
      if (dx===0 && dy===0) continue;
      const neighbour = spatialMap[I((x+dx+S())%S(),(y+dy+S())%S())];
      if (neighbour?.alive && dominantColour(neighbour) === 'green') return true;
    }
  }
  return false;
}

function congaMove(start:GridCell, dx:number, dy:number): boolean {
  const chain: GridCell[] = [start];
  let current = start;
  while (chain.length < S()) {
    const next = spatialMap[I((current.x + dx + S())%S(), (current.y + dy + S())%S())];
    if (!next) break;
    if (next.alive && next.heading === start.heading) {
      chain.push(next);
      current = next;
    } else {
      recordDeath(next, "squish");
      break;
    }
  }
  
  for (let i = chain.length - 1; i >= 0; i--) {
    const c = chain[i];
    performMove(c, (c.x + dx + S())%S(), (c.y + dy + S())%S());
  }
  return true;
}

function attemptMove(cell:GridCell, dx:number, dy:number): boolean {
  if (rand() < cell.strength*0.2) return false;

  const newX = (cell.x + dx + S()) % S();
  const newY = (cell.y + dy + S()) % S();
  const key = I(newX, newY);
  const target = spatialMap[key];

  const heightDiff = solidGrid[key] - solidGrid[I(cell.x, cell.y)];
  if (heightDiff > 0 && dominantColour(cell) !== 'red') {
      const climbCap = cell.strength * 3;
      if (heightDiff > climbCap) return false;
      if (rand() < Math.min(0.9, 0.8 * (1 - cell.strength) * (heightDiff / climbCap))) return false;
      cell.energy -= heightDiff * 0.1;
  }

  if (!target){
    performMove(cell, newX, newY);
    return true;
  }

  if (target.alive){
    const compVal = compatibility(cell, target);
    const pairAff = getAffinity(cell, target);
    const coopBoost = (cell.coop + target.coop) * 0.2 + pairAff * 0.1;
    let pCompat = Math.min(1, 0.05 + compVal * 0.35 + (cell.fertility + target.fertility) * 0.05 + coopBoost);

    if (isCloseFamily(cell, target)) {
      const options = countCompatibleNonFamily(cell);
      if (options > FAMILY_PENALTY_THRESHOLD) {
        pCompat *= FAMILY_PENALTY_THRESHOLD / options;
      }
    }

    const baseWar = (cell.aggression + target.aggression) * 0.35 + (heatField[key] * 0.25);
    const pWar = Math.min(1, Math.max(0, baseWar - coopBoost * 0.5 - pairAff * 0.1));

    if (compVal >= GENETIC_COMPAT_THRESHOLD && pCompat >= pWar &&
        cell.energy > REPRODUCTION_MIN_ENERGY && target.energy > REPRODUCTION_MIN_ENERGY) {
      adjustAffinity(cell, target, 0.5);
      const spawn = findEmptyAdjacent(newX, newY) || findEmptyAdjacent(cell.x, cell.y);
      if (spawn){
        const baby = mergeBaby(cell, target, spawn[0], spawn[1]);
        livingCells.value.push(baby);
        spatialMap[I(spawn[0], spawn[1])] = livingCells.value[livingCells.value.length - 1];
        stats.value.babyMerges++;
      }
      return false;
    } else {
      const cellScore = cell.energy * (0.8 + 0.5 * cell.aggression) + (cell.strength * 20);
      const tarScore  = target.energy * (0.8 + 0.5 * target.aggression) + (target.strength * 20);
      if (cellScore >= tarScore){
        recordDeath(target, "war");
        adjustAffinity(cell, target, -1.5);
        cell.energy = Math.min(cell.energy + 20, 260);
        performMove(cell, newX, newY);
        return true;
      } else {
        recordDeath(cell, "war");
        adjustAffinity(cell, target, -1.5);
        return false;
      }
    }
  }
  return congaMove(cell, dx, dy);
}

function performMove(moving:GridCell, toX:number, toY:number){
  const s = S();
  const fromX = moving.x, fromY = moving.y;
  const fromIdx = I(fromX, fromY);
  spatialMap[fromIdx] = null;
  moving.x = (toX + s) % s; moving.y = (toY + s) % s;
  spatialMap[I(moving.x, moving.y)] = moving;

  if (dominantColour(moving) === 'blue' && moving.solidCargo > 0) {
      const drop = moving.solidCargo * 0.25;
      solidGrid[fromIdx] = Math.min(6, solidGrid[fromIdx] + drop);
      moving.solidCargo -= drop;
  }
}

/* ===================== Interactions ===================== */
function pickRandomLivingCell(): GridCell | null {
  if (livingCells.value.length === 0) return null;
  return livingCells.value[Math.floor(rand()*livingCells.value.length)];
}

function getAffinity(a:GridCell, b:GridCell){
  return a.friends[b.id] || 0;
}

function adjustAffinity(a:GridCell, b:GridCell, delta:number){
  const clamp = (v:number)=>Math.min(10, Math.max(-10, v));
  a.friends[b.id] = clamp((a.friends[b.id]||0) + delta);
  b.friends[a.id] = clamp((b.friends[a.id]||0) + delta);
}

function isCloseFamily(a: GridCell, b: GridCell): boolean {
  const fa = familyTree[a.id];
  const fb = familyTree[b.id];
  if (!fa || !fb) return false;
  if (fa.parents.includes(b.id) || fa.children.includes(b.id)) return true;
  if (fb.parents.includes(a.id) || fb.children.includes(a.id)) return true;
  return fa.parents.some(p => fb.parents.includes(p));
}

function countCompatibleNonFamily(cell: GridCell): number {
  let count = 0;
  for (const other of livingCells.value) {
    if (other.id === cell.id || !other.alive) continue;
    if (isCloseFamily(cell, other)) continue;
    if (compatibility(cell, other) >= GENETIC_COMPAT_THRESHOLD) count++;
  }
  return count;
}

function compatibility(a:GridCell,b:GridCell){
  const AR=a.r/255, AG=a.g/255, AB=a.b/255;
  const BR=b.r/255, BG=b.g/255, BB=b.b/255;
  const comp = (AR*BB + AG*BR + AB*BG) / 3;
  const dist = Math.hypot(AR-BR, AG-BG, AB-BB) / Math.sqrt(3);
  const satA = colourIntensity(a.r, a.g, a.b);
  const satB = colourIntensity(b.r, b.g, b.b);
  const base = 0.6*comp + 0.4*(1 - dist);
  return base * ((satA + satB) / 2);
}

function mergeBaby(cell:GridCell,target:GridCell,x:number,y:number): GridCell {
  const totalS = Math.max(0.0001, cell.strength + target.strength);
  const wA = cell.strength / totalS;
  const wB = target.strength / totalS;

  function blendChannel(a:number, b:number, mut:number){
    const avg = a*wA + b*wB;
    const diff = a - b;
    const drift = diff * (rand()*0.25 + 0.125);
    return Math.min(255, Math.max(0, Math.round(avg + drift + (rand()*mut - mut/2))));
  }

  const babyR = blendChannel(cell.r, target.r, 6);
  const babyG = blendChannel(cell.g, target.g, 6);
  const babyB = blendChannel(cell.b, target.b, 6);

  const avgLifespan = (cell.lifespan + target.lifespan) / 2;
  const kid = makeCell(x, y, babyR, babyG, babyB, 255, avgLifespan);
  
  kid.energy = Math.min((cell.energy + target.energy) * 0.3, 240);
  cell.energy *= 0.7;
  target.energy *= 0.7;

  familyTree[kid.id].parents = [cell.id, target.id];
  familyTree[cell.id].children.push(kid.id);
  familyTree[target.id].children.push(kid.id);
  adjustAffinity(cell, target, 2);
  adjustAffinity(cell, kid, 3);
  adjustAffinity(target, kid, 3);
  return kid;
}

function recordDeath(cell: GridCell, reason: "war" | "squish" | "fade") {
  if (!cell.alive) return;
  cell.alive = false;

  stats.value.totalLifespan += cell.age;
  stats.value.deadCount++;
  if (reason === "war") stats.value.warDeaths++;
  if (reason === "squish") stats.value.squishDeaths++;
  if (reason === "fade") stats.value.fadedDeaths++;

  const i = I(cell.x, cell.y);

  let solidAdd = 0.2 + 0.8 * cell.strength;
  if (cell.solidCargo > 0) solidAdd += cell.solidCargo;
  solidGrid[i] = Math.min(solidGrid[i] + solidAdd, 6);

  const energy = cell.energy;
  const Rf = cell.r/255, Bf = cell.b/255, Gf = cell.g/255;
  const nutrientBonus = (dominantColour(cell) === 'green') ? 2.5 : 1.0;

  moistureField[i] += energy*(0.01 + 0.02*Bf);
  heatField[i]     += energy*(0.005 + 0.03*Rf);
  nutrientField[i] += energy*(0.01 + 0.04*Gf) * nutrientBonus;

  spatialMap[i] = null;
  const index = livingCells.value.findIndex(c => c.id === cell.id);
  if (index > -1) livingCells.value.splice(index, 1);
}

function deposit(cell:GridCell){
  const i = I(cell.x, cell.y);
  const Rf = cell.r/255, Bf = cell.b/255, Gf = cell.g/255;
  const e = (cell.energy/200);
  heatField[i]     += (0.02 + 0.08*e) * Rf;
  moistureField[i] += (0.02 + 0.06*e) * Bf;
  nutrientField[i] += (0.02 + 0.10*e) * Gf;

  moistureField[i] = Math.max(0, moistureField[i] - (0.015*Rf));
  heatField[i]     = Math.max(0, heatField[i] - (0.012*Bf));
  nutrientField[i] += 0.005*Bf;
  heatField[i]     += 0.003*Gf;
  if (cell.cargo > 0) {
    nutrientField[i] += cell.cargo * 0.01;
    cell.cargo = 0;
  }
}

/* ===================== Draw ===================== */
function drawGrid(ctx: CanvasRenderingContext2D) {
  if (!frameImg) return;
  ctx.imageSmoothingEnabled = false;

  const skyR = Number(currentColour.r)||0;
  const skyG = Number(currentColour.g)||0;
  const skyB = Number(currentColour.b)||0;

  const SKY_SCALE = 0.03, FIELD_SCALE = 80, FLOOR_ALPHA = 0.10;
  const s=S();

  for (let y=0;y<s;y++){
    for (let x=0;x<s;x++){
      const off = (x + y*s)*4;
      const ii = I(x,y);
      const H = Math.floor(heatField[ii]*FIELD_SCALE);
      const W = Math.floor(moistureField[ii]*FIELD_SCALE);
      const N = Math.floor(nutrientField[ii]*FIELD_SCALE);

      const baseR = 16 + (skyR*SKY_SCALE)|0;
      const baseG = 16 + (skyG*SKY_SCALE)|0;
      const baseB = 18 + (skyB*SKY_SCALE)|0;

      const glowR = baseR + H, glowG = baseG + N, glowB = baseB + W;
      const a = FLOOR_ALPHA;
      let r = (baseR*(1-a) + glowR*a) | 0;
      let g = (baseG*(1-a) + glowG*a) | 0;
      let b = (baseB*(1-a) + glowB*a) | 0;

      const rock = solidGrid[ii] * 30;
      if (rock > 0) {
        r = Math.min(255, r + rock);
        g = Math.min(255, g + rock);
        b = Math.min(255, b + rock);
      }

      const dr = dyeRField[ii], dg = dyeGField[ii], db = dyeBField[ii];
      const dyeTotal = dr + dg + db;
      if (dyeTotal > 0){
        const dyeAlpha = Math.min(0.4, dyeTotal / 765);
        r = (r*(1-dyeAlpha) + (dr/dyeTotal*255)*dyeAlpha) | 0;
        g = (g*(1-dyeAlpha) + (dg/dyeTotal*255)*dyeAlpha) | 0;
        b = (b*(1-dyeAlpha) + (db/dyeTotal*255)*dyeAlpha) | 0;
      }

      frame[off  ] = r; frame[off+1] = g; frame[off+2] = b; frame[off+3] = 255;
    }
  }

  for (const c of livingCells.value){
    const off = (c.x + c.y*s)*4;
    frame[off  ] = c.r; frame[off+1] = c.g; frame[off+2] = c.b; frame[off+3] = c.a;

    if (highlightedGroup.value === groupKey(c)) {
      frame[off] = Math.min(255, frame[off] + 100);
      frame[off+1] = Math.min(255, frame[off+1] + 100);
      frame[off+2] = Math.min(255, frame[off+2] + 100);
    }
    if (selectedCell.value?.id === c.id) {
      frame[off] = 255; frame[off+1] = 255; frame[off+2] = 0;
    }
    if (c.age < BIRTH_FLASH_TICKS){
      const flash = 1 - c.age / BIRTH_FLASH_TICKS;
      frame[off] = Math.min(255, frame[off] + flash*200);
      frame[off+1] = Math.min(255, frame[off+1] + flash*200);
      frame[off+2] = Math.min(255, frame[off+2] + flash*200);
    }
  }

  ctx.putImageData(frameImg, 0, 0);
}

/* ===================== Scope ===================== */
const updateScope = throttle((event: MouseEvent) => {
  if (!scopeActive.value) return;
  const canvas = gameCanvas.value, scope = scopeCanvas.value, box = scopeBox.value;
  if (!canvas || !scope || !box || !frameImg) return;
  
  const rect = canvas.getBoundingClientRect();
  const hx = Math.floor((event.clientX - rect.left) * (canvas.width / rect.width));
  const hy = Math.floor((event.clientY - rect.top) * (canvas.height / rect.height));
  const ctx = scope.getContext('2d');
  if (!ctx) return;

  const SCOPE_SIZE = 9;
  const half = Math.floor(SCOPE_SIZE / 2);
  const pixelSize = scope.width / SCOPE_SIZE;
  const s = S();
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, scope.width, scope.height);
  
  for (let dy = 0; dy < SCOPE_SIZE; dy++) {
    for (let dx = 0; dx < SCOPE_SIZE; dx++) {
      const sx = hx - half + dx, sy = hy - half + dy;
      if (sx >= 0 && sy >= 0 && sx < s && sy < s) {
        const off = (sx + sy * s) * 4;
        ctx.fillStyle = `rgba(${frame[off]},${frame[off+1]},${frame[off+2]},${frame[off+3]/255})`;
        ctx.fillRect(dx * pixelSize, dy * pixelSize, pixelSize, pixelSize);
      }
    }
  }
  ctx.strokeStyle = 'rgba(255,255,255,0.7)';
  ctx.lineWidth = 1;
  ctx.strokeRect(0, 0, scope.width, scope.height);
  ctx.strokeStyle = 'rgba(0,0,0,0.7)';
  ctx.strokeRect(half * pixelSize, half * pixelSize, pixelSize, pixelSize);

  if (hx >= 0 && hy >= 0 && hx < s && hy < s) {
    const ii = I(hx, hy);
    hoverEnv.value = { x: hx, y: hy, heat: heatField[ii], moisture: moistureField[ii], nutrient: nutrientField[ii] };
    hoverCell.value = spatialMap[ii] || null;
  } else {
    hoverEnv.value = { x: hx, y: hy, heat: 0, moisture: 0, nutrient: 0 };
    hoverCell.value = null;
  }

  const stageRect = stageEl.value?.getBoundingClientRect();
  if (!stageRect) return;
  
  const boxX = event.clientX - stageRect.left, boxY = event.clientY - stageRect.top;
  const offsetX = (boxX / stageRect.width < 0.5) ? 20 : -box.offsetWidth - 20;
  const offsetY = (boxY / stageRect.height < 0.5) ? 20 : -box.offsetHeight - 20;
  box.style.left = `${event.clientX + offsetX}px`;
  box.style.top = `${event.clientY + offsetY}px`;
}, 16);

/* ===================== Derived ===================== */
const elapsedTimeDisplay = computed(() => formatTicks(tickCount.value));

const avgLifespan = computed(() => {
  return stats.value.deadCount > 0
    ? formatTicks(stats.value.totalLifespan / stats.value.deadCount)
    : "–";
});
</script>

<style scoped>
.bbyworld-page {
  display:flex;
  width:100%;
  height:var(--full-height);
  box-sizing:border-box;
  padding:var(--padding);
}
.world-layout{display:flex;flex-direction:row;width:100%;height:100%;gap:var(--spacing);overflow:hidden}
.world-left{flex:1 1 320px;min-width:280px;height:100%;display:flex;flex-direction:column}
.world-right{flex:0 1 var(--full-height);display:flex;align-items:center;justify-content:center;height:100%;max-width:var(--full-height);min-width:0;position:relative}
.vertical-panel{position:relative;width:100%;height:100%;overflow-y:auto;padding:var(--padding);background:var(--panel-colour);border:var(--border);border-radius:var(--border-radius);box-shadow:var(--box-shadow);display:flex;flex-direction:column;gap:calc(var(--spacing)*1.1)}
.vertical-panel h1{margin:0;text-align:center;line-height:1.05}
.world-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.group-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.group-row{display:grid;grid-template-columns: 2fr 1fr 1fr 1.5fr 1fr 1fr; gap:.25rem;position:relative;cursor:pointer; align-items: center;}
.group-row.header{font-weight:700;cursor:default}
.group-row.selected{outline:1px solid var(--accent-colour);}
.group-bar{position:absolute;top:0;left:0;bottom:0;opacity:.2;pointer-events:none}
.colour-cell{display:flex;align-items:center;gap:.25rem}
.colour-swatch{width:1rem;height:1rem;border:var(--border);border-radius:2px; flex-shrink: 0;}
.world-stage{position:relative;width:100%;height:100%;max-width:100%;max-height:100%;aspect-ratio:1/1;overflow:hidden;border:var(--border);border-radius:var(--border-radius);background:var(--bby-colour-black)}
.world-stage .stack{width:100%;height:100%;display:grid;align-items:start;justify-content:start}
.world-stage .stack canvas{
  grid-area:1/1;
  image-rendering:pixelated;
  image-rendering:crisp-edges;
  display:block;
}
.zoom-scope{position:fixed;width:256px;height:256px;pointer-events:none;z-index:1000}
.zoom-scope canvas{width:100%;height:100%;image-rendering:pixelated;display:block}
.zoom-scope .scope-info{position:absolute;bottom:0;left:0;background:rgba(0,0,0,.7);color:#fff;font-size:12px;padding:4px;font-family:monospace;line-height:1.2;white-space:nowrap}
.grp{display:flex;flex-direction:column;gap:.5rem}
.legend{font-size:var(--small-font-size);display:flex;flex-direction:column;gap:.25rem;line-height:1.2}
.section{font-size:var(--small-font-size);text-align:center;opacity:.85;letter-spacing:.1em;text-transform:uppercase}
.action{display:block;width:100%;padding:.4rem .5rem;transition:all .2s ease-out;text-align:center}
.action.active,.action:active{background:var(--accent-hover);border-color:var(--accent-colour)!important}
.row2{display:grid;grid-template-columns:repeat(2,1fr);gap:.5rem}
.row3{display:grid;grid-template-columns:1fr auto 1fr;gap:.5rem;align-items:center}
.zoom-display{text-align:center;font-size:var(--small-font-size)}
#board-size{width:4rem;text-align:center}
.card-swatch-bar{display:flex;flex-wrap:wrap;gap:.5rem}
.card-swatch{border:var(--border);padding:2px;background:var(--panel-colour);cursor:pointer}
.card-swatch img{width:32px;height:32px;image-rendering:pixelated;display:block}
.card-swatch.selected{border-color:var(--accent-colour);background:var(--accent-hover)}
.group-insight{display:flex;align-items:center;gap:.5rem;font-size:var(--small-font-size)}
.family-tree{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.family-link{cursor:pointer;margin-right:.25rem;color:var(--accent-colour)}
.family-link:hover{text-decoration:underline}
.cell-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.cell-colour{display:flex;align-items:center;gap:.25rem}
@media (max-width:720px){.world-layout{flex-direction:column}.world-left{width:100%;flex-basis:auto;height:auto}.vertical-panel{overflow-y:visible}.world-right{width:100%;max-width:none;flex:0 0 auto}}
</style>