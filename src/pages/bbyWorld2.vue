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

const DYE_RATE = 0.001; // how quickly cells tint terrain
const BALANCE_RATE = 0.005; // environmental pressure toward colour parity

function I(x:number,y:number){ const s=S(); return ((x & (s-1)) + ((y & (s-1)) * s)) >>> 0; }

function colourDominance(v:number, o1:number, o2:number): number {
  // Use the average of the other channels so dominance swings are gentler
  // and no single colour overwhelms the world.
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
  // Treat colours as "mixed" unless one channel clearly dominates. This
  // prevents near-neutral tones (e.g. purples with a slightly higher green
  // value) from inheriting directional physics like the green cells' upward
  // climb, which caused drifting across the board.
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  if (max - min < 10) return null; // no strong dominance
  if (max === r) return 'red';
  if (max === g) return 'green';
  if (max === b) return 'blue';
  return null;
}

function dominantColour(c: GridCell): ColourName {
  return dominantFromRGB(c.r, c.g, c.b);
}

function applyPhysics(c: GridCell, dom: ColourName) {
  // Older physics pushed blue and green cells straight up or down each tick.
  // This ignored the terrain height map and caused tiles to bounce vertically
  // across the board. Now movements are based solely on terrain height so the
  // canvas' vertical dimension no longer influences behaviour.
  const s = S();
  const hereIdx = I(c.x, c.y);
  const hereH = solidGrid[hereIdx];

  if (dom === 'red') {
    const burned = erodeSolid(hereIdx, 0.02);
    if (burned > 0) c.energy = Math.min(260, c.energy + burned * 5);
  } else if (dom === 'green') {
    // Greens prefer higher nearby terrain but shouldn't always drift upward.
    // Check all adjacent tiles and pick one of the higher spots at random.
    const options: [number, number][] = [];
    for (const [dx, dy] of HEADING_VECS) {
      const nx = (c.x + dx + s) % s;
      const ny = (c.y + dy + s) % s;
      const ni = I(nx, ny);
      if (!spatialMap[ni] && solidGrid[ni] > hereH + 0.01) {
        options.push([nx, ny]);
      }
    }
    if (options.length) {
      const [mx, my] = options[(rand() * options.length) | 0];
      performMove(c, mx, my);
    }
  }
}

