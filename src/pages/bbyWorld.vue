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

          <div class="grp">
            <label class="section">legend</label>
            <div class="legend">
              <p><strong>Shade = strength:</strong> opaque pixels spawn tougher cells; transparent shades are frail but nimble.</p>
              <p><strong>Colours = genes:</strong> the intensity of each channel is the strength of that trait—red for aggression & heat-seeking, blue boosts moisture affinity, green fuels metabolism & nutrient hunger, while alpha sets overall toughness.</p>
              <p><strong>Trade-offs:</strong> excess red burns energy, greens need elbow-room, blues pool but slip off heights, and high alpha is mighty yet sluggish.</p>
              <p><strong>Genetics:</strong> when two cells merge, each colour channel mixes according to parental strength so offspring wear a visible blend. New births flash briefly to mark their arrival.</p>
              <p><strong>Attraction:</strong> cells drift toward heat, moisture, or nutrients in proportion to their red, blue, and green channels.</p>
              <p><strong>Group stats:</strong> % shows each colour's share of living cells; age and energy track group averages.</p>
            </div>
          </div>

          <div class="grp">
            <label class="section">speed ({{ ticksPerSecond }} TPS)</label>
            <div class="row2">
              <button class="action" @click="slowDown">-</button>
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

// total scale applied to canvas
const totalScale = computed(() => baseScale.value * zoomFactor.value);

// style for canvas transform
const canvasStyle = computed(() => ({
  transform: `translate(${pan.value.x}px, ${pan.value.y}px) scale(${totalScale.value})`,
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
function speedUp() { ticksPerSecond.value = Math.min(240, ticksPerSecond.value + 10); }
function slowDown() { ticksPerSecond.value = Math.max(1, ticksPerSecond.value - 10); }

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
  heading: Heading;        // chain direction
  turnBias:number;         // smoothness (smaller = straighter)
  coop:number;             // cooperation affinity
  cargo:number;            // carried nutrients
  friends: Record<number, number>; // pairwise affinity
  decayRate:number;        // alpha loss per tick
};

/* ===================== World State ===================== */
const livingCells = ref<GridCell[]>([]);
let nextCellId = 1;
const cellById: Record<number, GridCell> = {};
const familyTree: Record<number, {parents:number[]; children:number[]}> = {};
// Spatial occupancy is tracked with a plain array indexed by the numeric
// key produced by `I(x,y)`.  Earlier versions used a `Map` with string
// keys such as "x,y" for lookups.  During large "light blooms" thousands
// of cells are spawned and moved every tick which caused that Map to churn
// out temporary strings and wrapper objects, eventually exhausting memory
// and crashing the page.  Using a preallocated array keeps lookups O(1)
// and avoids those allocations entirely.
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

const groupStats = computed<ColourGroupStat[]>(() => {
  const base = {
    count: 0,
    totalStrength: 0,
    totalAge: 0,
    totalEnergy: 0,
  };
  const groups: Record<string, typeof base> = {};
  const STEP = 48; // bucket size for colour grouping
  const quant = (v: number) => Math.min(255, Math.round(v / STEP) * STEP);
  for (const c of livingCells.value) {
    const key = rgbToHex(quant(c.r), quant(c.g), quant(c.b));
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

const DYE_RATE = 0.001; // how quickly cells tint terrain
const BALANCE_RATE = 0.005; // environmental pressure toward colour parity

function I(x:number,y:number){ const s=S(); return ((x & (s-1)) + ((y & (s-1)) * s)) >>> 0; }

function colourDominance(v:number, o1:number, o2:number): number {
  const diff = v - Math.max(o1, o2);
  return diff * Math.abs(diff) * 0.7;
}

/* Renderer buffer */
let frame = new Uint8ClampedArray(0);
let frameImg: ImageData | null = null;

/* ===================== RNG ===================== */
let rng = mulberry32(1337);
function mulberry32(a:number){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
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
  // Reset arrays without creating new ones to avoid extra allocations
  livingCells.value.length = 0;
  spatialMap.fill(null);
  stats.value = { warDeaths:0, babyMerges:0, squishDeaths:0, fadedDeaths:0, totalLifespan:0, deadCount:0 };
  tickCount.value = 0;
}

function applyBoardSize(){
  // reset pan/zoom to fit
  pan.value = {x:0, y:0};
  zoomFactor.value = 1;
  // resize canvas attrs
  const canvas = gameCanvas.value;
  if (canvas){ canvas.width = S(); canvas.height = S(); }
  allocateWorldArrays(S());
  clearWorld();
  computeBaseScale(); // recalc fit scale
}

function computeBaseScale(){
  const stage = stageEl.value;
  if (!stage) return;
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  const s = S();
  if (w <= 0 || h <= 0 || s <= 0) return;
  // fit entire board into stage
  baseScale.value = Math.min(w / s, h / s);
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

  // set up resize observer to keep baseScale (fit) fresh
  if (stageEl.value) {
    resizeObs = new ResizeObserver(() => computeBaseScale());
    resizeObs.observe(stageEl.value);
    computeBaseScale();
  }

  // scope canvas
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
  timeSinceLastTick += deltaTime;

  // Cap the number of simulation updates processed in a single frame. When
  // the tab is hidden or timers are throttled `deltaTime` can grow very
  // large. Without a cap the loop below would attempt to "catch up" by
  // running thousands of updates at once, freezing or crashing the page.
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
    // Drop any excess accumulated time to avoid spiralling further.
    timeSinceLastTick = 0;
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

function moveSolid(from:number, to:number, amt:number){
  const current = solidGrid[from];
  const moveAmt = Math.min(current, amt);
  if (moveAmt <= 0 || current <= 0) return 0;
  const frac = moveAmt / current;
  const r = dyeRField[from] * frac;
  const g = dyeGField[from] * frac;
  const b = dyeBField[from] * frac;
  solidGrid[from] -= moveAmt;
  dyeRField[from] -= r;
  dyeGField[from] -= g;
  dyeBField[from] -= b;
  solidGrid[to] = Math.min(6, solidGrid[to] + moveAmt);
  dyeRField[to] += r;
  dyeGField[to] += g;
  dyeBField[to] += b;
  return moveAmt;
}

function worldTick(totalR=0,totalG=0,totalB=0){
  // Baby colour biases fields *gently*
  let skyR = (Number(currentColour.r)||0)/255 * 0.004;
  let skyG = (Number(currentColour.g)||0)/255 * 0.004;
  let skyB = (Number(currentColour.b)||0)/255 * 0.004;

  // Apply negative feedback so no single colour dominates the world.
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

  // The world previously began completely barren which meant freshly born
  // cells had nothing to metabolise unless they immediately encountered
  // another deposit.  Inject a tiny baseline amount of each field every tick
  // so there is always some resource to draw from.
  const base = 0.0008;

  const s=S();
  for (let y=0;y<s;y++){
    for (let x=0;x<s;x++){
      const i = I(x,y);
      if (solidGrid[i] > 0){
        nutrientField[i] += Math.min(0.02*solidGrid[i], 0.05);
        heatField[i] *= 0.999;
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

  // Tally colour populations to inform environmental balancing
  let totalR = 0, totalG = 0, totalB = 0;
  for (const c of livingCells.value) {
    totalR += c.r;
    totalG += c.g;
    totalB += c.b;
  }

  worldTick(totalR, totalG, totalB);

  // metabolism & micro-reactions
  for (let i = livingCells.value.length - 1; i >= 0; i--) {
    const c = livingCells.value[i];
    c.coop *= 0.95; // cooperative affinity decays each tick
    // Red aggression burns extra energy while alpha heft slows overall output
    c.energy -= c.metabolism + c.aggression*0.05;
    c.age += 1;

    const ii = I(c.x, c.y);
    for (const [dx, dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
      const nx = (c.x + dx + S()) % S();
      const ny = (c.y + dy + S()) % S();
      const n = spatialMap[I(nx, ny)];
      if (n && n.alive) adjustAffinity(c, n, 0.01);
    }
    // Basic environmental energy intake allows cells to sustain themselves
    // instead of rapidly starving. Each colour channel draws from its
    // matching field, converting a small portion into energy.
    const Rf = c.r/255, Bf = c.b/255, Gf = c.g/255;
    dyeRField[ii] = Math.min(255, dyeRField[ii] + c.r * DYE_RATE);
    dyeGField[ii] = Math.min(255, dyeGField[ii] + c.g * DYE_RATE);
    dyeBField[ii] = Math.min(255, dyeBField[ii] + c.b * DYE_RATE);
    const domR = colourDominance(Rf, Bf, Gf);
    const domB = colourDominance(Bf, Rf, Gf);
    const domG = colourDominance(Gf, Rf, Bf);

    // transparency fades over time based on each cell's inherent decay rate
    c.a = Math.max(0, c.a - c.decayRate);
    c.strength = c.a / 255;
    if (c.a < VISIBLE_ALPHA) {
      recordDeath(c, "fade");
      continue;
    }
    const ageFactor = Math.min(1, c.age / 1000);
    const alphaN = c.a / 255;
    let fertAlpha = 0;
    if (alphaN >= FERTILITY_ALPHA_MIN && alphaN <= FERTILITY_ALPHA_MAX) {
      if (alphaN <= FERTILITY_ALPHA_PEAK) {
        fertAlpha = (alphaN - FERTILITY_ALPHA_MIN) / (FERTILITY_ALPHA_PEAK - FERTILITY_ALPHA_MIN);
      } else {
        fertAlpha = (FERTILITY_ALPHA_MAX - alphaN) / (FERTILITY_ALPHA_MAX - FERTILITY_ALPHA_PEAK);
      }
    }
    c.fertility = ageFactor * fertAlpha;

    let gain = 0;
    const handleField = (dom:number, field:Float32Array, idx:number) => {
      if (dom === 0) return;
      const amt = 0.02 * Math.abs(dom);
      if (dom > 0) {
        const take = Math.min(amt, field[idx]);
        field[idx] -= take;
        gain += take * 10;
      } else {
        field[idx] += amt;
        gain -= amt * 10;
      }
    };
    handleField(domR, heatField, ii);
    handleField(domB, moistureField, ii);
    handleField(domG, nutrientField, ii);
    if (domG > 0) {
      nutrientField[ii] += 0.004 * Gf * domG;
    } else if (domG < 0) {
      nutrientField[ii] = Math.max(0, nutrientField[ii] - 0.004 * Gf * (-domG));
    }
    if (domR > 0) {
      const fuel = Math.min(0.015 * Rf * domR, nutrientField[ii]);
      nutrientField[ii] -= fuel;
      gain += fuel * 25;
      if (fuel === 0) c.energy -= 0.1;
    }
    // Mixed colour synergies encourage varied emergent behaviours by letting
    // cells with blended channels transmute nearby resources. These effects
    // provide alternatives to chasing a perfectly neutral colour.
    const mixRB = Math.min(Rf, Bf); // magenta: steam heats up
    if (mixRB > 0.3) {
      const take = Math.min(0.01*mixRB, moistureField[ii]);
      moistureField[ii] -= take;
      heatField[ii]     += take*1.5;
      gain              += take*5;
    }
    const mixBG = Math.min(Bf, Gf); // cyan: water feeds growth
    if (mixBG > 0.3) {
      const take = Math.min(0.01*mixBG, nutrientField[ii]);
      nutrientField[ii] -= take;
      moistureField[ii] += take*1.5;
      gain              += take*5;
    }
    const mixRG = Math.min(Rf, Gf); // yellow: warmth enriches soil
    if (mixRG > 0.3) {
      const take = Math.min(0.01*mixRG, heatField[ii]);
      heatField[ii]     -= take;
      nutrientField[ii] += take*1.5;
      gain              += take*5;
    }

    c.energy = Math.min(c.energy + gain, 260);

    // Bright cells struggle near the depths and dim cells shun the dazzling.
    const brightness = (c.r + c.g + c.b) / 3;
    const deep = S() * 0.75;
    if (brightness > 200 && c.y > deep) {
      c.energy -= (brightness - 200) * 0.01;
    }
    if (brightness < 100) {
      let brightNeighbours = 0;
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          if (dx === 0 && dy === 0) continue;
          const nx = (c.x + dx + S()) % S();
          const ny = (c.y + dy + S()) % S();
          const neigh = spatialMap[I(nx, ny)];
          if (neigh && neigh.alive) {
            const nb = (neigh.r + neigh.g + neigh.b) / 3;
            if (nb > 200) brightNeighbours++;
          }
        }
      }
      if (brightNeighbours > 0) {
        c.energy -= brightNeighbours * 0.5;
      }
    }

    // Blue cells slowly erode nearby solids and push debris outward
    if (domB !== 0) {
      const erosion = 0.004 * Bf * Math.abs(domB);
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const nx = (c.x + dx + S()) % S();
          const ny = (c.y + dy + S()) % S();
          const ni = I(nx, ny);
          const limit = domB > 0 ? solidGrid[ni] : 6 - solidGrid[ni];
          const take = Math.min(erosion, limit);
          if (take > 0) {
            if (domB > 0) {
              // determine where to push removed material
              let px: number, py: number;
              if (dx === 0 && dy === 0) {
                const dirs = [[1,0],[-1,0],[0,1],[0,-1]];
                const d = dirs[(rand() * dirs.length) | 0];
                px = (c.x + d[0] + S()) % S();
                py = (c.y + d[1] + S()) % S();
              } else {
                px = (c.x + dx * 2 + S()) % S();
                py = (c.y + dy * 2 + S()) % S();
              }
              const pi = I(px, py);
              const push = take * 0.5;
              moveSolid(ni, pi, push);

              const resource = take - push;
              erodeSolid(ni, resource);
              moistureField[ni] += resource * 0.6;
              nutrientField[ni] += resource * 0.3;
              heatField[ni]     += resource * 0.1;
            } else {
              solidGrid[ni] += take;
              moistureField[ni] = Math.max(0, moistureField[ni] - take * 0.6);
              nutrientField[ni] = Math.max(0, nutrientField[ni] - take * 0.3);
              heatField[ni]     = Math.max(0, heatField[ni] - take * 0.1);
            }
          }
        }
      }
    }

    // Green cells chew through nearby ground, releasing nutrients
    if (domG !== 0) {
      const erosion = 0.002 * Gf * Math.abs(domG);
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const nx = (c.x + dx + S()) % S();
          const ny = (c.y + dy + S()) % S();
          const ni = I(nx, ny);
          const limit = domG > 0 ? solidGrid[ni] : 6 - solidGrid[ni];
          const take = Math.min(erosion, limit);
          if (take > 0) {
            if (domG > 0) {
              erodeSolid(ni, take);
              nutrientField[ni] += take * 0.8;
              moistureField[ni] += take * 0.1;
              heatField[ni]     += take * 0.1;
            } else {
              solidGrid[ni] += take;
              nutrientField[ni] = Math.max(0, nutrientField[ni] - take * 0.8);
              moistureField[ni] = Math.max(0, moistureField[ni] - take * 0.1);
              heatField[ni]     = Math.max(0, heatField[ni] - take * 0.1);
            }
          }
        }
      }
    }

    // Red cells bake the earth, hardening ground and drying it out
    if (domR !== 0) {
      const harden = 0.0025 * Rf * Math.abs(domR);
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const nx = (c.x + dx + S()) % S();
          const ny = (c.y + dy + S()) % S();
          const ni = I(nx, ny);
          if (domR > 0) {
            solidGrid[ni] = Math.min(6, solidGrid[ni] + harden);
            moistureField[ni] = Math.max(0, moistureField[ni] - harden * 0.5);
          } else {
            erodeSolid(ni, harden);
            moistureField[ni] += harden * 0.5;
          }
        }
      }
    }

    // Green cells crave space to grow – reward solitude but punish crowding
    const neighbours = countOccupiedAdjacent(c.x, c.y);
    if (domG !== 0) {
      if (neighbours <= 1) {
        c.energy = Math.min(c.energy + Gf*domG*0.5, 260);
      } else if (neighbours > 3) {
        c.energy -= (neighbours-3) * Gf * domG * 2;
      }
    }

    // Blue cells slip toward lower ground or climb high when suppressed
    if (domB !== 0) {
      let target = solidGrid[ii];
      let bx = c.x, by = c.y;
      const dirs:[number,number][] = [[1,0],[-1,0],[0,1],[0,-1]];
      for (const [dx,dy] of dirs){
        const nx = (c.x + dx + S()) % S();
        const ny = (c.y + dy + S()) % S();
        const ni = I(nx, ny);
        if (domB > 0) {
          if (!spatialMap[ni] && solidGrid[ni] + 0.1 < target){
            target = solidGrid[ni];
            bx = nx; by = ny;
          }
        } else {
          if (!spatialMap[ni] && solidGrid[ni] - 0.1 > target){
            target = solidGrid[ni];
            bx = nx; by = ny;
          }
        }
      }
      if (bx !== c.x || by !== c.y){
        performMove(c, bx, by);
        deposit(c);
      }
    }

    // --- Cooperation: share energy with compatible neighbours ---
    const shareDirs:[number,number][] = [[1,0],[-1,0],[0,1],[0,-1]];
    for (const [dx,dy] of shareDirs){
      const nx = (c.x + dx + S()) % S();
      const ny = (c.y + dy + S()) % S();
      const neighbour = spatialMap[I(nx, ny)];
      if (!neighbour || !neighbour.alive) continue;
      const comp = compatibility(c, neighbour);
      if (comp > 0.6){
        const boost = comp * 0.02;
        c.coop = Math.min(1, c.coop + boost);
        neighbour.coop = Math.min(1, neighbour.coop + boost);
      }
      if (comp > 0.65 && c.energy > neighbour.energy + 20){
        const diff = c.energy - neighbour.energy;
        const transfer = Math.min(diff * 0.25 * comp, 30);
        c.energy -= transfer;
        neighbour.energy = Math.min(neighbour.energy + transfer, 260);
      }
    }

    // Animal behaviour: dark and purple cells ferry nutrients and gift energy
    const isAnimal = (c.r + c.g + c.b < 60) || (c.r > 150 && c.b > 150 && c.g < 80);
    if (isAnimal) {
      if (c.cargo < 20 && nutrientField[ii] > 0.01) {
        const take = Math.min(0.01, nutrientField[ii]);
        nutrientField[ii] -= take;
        c.cargo += take * 100;
      }
      for (const [dx, dy] of shareDirs) {
        const nx = (c.x + dx + S()) % S();
        const ny = (c.y + dy + S()) % S();
        const neighbour = spatialMap[I(nx, ny)];
        if (!neighbour || !neighbour.alive || c.cargo <= 0) continue;
        const nIsAnimal = (neighbour.r + neighbour.g + neighbour.b < 60) || (neighbour.r > 150 && neighbour.b > 150 && neighbour.g < 80);
        if (nIsAnimal) {
          const gift = Math.min(5, c.cargo);
          neighbour.energy = Math.min(260, neighbour.energy + gift);
          c.cargo -= gift;
        }
      }
    }

    // Only squash cells that fail to recover enough energy after drawing from
    // their local field this tick.
    if (c.energy <= 0) {
      if (domB > 0) {
        let pooled = false;
        for (const [dx, dy] of shareDirs) {
          const nx = (c.x + dx + S()) % S();
          const ny = (c.y + dy + S()) % S();
          const neighbour = spatialMap[I(nx, ny)];
          if (neighbour && neighbour.alive) {
            const nDomB = colourDominance(neighbour.b/255, neighbour.r/255, neighbour.g/255);
            if (nDomB > 0) { pooled = true; break; }
          }
        }
        if (pooled) {
          c.energy = 1;
          continue;
        }
        const escape = findEmptyAdjacent(c.x, c.y);
        if (escape) {
          const [ex, ey] = escape;
          performMove(c, ex, ey);
          c.energy = 5;
          continue;
        }
      }
      recordDeath(c, "squish");
      continue;
    }
  }

  // move slice — handle a slightly larger portion each tick to keep things lively
  const updatesPerTick = Math.ceil(livingCells.value.length / 80) || 1;
  for (let i = 0; i < updatesPerTick; i++) {
    const cell = pickRandomLivingCell();
    if (cell) {
      const [dx, dy, newH] = chooseChainDir(cell);
      if (attemptMove(cell, dx, dy)) {
        cell.heading = newH;
        deposit(cell);
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
    const scale = Math.min(1, 64 / Math.max(img.width, img.height)); // MAX_STAMP=64
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
const FERTILITY_ALPHA_MIN = 0.3
const FERTILITY_ALPHA_MAX = 0.9
const FERTILITY_ALPHA_PEAK = 0.7
const BIRTH_FLASH_TICKS = 8
const MIN_DECAY_RATE = 0.02
const MAX_DECAY_RATE = 0.05

function randomDecayRate(){
  return MIN_DECAY_RATE + rand() * (MAX_DECAY_RATE - MIN_DECAY_RATE);
}

function makeCell(px:number,py:number,r:number,g:number,b:number,a:number): GridCell {
  const A = Math.max(VISIBLE_ALPHA, a);
  const strength = (A/255);              // weight 0..1
  let energy = 60 + strength*140;
  let metabolism = 0.18 + (g/255)*0.20;  // green=hungry growth
  let aggression  = (r/255)*0.9;         // red=fighty
  let fertility   = 0;                   // fertility will grow with age/transparency

  const heading = (Math.floor(rand()*4) as Heading);
  const cell: GridCell = {
    id: nextCellId++,
    r, g, b, a: A, x: px, y: py, energy, alive: true, birthTick: tickCount.value, age: 0,
    aggression, fertility, metabolism,
    strength, heading, turnBias: 0.3 + (1 - strength) * 0.4,
    coop: 0,
    cargo: 0,
    friends: {},
    decayRate: randomDecayRate(),
  };
  cellById[cell.id] = cell;
  familyTree[cell.id] = {parents: [], children: []};

  // Newborn cells previously spawned into completely empty tiles and
  // immediately began burning energy faster than they could recover it. By
  // seeding a little of their preferred field type at birth, they have an
  // initial resource to metabolise which prevents the whole population from
  // dying out in the opening moments of a game.
  const idx = I(px, py);
  const Rf = r/255, Gf = g/255, Bf = b/255;
  heatField[idx]     += 0.1 + 0.2*Rf;
  moistureField[idx] += 0.1 + 0.2*Bf;
  nutrientField[idx] += 0.1 + 0.2*Gf;

  return cell;
}

function placeImage(event: MouseEvent) {
  if (!loadedImageData) return;
  const canvas = gameCanvas.value; if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  const clickX = (event.clientX - rect.left) * (canvas.width / rect.width);
  const clickY = (event.clientY - rect.top) * (canvas.height / rect.height);

  const mouseGridX = Math.floor(clickX);
  const mouseGridY = Math.floor(clickY);

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
            // Vue wraps objects pushed into reactive arrays with proxies.
            // Retrieve the proxied instance so `spatialMap` holds the same
            // reference as `livingCells`.  This ensures identity checks
            // succeed when removing cells later (e.g. during merges).
            spatialMap[key] = livingCells.value[livingCells.value.length - 1];
          }
        }
      }
    }
  }
}

/* ===================== Movement / Chains ===================== */
// This helper function shuffles an array in place
function shuffleArray(array: any[]) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(rand() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function chooseChainDir(cell:GridCell): [number,number,Heading] {
  const prefs: {h:Heading, score:number}[] = [];

  // Evaluate directions in a random order to avoid directional bias
  const headings: Heading[] = [0, 1, 2, 3];
  shuffleArray(headings);

  for (const h of headings) {

    const [dx,dy] = HEADING_VECS[h];
    const nx = (cell.x + dx + S()) % S();
    const ny = (cell.y + dy + S()) % S();
    const i = I(nx,ny);

    const heat = heatField[i], wet = moistureField[i], nut = nutrientField[i];
    const Rf = cell.r/255, Bf = cell.b/255, Gf = cell.g/255;
    const domR = colourDominance(Rf, Bf, Gf);
    const domB = colourDominance(Bf, Rf, Gf);
    const domG = colourDominance(Gf, Rf, Bf);
    let want = heat*Rf + wet*Bf + nut*Gf + (heat+wet+nut)*0.05;
    // Blue cells shy from climbing higher ground
    const hDiff = solidGrid[i] - solidGrid[I(cell.x, cell.y)];
    want -= Math.max(0, hDiff) * Bf * domB;
    // Red cells hunt for fuel (nutrient and dryness)
    want += (nut - wet) * Rf * domR * 0.5;

    // Stronger cells should be less deterred by solid tiles. Previously the
    // penalty increased with strength, causing fragile cells to push through
    // rock more easily than tough ones. Invert the relationship so that
    // strong cells incur the minimum penalty while weak cells avoid solids.
    let solidPenalty = solidGrid[i] * (1 - cell.strength);
    if (Math.abs(cell.r - cell.g) < 20 && Math.abs(cell.g - cell.b) < 20) {
      solidPenalty *= 0.3;
    }
    const same = (h === cell.heading) ? 1 : 0;
    const turnPenalty = (h === cell.heading ? 0 : cell.turnBias);

    let score = want + same*0.15 - turnPenalty - solidPenalty;
    // Weak cells struggle in wet terrain, so make damp tiles less appealing
    // for them. Stronger cells are less affected by moisture.
    score -= (1 - cell.strength) * wet * 0.2;

    if (domG > 0) {
      if (wet > 0.1 && hasNearbyGreenBlue(nx, ny, 2)) {
        score += wet * 0.3 * domG;
      } else {
        score -= 0.4 * domG;
      }
    } else if (domG < 0) {
      if (wet > 0.1 && hasNearbyGreenBlue(nx, ny, 2)) {
        score -= wet * 0.3 * (-domG);
      } else {
        score += 0.4 * (-domG);
      }
    }

    // --- Social bias ---
    // Peek at the neighbour in this direction. Compatible neighbours draw
    // cells together while enemies repel, nudging movement toward emergent
    // groups.
    const neighbour = spatialMap[i];
    if (neighbour && neighbour.alive) {
      const comp = compatibility(cell, neighbour);
      if (comp > 0.6) {
        score += comp * 0.2;
      } else {
        score -= (1 - comp) * 0.2;
      }
    }

    if (Math.abs(cell.r - cell.g) < 20 && Math.abs(cell.g - cell.b) < 20) {
      const density = neighbourCount(nx, ny);
      score += (1 - density / 8) * 0.3;
    }
    // amplify a touch of randomness so groups don't lock into perfect stability
    score += (rand()-0.5)*0.1;

    prefs.push({h: h as Heading, score});
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
    const idx = I(nx, ny);
    if (!spatialMap[idx] && solidGrid[idx] <= 0) {
      return [nx, ny];
    }
  }
  return null;
}

function countOccupiedAdjacent(x:number,y:number): number {
  const dirs:[number,number][] = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
  let c=0;
  for (const [dx,dy] of dirs){
    const nx=(x+dx+S())%S();
    const ny=(y+dy+S())%S();
    if (spatialMap[I(nx,ny)]) c++;
  }
  return c;
}

function hasNearbyGreenBlue(x:number,y:number,dist=2): boolean {
  for (let dy=-dist; dy<=dist; dy++){
    for (let dx=-dist; dx<=dist; dx++){
      if (dx===0 && dy===0) continue;
      const nx=(x+dx+S())%S();
      const ny=(y+dy+S())%S();
      const neighbour = spatialMap[I(nx,ny)];
      if (neighbour && neighbour.alive){
        const r = neighbour.r/255, g = neighbour.g/255, b = neighbour.b/255;
        const gDom = g>0.5 && g>r && g>b;
        const bDom = b>0.5 && b>r && b>g;
        if (gDom || bDom) return true;
      }
    }
  }
  return false;
}

function attemptMove(cell:GridCell, dx:number, dy:number): boolean {
  // stronger cells used to sit still half the time which made the world feel static.
  // reduce the rest chance so even tough pixels wander and bump into neighbours.
  const restChance = cell.strength*0.2;
  if (rand() < restChance) return false;
  const newX = (cell.x + dx + S()) % S();
  const newY = (cell.y + dy + S()) % S();
  const key = I(newX, newY);
  const target = spatialMap[key];
  const tIndex = key;

  const currentH = solidGrid[I(cell.x, cell.y)];
  const targetH = solidGrid[tIndex];
  const Rf = cell.r/255, Gf = cell.g/255, Bf = cell.b/255;
  const domB = colourDominance(Bf, Rf, Gf);
  if (domB > 0 && targetH > currentH + 0.1) return false;
  if (domB < 0 && targetH < currentH - 0.1) return false;

  if (targetH > 0){
    if (domB > 0){
      const erode = Math.min(targetH, Bf*(0.05 + 0.1*(cell.energy/200)) * domB);
      erodeSolid(tIndex, erode);
      moistureField[tIndex] += erode*0.5;

      const px = (newX + dx + S()) % S();
      const py = (newY + dy + S()) % S();
      const pi = I(px, py);
      if (!spatialMap[pi]){
        const moved = solidGrid[tIndex]*0.6;
        moveSolid(tIndex, pi, moved);
      }
      if (!target && solidGrid[tIndex] < 0.2) {
        performMove(cell, newX, newY);
        return true;
      }
    } else {
      // Likewise, strong cells should have a lower chance of getting stuck
      // when moving through solids. The previous formula increased the stuck
      // probability with strength. Flip it so strength reduces the likelihood
      // of becoming trapped.
      const stuckP = Math.min(0.9, 0.8 * (1 - cell.strength) * Math.min(1, solidGrid[tIndex]/3));
      if (rand() < stuckP) return false;
    }
  }

  if (!target){
    performMove(cell, newX, newY);
    return true;
  }

  if (target.alive){
    const pairAff = getAffinity(cell, target);
    const coopBoost = (cell.coop + target.coop) * 0.2 + pairAff * 0.1;
    const pCompat = Math.min(1, compatibility(cell,target) * 0.8 + (cell.fertility+target.fertility)*0.1 + coopBoost);
    const baseWar = (cell.aggression+target.aggression)*0.35 + (heatField[tIndex]*0.25);
    const pWar    = Math.min(1, Math.max(0, baseWar - coopBoost*0.5 - pairAff*0.1));

    if (pCompat >= pWar){
      adjustAffinity(cell, target, 0.5);
      const spawn = findEmptyAdjacent(newX, newY) || findEmptyAdjacent(cell.x, cell.y);
      if (spawn){
        const [bx, by] = spawn;
        const baby = mergeBaby(cell, target, bx, by);
        livingCells.value.push(baby);
        spatialMap[I(bx, by)] = livingCells.value[livingCells.value.length - 1];
        stats.value.babyMerges++;
      }
      return false;
    } else {
      const envBoost = (
        (cell.r-target.r)/255 * heatField[tIndex] +
        (cell.b-target.b)/255 * moistureField[tIndex] +
        (cell.g-target.g)/255 * nutrientField[tIndex]
      ) * 30;

      const cellScore = cell.energy * (0.8 + 0.5*cell.aggression) + envBoost;
      const tarScore  = target.energy*(0.8 + 0.5*target.aggression) - envBoost;

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

  return false;
}

function performMove(moving:GridCell, toX:number, toY:number){
  spatialMap[I(moving.x, moving.y)] = null;
  moving.x = toX; moving.y = toY;
  spatialMap[I(toX, toY)] = moving;
}

/* ===================== Interactions ===================== */
function pickRandomLivingCell(): GridCell | null {
  if (livingCells.value.length === 0) return null;
  return livingCells.value[Math.floor(rand()*livingCells.value.length)];
}

function neighbourCount(x:number,y:number):number{
  let count=0;
  for(let dy=-1;dy<=1;dy++){
    for(let dx=-1;dx<=1;dx++){
      if(dx===0&&dy===0) continue;
      const ni = I((x+dx+S())%S(), (y+dy+S())%S());
      const c = spatialMap[ni];
      if(c && c.alive) count++;
    }
  }
  return count;
}

function getAffinity(a:GridCell, b:GridCell){
  return a.friends[b.id] || 0;
}

function adjustAffinity(a:GridCell, b:GridCell, delta:number){
  const clamp = (v:number)=>Math.min(10, Math.max(-10, v));
  a.friends[b.id] = clamp((a.friends[b.id]||0) + delta);
  b.friends[a.id] = clamp((b.friends[a.id]||0) + delta);
}

function compatibility(a:GridCell,b:GridCell){
  // cross-channel complement: blue↔red, red↔green, green↔blue
  const AR=a.r/255, AG=a.g/255, AB=a.b/255;
  const BR=b.r/255, BG=b.g/255, BB=b.b/255;
  const comp = (AR*BB + AG*BR + AB*BG) / 3;
  // normalise distance into [0,1] so compatibility stays bounded
  const dist = Math.hypot(AR-BR, AG-BG, AB-BB) / Math.sqrt(3);
  return 0.6*comp + 0.4*(1 - dist);
}

function mergeBaby(cell:GridCell,target:GridCell,x:number,y:number): GridCell {
  // Weight genetic contribution by parental strength so tougher parents pass on more of their colour.
  const totalS = Math.max(0.0001, cell.strength + target.strength);
  const wA = cell.strength / totalS;
  const wB = target.strength / totalS;

  // Blend channels but push slightly away from the average so colours don't
  // collapse toward a neutral grey. The drift is proportional to the parental
  // difference which encourages stronger hues to persist and mutate.
  function blendChannel(a:number, b:number, mut:number){
    const avg = a*wA + b*wB;
    const diff = a - b;
    const drift = diff * (rand()*0.25 - 0.125); // bias away from middle
    return Math.min(255, Math.max(0, Math.round(avg + drift + (rand()*mut - mut/2))));
  }

  const babyR = blendChannel(cell.r, target.r, 6);
  const babyG = blendChannel(cell.g, target.g, 6);
  const babyB = blendChannel(cell.b, target.b, 6);
  const babyA = 255;

  const totalE = Math.max(1, cell.energy + target.energy);
  const kid = makeCell(x,y,babyR,babyG,babyB,babyA);
  kid.energy = Math.min(totalE * 0.3, 240);
  cell.energy *= 0.7;
  target.energy *= 0.7;

  kid.aggression += (rand()*0.1-0.05);
  kid.metabolism += (rand()*0.04-0.02);
  const baseDecay = (cell.decayRate + target.decayRate) / 2;
  kid.decayRate = Math.min(MAX_DECAY_RATE, Math.max(MIN_DECAY_RATE, baseDecay + (rand()*0.01 - 0.005)));
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

  stats.value.totalLifespan += tickCount.value - cell.birthTick;
  stats.value.deadCount++;
  if (reason === "war") stats.value.warDeaths++;
  if (reason === "squish") stats.value.squishDeaths++;
  if (reason === "fade") stats.value.fadedDeaths++;

  const i = I(cell.x, cell.y);
  const solidAdd = 0.2 + 0.8*cell.strength; // alpha = stronger rock
  solidGrid[i] = Math.min(solidGrid[i] + solidAdd, 6);

  const energy = cell.energy;
  const Rf = cell.r/255, Bf = cell.b/255, Gf = cell.g/255;
  moistureField[i] += energy*(0.01 + 0.02*Bf);
  heatField[i]     += energy*(0.005 + 0.03*Rf);
  nutrientField[i] += energy*(0.01 + 0.04*Gf);

  spatialMap[I(cell.x, cell.y)] = null;
  const index = livingCells.value.findIndex(c => c === cell);
  if (index > -1) livingCells.value.splice(index, 1);
}

function deposit(cell:GridCell){
  const i = I(cell.x, cell.y);
  const Rf = cell.r/255, Bf = cell.b/255, Gf = cell.g/255;
  const e = (cell.energy/200);
  heatField[i]     += (0.02 + 0.08*e) * Rf;
  moistureField[i] += (0.02 + 0.06*e) * Bf;
  nutrientField[i] += (0.02 + 0.10*e) * Gf;

  // cross-channel reactions to boost colour interplay
  moistureField[i] = Math.max(0, moistureField[i] - (0.015*Rf)); // red dries
  heatField[i]     = Math.max(0, heatField[i] - (0.012*Bf));     // blue cools
  nutrientField[i] += 0.005*Bf;                                 // water dissolves
  heatField[i]     += 0.003*Gf;                                 // growth warms
  if (cell.cargo > 0) {
    nutrientField[i] += cell.cargo;
    cell.cargo = 0;
  }
}

/* ===================== Draw ===================== */
function drawGrid(ctx: CanvasRenderingContext2D) {
  if (!frameImg) return;

  const skyR = Number(currentColour.r)||0;
  const skyG = Number(currentColour.g)||0;
  const skyB = Number(currentColour.b)||0;

  const SKY_SCALE = 0.03;     // much subtler sky tint
  const FIELD_SCALE = 80;     // dim field glow
  const FLOOR_ALPHA = 0.10;   // ~10% opacity

  const s=S();

  // base + faint field glow and solids darken in one pass
  for (let y=0;y<s;y++){
    for (let x=0;x<s;x++){
      const off = (x + y*s)*4;
      const ii = I(x,y);
      const H = Math.min(255, Math.floor(heatField[ii]*FIELD_SCALE));
      const W = Math.min(255, Math.floor(moistureField[ii]*FIELD_SCALE));
      const N = Math.min(255, Math.floor(nutrientField[ii]*FIELD_SCALE));

      const baseR = 16 + (skyR*SKY_SCALE)|0;
      const baseG = 16 + (skyG*SKY_SCALE)|0;
      const baseB = 18 + (skyB*SKY_SCALE)|0;

      const glowR = baseR + H;
      const glowG = baseG + N;
      const glowB = baseB + W;

      const a = FLOOR_ALPHA;
      let r = (baseR*(1-a) + glowR*a) | 0;
      let g = (baseG*(1-a) + glowG*a) | 0;
      let b = (baseB*(1-a) + glowB*a) | 0;

      const m = solidGrid[ii];
      if (m>0){
        const gVal = Math.max(0, 180 - Math.floor(m*25));
        r = (r*0.6 + gVal*0.4)>>>0;
        g = (g*0.6 + gVal*0.4)>>>0;
        b = (b*0.6 + gVal*0.4)>>>0;
      }

      const dr = dyeRField[ii];
      const dg = dyeGField[ii];
      const db = dyeBField[ii];
      const dyeTotal = dr + dg + db;
      if (dyeTotal > 0){
        const dyeAlpha = Math.min(0.4, dyeTotal / 765);
        const rr = dr / dyeTotal * 255;
        const gg = dg / dyeTotal * 255;
        const bb = db / dyeTotal * 255;
        r = (r*(1-dyeAlpha) + rr*dyeAlpha) | 0;
        g = (g*(1-dyeAlpha) + gg*dyeAlpha) | 0;
        b = (b*(1-dyeAlpha) + bb*dyeAlpha) | 0;
      }

      const terrainAlpha = Math.min(255, Math.floor((m / 6) * 255));
      frame[off  ] = r;
      frame[off+1] = g;
      frame[off+2] = b;
      frame[off+3] = terrainAlpha;
    }
  }

  // cells on top
  for (const c of livingCells.value){
    const off = (c.x + c.y*s)*4;
    frame[off  ] = c.r;
    frame[off+1] = c.g;
    frame[off+2] = c.b;
    frame[off+3] = Math.max(0, Math.min(255, c.a));

    if (c.age < BIRTH_FLASH_TICKS){
      const flash = 1 - c.age / BIRTH_FLASH_TICKS;
      frame[off  ] = Math.min(255, frame[off  ] + flash*200);
      frame[off+1] = Math.min(255, frame[off+1] + flash*200);
      frame[off+2] = Math.min(255, frame[off+2] + flash*200);
    }
  }

  ctx.putImageData(frameImg, 0, 0);

  ctx.lineWidth = 1;
  for (const c of livingCells.value) {
    ctx.strokeStyle = `rgba(${c.r},${c.g},${c.b},1)`;
    ctx.strokeRect(c.x + 0.5, c.y + 0.5, 1, 1);
  }
}

/* ===================== Scope ===================== */
const updateScope = throttle((event: MouseEvent) => {
  if (!scopeActive.value) return;
  const canvas = gameCanvas.value;
  const scope = scopeCanvas.value;
  const box = scopeBox.value;
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
      const sx = hx - half + dx;
      const sy = hy - half + dy;
      let r = 0, g = 0, b = 0, a = 255;
      if (sx >= 0 && sy >= 0 && sx < s && sy < s) {
        const off = (sx + sy * s) * 4;
        r = frame[off];
        g = frame[off + 1];
        b = frame[off + 2];
        a = frame[off + 3];
      }
      ctx.fillStyle = `rgba(${r},${g},${b},${a/255})`;
      ctx.fillRect(dx * pixelSize, dy * pixelSize, pixelSize, pixelSize);
    }
  }
  ctx.strokeStyle = 'rgba(255,255,255,0.7)';
  ctx.lineWidth = 1;
  ctx.strokeRect(0, 0, scope.width, scope.height);
  ctx.strokeStyle = 'rgba(0,0,0,0.7)';
  ctx.strokeRect(half * pixelSize, half * pixelSize, pixelSize, pixelSize);

  if (hx >= 0 && hy >= 0 && hx < s && hy < s) {
    const ii = I(hx, hy);
    hoverEnv.value = {
      x: hx,
      y: hy,
      heat: heatField[ii],
      moisture: moistureField[ii],
      nutrient: nutrientField[ii],
    };
    hoverCell.value = spatialMap[ii] || null;
  } else {
    hoverEnv.value = { x: hx, y: hy, heat: 0, moisture: 0, nutrient: 0 };
    hoverCell.value = null;
  }

  const offsetX = (hx / s < 0.5) ? 20 : -box.offsetWidth - 20;
  const offsetY = (hy / s < 0.5) ? 20 : -box.offsetHeight - 20;
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
.group-row{display:grid;grid-template-columns:repeat(7,auto);gap:.25rem;position:relative}
.group-row.header{font-weight:700}
.group-bar{position:absolute;top:0;left:0;bottom:0;opacity:.2;pointer-events:none}
.colour-cell{display:flex;align-items:center;gap:.25rem}
.colour-swatch{width:1rem;height:1rem;border:var(--border);border-radius:2px}
.world-stage{position:relative;width:100%;height:100%;max-width:100%;max-height:100%;aspect-ratio:1/1;overflow:hidden;border:var(--border);border-radius:var(--border-radius);background:var(--bby-colour-black)}
.world-stage .stack{width:100%;height:100%;display:grid;align-items:start;justify-content:start}
.world-stage .stack canvas{grid-area:1/1;image-rendering:pixelated}
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
@media (max-width:720px){.world-layout{flex-direction:column}.world-left{width:100%;flex-basis:auto;height:auto}.vertical-panel{overflow-y:visible}.world-right{width:100%;max-width:none;flex:0 0 auto}}
</style>