function applyRules(c: GridCell, dom: ColourName, _domR:number, _domG:number, _domB:number, ii:number){
  if (dom === 'blue') {
    let count = 0;
    for (const [dx, dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
      const n = spatialMap[I((c.x + dx + S()) % S(), (c.y + dy + S()) % S())];
      if (n && n.alive && dominantColour(n) === 'blue') count++;
    }
    if (count >= 2) c.energy = Math.min(260, c.energy + count * 0.2);
  } else if (dom === 'red') {
    for (const [dx, dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
      const nx = (c.x + dx + S()) % S();
      const ny = (c.y + dy + S()) % S();
      const n = spatialMap[I(nx, ny)];
      if (n && n.alive) {
        const nDom = dominantColour(n);
        if (nDom === 'green') {
          n.energy -= 10;
          c.energy = Math.min(260, c.energy + 10);
          if (n.energy <= 0) recordDeath(n, "war");
        } else if (nDom === 'red' && c.energy > n.energy + 5) {
          const transfer = 5;
          c.energy -= transfer;
          n.energy = Math.min(260, n.energy + transfer);
        }
      }
    }
  } else if (dom === 'green') {
    c.energy = Math.min(260, c.energy + moistureField[ii] * 0.02);
  }
}

function applyNorms(c: GridCell, dom: ColourName){
  if (dom === 'green' && c.attached){
    const s = S();
    const ny = (c.y - 1 + s) % s;
    const above = spatialMap[I(c.x, ny)];
    if (above && above.alive && above.rootId === c.rootId && c.energy > 20){
      const transfer = Math.min(5, c.energy - 20);
      c.energy -= transfer;
      above.energy = Math.min(260, above.energy + transfer);
    }
  } else if (dom === 'blue' && c.cargo > 0){
    const [dx, dy] = HEADING_VECS[c.heading];
    const nx = (c.x + dx + S()) % S();
    const ny = (c.y + dy + S()) % S();
    const n = spatialMap[I(nx, ny)];
    if (n && n.alive && dominantColour(n) === 'blue'){
      const gift = Math.min(5, c.cargo);
      c.cargo -= gift;
      n.cargo += gift;
    }
  } else if (dom === 'red') {
    erodeSolid(I(c.x, c.y), 0.01);
  }
}

function attemptAsexual(c: GridCell, dom: ColourName){
  if (dom === 'green' && c.energy > 200 && rand() < 0.002){
    const spot = findEmptyAdjacent(c.x, c.y);
    if (spot){
      const [sx, sy] = spot;
      const kid = makeCell(sx, sy, c.r, c.g, c.b, c.a, c.lifespan);
      livingCells.value.push(kid);
      spatialMap[I(sx, sy)] = livingCells.value[livingCells.value.length - 1];
      familyTree[c.id].children.push(kid.id);
      familyTree[kid.id].parents.push(c.id);
    }
  }
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
  // Reset arrays without creating new ones to avoid extra allocations
  livingCells.value.length = 0;
  spatialMap.fill(null);
  stats.value = { warDeaths:0, babyMerges:0, squishDeaths:0, fadedDeaths:0, totalLifespan:0, deadCount:0 };
  tickCount.value = 0;
  reseedRNG();
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
  // fit entire board into stage using integer scale for crisp pixels
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
  if (!isPaused.value) {
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
        heatField[i]     += Math.min(0.01*solidGrid[i], 0.03); // sunlight bonus on high ground
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
    if (!c.alive) continue;

    updateAttachment(c);
    const dom = dominantColour(c);
    applyPhysics(c, dom);
    const blueGroup = dom === 'blue' ? countAdjacentBlue(c.x, c.y) : 0;

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
    if (c.age > c.lifespan) {
        c.a = Math.max(0, c.a - c.decayRate * 5); // Accelerate fading past lifespan
    } else {
        c.a = Math.max(0, c.a - c.decayRate);
    }

    // pixels that clump lose transparency so massive blobs
    // cannot accumulate without a supporting mechanism. The
    // penalty now ramps up gently so moderately sized groups
    // can persist while very dense clusters still thin out
    // over time.
    let neighbourCount = 0;
    for (let dy = -1; dy <= 1; dy++) {
      for (let dx = -1; dx <= 1; dx++) {
        if (dx === 0 && dy === 0) continue;
        const nx = (c.x + dx + S()) % S();
        const ny = (c.y + dy + S()) % S();
        const n = spatialMap[I(nx, ny)];
        if (n && n.alive) neighbourCount++;
      }
    }
    if (neighbourCount > 3) {
      const excess = neighbourCount - 3;
      const penalty = (excess * excess) * 0.02; // slow, offsetting group detriment
      c.a = Math.max(0, c.a - penalty);
    }

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
    handleField(domB, moistureField, ii);
    handleField(domG, nutrientField, ii);
    if (domG > 0) {
      nutrientField[ii] += 0.004 * Gf * domG;
    } else if (domG < 0) {
      nutrientField[ii] = Math.max(0, nutrientField[ii] - 0.004 * Gf * (-domG));
    }
    // MODIFIED: Red pixels (fire) require nutrient (fuel) to gain energy
    if (domR > 0) {
      const fuel = Math.min(0.015 * Rf * domR, nutrientField[ii]);
      nutrientField[ii] -= fuel;
      gain += fuel * 25; // Fire gets a large energy boost from fuel
      if (fuel === 0) c.energy -= 0.1; // Burn out without fuel
      // NEW: moisture douses fire
      const damp = moistureField[ii];
      if (damp > 0.01) {
        c.energy -= damp * domR * 5;
      }
    } else {
      handleField(domR, heatField, ii); // Non-fire reds behave as before
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

    applyRules(c, dom, domR, domG, domB, ii);
    applyNorms(c, dom);
    attemptAsexual(c, dom);
    c.energy = Math.min(c.energy, 260);

    // Bright cells struggle in low terrain and dim cells shun the dazzling.
    const brightness = (c.r + c.g + c.b) / 3;
    const depth = solidGrid[ii]; // terrain height at this location
    if (brightness > 200 && depth < 1.5) {
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
      const erosion = 0.004 * Bf * Math.abs(domB) * (1 + blueGroup * 0.5);
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
              const push = take * 0.95; // CHANGED: Move 95% of the eroded material
              moveSolid(ni, pi, push);

              const resource = take - push; // The remaining 5% is converted to resources
              if (resource > 0) { // ADDED: Only erode if there's something left
                  erodeSolid(ni, resource);
                  moistureField[ni] += resource * 0.6;
                  nutrientField[ni] += resource * 0.3;
                  heatField[ni]     += resource * 0.1;
              }
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

      // Red cells (fire) consume nearby terrain for energy, leaving ground dry
      if (domR !== 0) {
        const burn = 0.0025 * Rf * Math.abs(domR);
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const nx = (c.x + dx + S()) % S();
            const ny = (c.y + dy + S()) % S();
            const ni = I(nx, ny);
            if (domR > 0) {
              const take = Math.min(burn, solidGrid[ni]);
              if (take > 0) {
                erodeSolid(ni, take);
                moistureField[ni] = Math.max(0, moistureField[ni] - take * 0.5);
                heatField[ni] += take * 0.2;
                c.energy = Math.min(260, c.energy + take * 10);
              }
            } else {
              solidGrid[ni] = Math.min(6, solidGrid[ni] + burn);
              moistureField[ni] = Math.max(0, moistureField[ni] - burn * 0.5);
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

    // Sprout new green tiles outward without a partner
    if (domG > 0 && c.energy > 60 && rand() < domG * 0.02) {
      const spot = findEmptyAdjacent(c.x, c.y);
      if (spot) {
        const [sx, sy] = spot;
        const kid = sproutFrom(c, sx, sy);
        livingCells.value.push(kid);
        spatialMap[I(sx, sy)] = livingCells.value[livingCells.value.length - 1];
      }
    }

    // Blue cells slip toward lower ground or climb high when suppressed
    if (domB !== 0) {
      const head = dominantBlueHeading(c);
      if (head !== null) c.heading = head;
      let target = solidGrid[ii];
      let bx = c.x, by = c.y;
      // Examine all four cardinal neighbours to locate height differences.
      // A copy-paste bug duplicated the left direction and omitted the up
      // check, which weakened blue's downhill attraction.
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

    // NEW: Green (plant) cells siphon energy from adjacent blue (water) cells
    if (domG > 0) {
      for (const [dx, dy] of shareDirs) {
        const nx = (c.x + dx + S()) % S();
        const ny = (c.y + dy + S()) % S();
        const neighbour = spatialMap[I(nx, ny)];
        if (!neighbour || !neighbour.alive) continue;
        const nDomB = colourDominance(neighbour.b/255, neighbour.r/255, neighbour.g/255);
        if (nDomB > 0) {
          const siphon = Math.min(0.05 * domG, neighbour.energy);
          neighbour.energy -= siphon;
          c.energy = Math.min(260, c.energy + siphon);
        }
      }
    }

    // NEW: Fire cells consume nearby green cells for fuel
    if (domR > 0) {
      for (const [dx, dy] of shareDirs) {
        const nx = (c.x + dx + S()) % S();
        const ny = (c.y + dy + S()) % S();
        const neighbour = spatialMap[I(nx, ny)];
        if (!neighbour || !neighbour.alive) continue;
        const nDomG = colourDominance(neighbour.g/255, neighbour.r/255, neighbour.b/255);
        if (nDomG > 0) {
          const burn = Math.min(0.08 * domR, neighbour.energy);
          neighbour.energy -= burn;
          c.energy = Math.min(260, c.energy + burn * 2);
          if (neighbour.energy <= 0) {
            recordDeath(neighbour, "war");
          }
        }
      }
      if (solidGrid[ii] > 0.1) {
        c.attached = true;
        c.rootId = c.id;
        let count = 0;
        for (const o of livingCells.value) {
          if (o.attached && o.rootId === c.id) count++;
        }
        c.energy = Math.min(260, c.energy + count * 0.3);
      }
    }

    // NEW: Animal behaviour: dark and purple cells ferry nutrients and gift energy
    const isAnimal = (c.r + c.g + c.b < 60) || (c.r > 150 && c.b > 150 && c.g < 80);
    if (isAnimal) {
      // Gather nutrients into cargo
      if (c.cargo < 20 && nutrientField[ii] > 0.01) {
        const take = Math.min(0.01, nutrientField[ii]);
        nutrientField[ii] -= take;
        c.cargo += take * 100;
      }
      // Gift cargo to other animals
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

    // NEW: Heavier pixels can roll off high places
    if (c.strength > 0.8 && solidGrid[ii] > 2.5) {
        let bestTarget: [number, number] | null = null;
        let lowestSolid = solidGrid[ii];
        for (const [dx, dy] of shareDirs) {
            const nx = (c.x + dx + S()) % S();
            const ny = (c.y + dy + S()) % S();
            const ni = I(nx, ny);
            if (!spatialMap[ni] && solidGrid[ni] < lowestSolid - 0.5) {
                lowestSolid = solidGrid[ni];
                bestTarget = [nx, ny];
            }
        }
        if (bestTarget && rand() < 0.1) { // 10% chance to roll per tick
            performMove(c, bestTarget[0], bestTarget[1]);
        }
    }

    // MODIFIED: Blue pixels (water) avoid squish death if pooled
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
          c.energy = 1; // Survive another tick if pooled
          continue;
        }
        // Try to flow into an empty space
        const escape = findEmptyAdjacent(c.x, c.y);
        if (escape) {
          const [ex, ey] = escape;
          performMove(c, ex, ey);
          c.energy = 5; // Get a small energy boost for escaping
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
    if (cell && cell.alive) {
      if (cell.attached && cell.rootId !== cell.id) continue;
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
// Lower genetic compatibility threshold to allow more varied pairings
const GENETIC_COMPAT_THRESHOLD = 0.05
// Only start penalising family breeding after many alternative partners exist
const FAMILY_PENALTY_THRESHOLD = 420
// Minimum energy a cell must have (alongside its partner) before reproduction is attempted
const REPRODUCTION_MIN_ENERGY = 69
const BIRTH_FLASH_TICKS = 8
// Cells previously faded extremely slowly which led to a world that would
// quickly fill and then stagnate. Bumping the decay range up causes even
// well-fed cells to lose opacity and expire at a reasonable pace so the
// environment can continually recycle.
const MIN_DECAY_RATE = 0.01
const MAX_DECAY_RATE = 0.5

function randomDecayRate(){
  return MIN_DECAY_RATE + rand() * (MAX_DECAY_RATE - MIN_DECAY_RATE);
}

function makeCell(px:number,py:number,r:number,g:number,b:number,a:number, parentLifespan?: number): GridCell {
  const A = Math.max(VISIBLE_ALPHA, a);
  const dom = dominantFromRGB(r, g, b);
  let strength = (A/255);              // weight 0..1
  let speed = 1 + Math.floor((255 - A) / 85); // lighter pixels hop further
  if (dom === 'green') strength *= 1.2;
  if (dom === 'blue') strength *= 0.8;
  if (dom === 'red')  speed += 1;
  let energy = 60 + strength*140;
  let metabolism = 0.18 + (g/255)*0.20;  // green=hungry growth
  let aggression  = (r/255)*0.9;         // red=fighty
  let fertility   = 0;                   // fertility will grow with age/transparency

  const heading = (Math.floor(rand()*4) as Heading);
  // Inherited lifespan with mutation
  const baseLifespan = parentLifespan || (TICKS_PER_DAY * 10 + rand() * TICKS_PER_DAY * 20);
  const lifespan = (baseLifespan + (rand() - 0.5) * (TICKS_PER_DAY * 5)) * 200;


  const id = nextCellId++;
  const cell: GridCell = {
    id,
    r, g, b, a: A, x: px, y: py, energy, alive: true, birthTick: tickCount.value, age: 0,
    aggression, fertility, metabolism,
    strength, speed,
    heading, turnBias: 0.3 + (1 - strength) * 0.4,
    coop: 0,
    cargo: 0,
    friends: {},
    decayRate: randomDecayRate(),
    lifespan,
    rootId: id,
    attached: false,
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
  lastTime = performance.now();
  timeSinceLastTick = 0;
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

  // Find the cell's most compatible mate and vector toward it
  // but only if the cell has enough energy to prioritise reproduction.
  let bestMate: GridCell | null = null;
  let bestComp = 0;
  if (cell.energy > REPRODUCTION_MIN_ENERGY) {
    for (const other of livingCells.value) {
      if (other.id === cell.id || !other.alive) continue;
      const comp = compatibility(cell, other);
      if (comp > bestComp) {
        bestComp = comp;
        bestMate = other;
      }
    }
  }

  const board = S();
  let mateDx = 0, mateDy = 0, fertFactor = 0;
  if (bestMate && cell.energy > REPRODUCTION_MIN_ENERGY) {
    mateDx = bestMate.x - cell.x;
    mateDy = bestMate.y - cell.y;
    if (mateDx > board / 2) mateDx -= board;
    if (mateDx < -board / 2) mateDx += board;
    if (mateDy > board / 2) mateDy -= board;
    if (mateDy < -board / 2) mateDy += board;
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
    const domR = colourDominance(Rf, Bf, Gf);
    const domB = colourDominance(Bf, Rf, Gf);
    const domG = colourDominance(Gf, Rf, Bf);
    let want = heat*Rf + wet*Bf + nut*Gf + (heat+wet+nut)*0.05;
    // Blue cells are pulled downhill and struggle to climb back up
    const hDiff = solidGrid[i] - solidGrid[I(cell.x, cell.y)];
    if (hDiff > 0) {
      // moving uphill is hard for blues
      want -= hDiff * Bf * domB;
    } else if (hDiff < 0) {
      // strong attraction toward lower terrain
      want += (-hDiff) * Bf * domB * 1.5;
    }
    // MODIFIED: Red cells hunt for fuel and stalk green plants
    if (domR > 0) {
      want += (nut - wet) * domR * 0.5;
      if (hasNearbyGreen(nx, ny, 2)) {
        want += 0.6 * domR;
      }
      want -= wet * domR * 0.7;
    }

    // Stronger cells should be less deterred by solid tiles. Previously the
    // penalty increased with strength, causing fragile cells to push through
    // rock more easily than tough ones. Invert the relationship so that
    // strong cells incur the minimum penalty while weak cells avoid solids.
    let solidPenalty = solidGrid[i] * (1 - cell.strength);
    if (domR > 0) {
      solidPenalty *= 0.1; // red cells ignore height
    }
    // NEW: White/Grey (gas-like) cells are less affected by terrain and seek empty space
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
      const currentH = solidGrid[I(cell.x, cell.y)];
      const nextH = solidGrid[i];
      let bonus = 0;
      if (wet > 0.1 && hasNearbyGreenBlue(nx, ny, 2)) {
        bonus += wet * 0.3 * domG;
      }
      if (nextH > currentH) {
        bonus += (nextH - currentH) * 0.3 * domG;
      }
      if (bonus > 0) {
        score += bonus;
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

    if (domB > 0 && hasNearbyBlue(nx, ny, 2)) {
      const currentH = solidGrid[I(cell.x, cell.y)];
      const nextH = solidGrid[i];
      score += wet * 0.3 * domB;
      if (nextH < currentH) {
        score += (currentH - nextH) * 0.2 * domB;
      }
    }

    // --- Social bias ---
    // Peek at the neighbour in this direction. Compatible neighbours draw
    // cells together while enemies repel, nudging movement toward emergent
    // groups.
    if (neighbour && neighbour.alive) {
      const comp = compatibility(cell, neighbour);
      if (comp > 0.6) {
        score += comp * 0.2;
      } else {
        score -= (1 - comp) * 0.2;
      }
      // NEW: Green cells are drawn toward adjacent blue (water) tiles
      if (domG > 0) {
        const nDomB = colourDominance(neighbour.b/255, neighbour.r/255, neighbour.g/255);
        if (nDomB > 0) {
          score += 0.5 * domG;
        }
      }
    }

    // NEW: White/Grey (gas-like) cells seek empty space
    if (Math.abs(cell.r - cell.g) < 20 && Math.abs(cell.g - cell.b) < 20) {
      const density = neighbourCount(nx, ny);
      score += (1 - density / 8) * 0.3; // Bonus for moving to less dense areas
    }
    // amplify a touch of randomness so groups don't lock into perfect stability
    score += (rand()-0.5)*0.1;

    // Attraction toward strongest compatible mate, scaled by fertility
    if (bestMate && cell.energy > REPRODUCTION_MIN_ENERGY) {
      const currentDist = Math.abs(mateDx) + Math.abs(mateDy);
      let ndx = mateDx - dx;
      let ndy = mateDy - dy;
      if (ndx > board / 2) ndx -= board;
      if (ndx < -board / 2) ndx += board;
      if (ndy > board / 2) ndy -= board;
      if (ndy < -board / 2) ndy += board;
      const newDist = Math.abs(ndx) + Math.abs(ndy);
      if (newDist < currentDist) {
        score += bestComp * fertFactor;
      }
    }

    prefs.push({h: h as Heading, score});
  }
  prefs.sort((a,b)=>b.score - a.score);
  const best = prefs[0];
  const [dx,dy] = HEADING_VECS[best.h];
  return [dx,dy,best.h];
}

function findEmptyAdjacent(x:number,y:number): [number,number] | null {
  // The direction list previously duplicated [-1,0] and omitted [0,-1],
  // meaning the search skipped one of the eight neighbouring tiles. When the
  // only available space for a newborn was directly above the parents, the
  // function incorrectly reported no free spot and reproduction failed.
  // Include all four cardinal directions explicitly.
  const dirs:[number,number][] = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
  shuffleArray(dirs);
  for (const [dx,dy] of dirs) {
    const nx = (x + dx + S()) % S();
    const ny = (y + dy + S()) % S();
    const idx = I(nx, ny);
    if (!spatialMap[idx]) {
      return [nx, ny];
    }
  }
  return null;
}

function updateAttachment(c: GridCell){
  if (!c.attached || c.rootId === c.id) return;
  // Same duplicate-direction bug existed here; ensure all adjacent tiles are
  // checked so detached sprouts don't mistakenly lose their root.
  // Check all eight surrounding tiles. A previous copy/paste error duplicated
  // the left direction and omitted the diagonals which allowed attached cells
  // connected only diagonally to be treated as detached.
  const dirs:[number,number][] = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
  let connected = false;
  for (const [dx,dy] of dirs){
    const nx = (c.x + dx + S()) % S();
    const ny = (c.y + dy + S()) % S();
    const n = spatialMap[I(nx, ny)];
    if (n && n.alive && n.rootId === c.rootId){ connected = true; break; }
  }
  if (!connected){
    c.attached = false;
    c.rootId = c.id;
  }
}

function countOccupiedAdjacent(x:number,y:number): number {
  // Check all eight neighbours; the previous duplication of [-1,0] meant the
  // tile above was ignored.
  const dirs:[number,number][] = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
  let c=0;
  for (const [dx,dy] of dirs){
    const nx=(x+dx+S())%S();
    const ny=(y+dy+S())%S();
    if (spatialMap[I(nx,ny)]) c++;
  }
  return c;
}

function countAdjacentBlue(x:number,y:number): number {
  let c=0;
  for (const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
    const nx=(x+dx+S())%S();
    const ny=(y+dy+S())%S();
    const n=spatialMap[I(nx,ny)];
    if (n && n.alive && dominantColour(n)==='blue') c++;
  }
  return c;
}

function dominantBlueHeading(cell:GridCell): Heading|null {
  const counts=[0,0,0,0];
  for (const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
    const nx=(cell.x+dx+S())%S();
    const ny=(cell.y+dy+S())%S();
    const n=spatialMap[I(nx,ny)];
    if (n && n.alive && dominantColour(n)==='blue') counts[n.heading]++;
  }
  let best=-1, bestCount=0;
  for (let h=0; h<4; h++) if (counts[h]>bestCount){ bestCount=counts[h]; best=h; }
  return bestCount>0 ? best as Heading : null;
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

function hasNearbyGreen(x:number,y:number,dist=2): boolean {
  for (let dy=-dist; dy<=dist; dy++){
    for (let dx=-dist; dx<=dist; dx++){
      if (dx===0 && dy===0) continue;
      const nx=(x+dx+S())%S();
      const ny=(y+dy+S())%S();
      const neighbour = spatialMap[I(nx,ny)];
      if (neighbour && neighbour.alive){
        const nDomG = colourDominance(neighbour.g/255, neighbour.r/255, neighbour.b/255);
        if (nDomG > 0) return true;
      }
    }
  }
  return false;
}

function hasNearbyBlue(x:number,y:number,dist=2): boolean {
  for (let dy=-dist; dy<=dist; dy++){
    for (let dx=-dist; dx<=dist; dx++){
      if (dx===0 && dy===0) continue;
      const nx=(x+dx+S())%S();
      const ny=(y+dy+S())%S();
      const neighbour = spatialMap[I(nx,ny)];
      if (neighbour && neighbour.alive){
        const nDomB = colourDominance(neighbour.b/255, neighbour.r/255, neighbour.g/255);
        if (nDomB > 0) return true;
      }
    }
  }
  return false;
}

function congaMove(start:GridCell, dx:number, dy:number): boolean {
  const heading = start.heading;
  const chain: GridCell[] = [start];
  let cx = start.x;
  let cy = start.y;
  for (let steps = 0; steps < S(); steps++) {
    const nx = (cx + dx + S()) % S();
    const ny = (cy + dy + S()) % S();
    const next = spatialMap[I(nx, ny)];
    if (!next) {
      for (let i = chain.length - 1; i >= 0; i--) {
        const c = chain[i];
        const tx = (c.x + dx + S()) % S();
        const ty = (c.y + dy + S()) % S();
        performMove(c, tx, ty);
      }
      return true;
    }
    if (next.heading === heading && next.alive) {
      chain.push(next);
      cx = nx; cy = ny;
      continue;
    }
    if (next.alive) {
      recordDeath(next, "squish");
      for (let i = chain.length - 1; i >= 0; i--) {
        const c = chain[i];
        const tx = (c.x + dx + S()) % S();
        const ty = (c.y + dy + S()) % S();
        performMove(c, tx, ty);
      }
      return true;
    }
  }
  const last = chain[chain.length - 1];
  recordDeath(last, "squish");
  for (let i = chain.length - 2; i >= 0; i--) {
    const c = chain[i];
    const tx = (c.x + dx + S()) % S();
    const ty = (c.y + dy + S()) % S();
    performMove(c, tx, ty);
  }
  return true;
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
  const domR = colourDominance(Rf, Bf, Gf);
  const heightDiff = targetH - currentH;
  if (domB > 0 && heightDiff > 0.1) {
    if (!hasNearbyBlue(cell.x, cell.y, 1) || heightDiff > 0.6) return false;
    cell.energy -= heightDiff * 0.05;
  }
  if (domB < 0 && heightDiff < -0.1) return false;

  if (targetH > 0 && domR <= 0) {
    // Base drag from traversing solid ground; climbing costs more.
    cell.energy -= targetH * (heightDiff > 0 ? 0.1 : 0.05);

    if (domB > 0) {
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
      if (!target && solidGrid[tIndex] < currentH + 0.2) {
        performMove(cell, newX, newY);
        return true;
      }
    } else if (heightDiff > 0 && domR <= 0) {
      // Height difference determines how likely the cell is to become stuck.
      // Cells can climb terrain only up to a limit set by their strength.
      const climbCap = cell.strength * 3;
      if (heightDiff > climbCap) return false;
      const stuckP = Math.min(0.9, 0.8 * (1 - cell.strength) * (heightDiff / climbCap));
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
    const compVal = compatibility(cell, target);
    // Soften compatibility and fertility scaling to encourage more breeding; double for higher birth rate
    let pCompat = Math.min(1, (0.05 + compVal * 0.35 + (cell.fertility + target.fertility) * 0.05 + coopBoost) * 2);
    if (isCloseFamily(cell, target)) {
      const options = countCompatibleNonFamily(cell);
      if (options > FAMILY_PENALTY_THRESHOLD) {
        pCompat *= FAMILY_PENALTY_THRESHOLD / options;
      }
    }
    const baseWar = (cell.aggression + target.aggression) * 0.35 + (heatField[tIndex] * 0.25);
    const pWar = Math.min(1, Math.max(0, baseWar - coopBoost * 0.5 - pairAff * 0.1));

    // Breed only when both cells have ample energy
    if (
      compVal >= GENETIC_COMPAT_THRESHOLD &&
      pCompat >= pWar &&
      cell.energy > REPRODUCTION_MIN_ENERGY &&
      target.energy > REPRODUCTION_MIN_ENERGY
    ){
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

      // MODIFIED: Strength (weight) is now a factor in combat, making lighter pixels more fragile
      const cellScore = cell.energy * (0.8 + 0.5 * cell.aggression) + (cell.strength * 20) + envBoost;
      const tarScore  = target.energy * (0.8 + 0.5 * target.aggression) + (target.strength * 20) - envBoost;

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
  spatialMap[I(fromX, fromY)] = null;
  moving.x = (toX + s) % s; moving.y = (toY + s) % s;
  spatialMap[I(moving.x, moving.y)] = moving;

  // Move attached sprouts along with their root
  if (moving.rootId === moving.id) {
    const rawDx = (moving.x - fromX + s) % s;
    const rawDy = (moving.y - fromY + s) % s;
    const shiftX = rawDx > s/2 ? rawDx - s : rawDx;
    const shiftY = rawDy > s/2 ? rawDy - s : rawDy;
    for (const c of livingCells.value) {
      if (c.attached && c.rootId === moving.id && c.id !== moving.id) {
        const nx = (c.x + shiftX + s) % s;
        const ny = (c.y + shiftY + s) % s;
        if (!spatialMap[I(nx, ny)]) {
          spatialMap[I(c.x, c.y)] = null;
          c.x = nx; c.y = ny;
          spatialMap[I(nx, ny)] = c;
        } else {
          c.attached = false;
          c.rootId = c.id;
        }
      }
    }
  }
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

// Determine whether two cells are close family (parent/child or siblings)
function isCloseFamily(a: GridCell, b: GridCell): boolean {
  const fa = familyTree[a.id];
  const fb = familyTree[b.id];
  if (!fa || !fb) return false;
  if (fa.parents.includes(b.id) || fa.children.includes(b.id)) return true;
  if (fb.parents.includes(a.id) || fb.children.includes(a.id)) return true;
  if (fa.parents.some(p => fb.parents.includes(p))) return true;
  return false;
}

// Count how many non-family cells are compatible mates for the given cell
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
  // cross-channel complement: blue↔red, red↔green, green↔blue
  const AR=a.r/255, AG=a.g/255, AB=a.b/255;
  const BR=b.r/255, BG=b.g/255, BB=b.b/255;
  const comp = (AR*BB + AG*BR + AB*BG) / 3;
  // normalise distance into [0,1] so compatibility stays bounded
  const dist = Math.hypot(AR-BR, AG-BG, AB-BB) / Math.sqrt(3);
  const satA = colourIntensity(a.r, a.g, a.b);
  const satB = colourIntensity(b.r, b.g, b.b);
  const base = 0.6*comp + 0.4*(1 - dist);
  return base * ((satA + satB) / 2);
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
    // Push away from the mid-point so blended colours stay vibrant instead of greying out
    const drift = diff * (rand()*0.25 + 0.125);
    return Math.min(255, Math.max(0, Math.round(avg + drift + (rand()*mut - mut/2))));
  }

  const babyR = blendChannel(cell.r, target.r, 6);
  const babyG = blendChannel(cell.g, target.g, 6);
  const babyB = blendChannel(cell.b, target.b, 6);
  const babyA = 255;

  const totalE = Math.max(1, cell.energy + target.energy);
  const avgLifespan = (cell.lifespan + target.lifespan) / 2;
  const kid = makeCell(x, y, babyR, babyG, babyB, babyA, avgLifespan);
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

// Sprout a new green cell from a parent without needing a partner.
function sproutFrom(parent: GridCell, x: number, y: number): GridCell {
  const kid = makeCell(x, y, parent.r, parent.g, parent.b, parent.a, parent.lifespan);
  kid.energy = Math.min(parent.energy * 0.5, 240);
  parent.energy *= 0.5;
  kid.aggression = parent.aggression;
  kid.metabolism = parent.metabolism;
  kid.decayRate = parent.decayRate;
  kid.rootId = parent.rootId;
  kid.attached = true;
  familyTree[kid.id].parents = [parent.id];
  familyTree[parent.id].children.push(kid.id);
  adjustAffinity(parent, kid, 3);
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
  const solidAdd = 0.2 + 0.8*cell.strength; // alpha = stronger rock
  solidGrid[i] = Math.min(solidGrid[i] + solidAdd, 6);

  const energy = cell.energy;
  const Rf = cell.r/255, Bf = cell.b/255, Gf = cell.g/255;
  moistureField[i] += energy*(0.01 + 0.02*Bf);
  heatField[i]     += energy*(0.005 + 0.03*Rf);
  nutrientField[i] += energy*(0.01 + 0.04*Gf);

  spatialMap[I(cell.x, cell.y)] = null;
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

  // cross-channel reactions to boost colour interplay
  moistureField[i] = Math.max(0, moistureField[i] - (0.015*Rf)); // red dries
  heatField[i]     = Math.max(0, heatField[i] - (0.012*Bf));     // blue cools
  nutrientField[i] += 0.005*Bf;                                 // water dissolves
  heatField[i]     += 0.003*Gf;                                 // growth warms
  if (cell.cargo > 0) {
    nutrientField[i] += cell.cargo * 0.01; // Deposit cargo back into nutrient field
    cell.cargo = 0;
  }
}

/* ===================== Draw ===================== */
function drawGrid(ctx: CanvasRenderingContext2D) {
  if (!frameImg) return;

  // ensure scaling keeps sharp edges
  ctx.imageSmoothingEnabled = false;

  const skyR = Number(currentColour.r)||0;
  const skyG = Number(currentColour.g)||0;
  const skyB = Number(currentColour.b)||0;

  const SKY_SCALE = 0.03;     // much subtler sky tint
  const FIELD_SCALE = 80;     // dim field glow
  const FLOOR_ALPHA = 0.10;   // ~10% opacity

  const s=S();

  // base + faint field glow; render terrain height
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

      const rock = solidGrid[ii] * 30;
      if (rock > 0) {
        // Add subtle grayscale height similar to bbyWorld1
        r = Math.min(255, r + rock);
        g = Math.min(255, g + rock);
        b = Math.min(255, b + rock);
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

      frame[off  ] = r;
      frame[off+1] = g;
      frame[off+2] = b;
      frame[off+3] = 255; // Solid background
    }
  }

  // cells on top
  for (const c of livingCells.value){
    const off = (c.x + c.y*s)*4;
    frame[off  ] = c.r;
    frame[off+1] = c.g;
    frame[off+2] = c.b;
    frame[off+3] = Math.max(0, Math.min(255, c.a));

    if (highlightedGroup.value && groupKey(c) === highlightedGroup.value) {
      frame[off  ] = Math.min(255, frame[off  ] + 100);
      frame[off+1] = Math.min(255, frame[off+1] + 100);
      frame[off+2] = Math.min(255, frame[off+2] + 100);
    }
    if (selectedCell.value && c.id === selectedCell.value.id) {
      frame[off  ] = 255;
      frame[off+1] = 255;
      frame[off+2] = 0;
    }

    if (c.age < BIRTH_FLASH_TICKS){
      const flash = 1 - c.age / BIRTH_FLASH_TICKS;
      frame[off  ] = Math.min(255, frame[off  ] + flash*200);
      frame[off+1] = Math.min(255, frame[off+1] + flash*200);
      frame[off+2] = Math.min(255, frame[off+2] + flash*200);
    }
  }

  ctx.putImageData(frameImg, 0, 0);
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

  const stageRect = stageEl.value?.getBoundingClientRect();
  if (!stageRect) return;
  const boxX = event.clientX - stageRect.left;
  const boxY = event.clientY - stageRect.top;
  
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