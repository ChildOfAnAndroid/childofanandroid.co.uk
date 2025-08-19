<!-- CHARIS CAT // bbyWorld — 2025 (The Definitive Hybrid Engine) -->
<template>
  <div class="page-container bbyworld-page">
    <div class="world-layout">
      <div class="world-left">
        <div class="vertical-panel">
          <h1 class="page-title">bbyWorld</h1>
          <h2 class="subtitle">The Hybrid Engine</h2>

          <!-- WORLD CONTROLS -->
          <div class="grp">
            <label class="section" for="board-size">board size</label>
            <div class="row3">
              <button class="action" @click="boardSize = Math.max(32, boardSize - 16)">-</button>
              <input id="board-size" type="number" v-model.number="boardSize" min="32" step="16" />
              <button class="action" @click="boardSize = Math.min(1024, boardSize + 16)">+</button>
            </div>
            <small style="opacity:.7">changing size clears the world</small>
          </div>

          <div class="grp">
            <label class="section">world</label>
            <button class="action" @click="clearWorld">clear</button>
          </div>

          <!-- PLACEMENT CONTROLS -->
          <div class="grp">
            <label class="section">select a cell stamp to place:</label>
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

          <!-- ADJUSTABLE FUNCTIONS (NEW) -->
          <div class="grp">
             <label class="section" style="cursor:pointer" @click="showParams = !showParams">
                universe laws {{ showParams ? '▼' : '▶' }}
             </label>
             <div v-show="showParams" class="params-grid">
                <!-- AGGRESSION -->
                <label for="aggressionFactor">Aggression Factor</label>
                <input title="Multiplier for Red channel's contribution to aggression." type="range" id="aggressionFactor" v-model.number="params.aggressionFactor" min="0" max="2" step="0.1" />
                <span>{{ params.aggressionFactor.toFixed(1) }}</span>
                <!-- FERTILITY -->
                <label for="fertilityFactor">Fertility Factor</label>
                <input title="Overall multiplier for a cell's fertility." type="range" id="fertilityFactor" v-model.number="params.fertilityFactor" min="0" max="2" step="0.1" />
                <span>{{ params.fertilityFactor.toFixed(1) }}</span>
                 <!-- OPPOSITE ATTRACTION -->
                <label for="oppositeAttraction">Opposite Attraction</label>
                <input title="How strongly dissimilar colors attract for reproduction." type="range" id="oppositeAttraction" v-model.number="params.oppositeAttraction" min="0" max="2" step="0.1" />
                <span>{{ params.oppositeAttraction.toFixed(1) }}</span>
                <!-- ENERGY TO COMBAT -->
                <label for="energyToCombat">Energy in Combat</label>
                <input title="How much Energy contributes to a cell's combat score." type="range" id="energyToCombat" v-model.number="params.energyToCombat" min="0" max="2" step="0.1" />
                <span>{{ params.energyToCombat.toFixed(1) }}</span>
                <!-- CHARGE TO COMBAT -->
                <label for="chargeToCombat">Charge in Combat</label>
                <input title="How much Charge contributes to a cell's combat score." type="range" id="chargeToCombat" v-model.number="params.chargeToCombat" min="0" max="2" step="0.1" />
                <span>{{ params.chargeToCombat.toFixed(1) }}</span>
             </div>
          </div>

          <!-- STATS -->
          <div class="grp">
            <label class="section">stats</label>
            <div class="world-stats">
              <span>TIME: {{ elapsedTimeDisplay }}</span>
              <span>CELLS: {{ livingCells.length }}</span>
              <span>AVG LIFE: {{ avgLifespan }}</span>
              <span>AVG ENERGY: {{ avgEnergy.toFixed(1) }}</span>
              <span>AVG CHARGE: {{ avgCharge.toFixed(1) }}</span>
              <br>
              <span>--BIRTHS--</span>
              <span>REPRODUCTIONS: {{ stats.reproductions }}</span>
              <br>
              <span>--DEATHS--</span>
              <span>WAR: {{ stats.warDeaths }}</span>
              <span>SQUISH: {{ stats.squishDeaths }}</span>
              <span>FADE (old age): {{ stats.fadedDeaths }}</span>
              <span>STARVATION: {{ stats.starveDeaths }}</span>
              <span>CHARGE DRAIN: {{ stats.chargeDeaths }}</span>
            </div>
          </div>

          <!-- GROUP STATS -->
          <div class="grp">
            <label class="section">colour groups</label>
            <div class="group-stats">
              <div class="group-row header">
                <span>colour</span>
                <span>%</span>
                <span>age</span>
                <span>nrg</span>
                <span>chg</span>
                <span>str</span>
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
                <span>{{ g.percentage.toFixed(1) }}%</span>
                <span>{{ formatTicks(g.avgAge) }}</span>
                <span>{{ g.avgEnergy.toFixed(1) }}</span>
                <span>{{ g.avgCharge.toFixed(1) }}</span>
                <span>{{ g.avgStrength.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- SELECTED CELL INFO -->
          <div class="grp" v-if="selectedCell">
            <label class="section">cell {{ selectedCell.id }} info</label>
            <div class="cell-stats">
              <div class="cell-colour">
                <span class="colour-swatch" :style="{ background: `rgba(${selectedCell.r},${selectedCell.g},${selectedCell.b},${selectedCell.a/255})` }"></span>
                <span>{{ selectedCell.r }},{{ selectedCell.g }},{{ selectedCell.b }},{{ selectedCell.a }}</span>
              </div>
              <div>pos: {{ selectedCell.x }}, {{ selectedCell.y }}</div>
              <div>age: {{ formatTicks(selectedCell.age) }}</div>
              <div>energy: {{ selectedCell.energy.toFixed(1) }}</div>
              <div>charge: {{ selectedCell.charge.toFixed(1) }}</div>
              <div>strength: {{ selectedCell.strength.toFixed(2) }}</div>
              <div>aggression: {{ selectedCell.aggression.toFixed(2) }}</div>
              <div>fertility: {{ selectedCell.fertility.toFixed(2) }}</div>
              <div>metabolism: {{ selectedCell.metabolism.toFixed(2) }}</div>
            </div>
          </div>

          <div class="grp" v-if="selectedCell">
            <label class="section">cell {{ selectedCell.id }} family</label>
            <div class="family-tree">
              <div>
                parents:
                <template v-if="selectedFamily.parents.length">
                  <span v-for="p in selectedFamily.parents" :key="p.id" class="family-link" @click="selectCellById(p.id)">#{{ p.id }}</span>
                </template>
                <span v-else>none</span>
              </div>
              <div>
                children:
                <template v-if="selectedFamily.children.length">
                  <span v-for="c in selectedFamily.children" :key="c.id" class="family-link" @click="selectCellById(c.id)">#{{ c.id }}</span>
                </template>
                <span v-else>none</span>
              </div>
            </div>
          </div>

          <!-- LEGEND -->
          <div class="grp">
            <label class="section" style="cursor:pointer" @click="showLegend = !showLegend">legend {{ showLegend ? '▼' : '▶' }}</label>
            <div class="legend" v-show="showLegend">
              <p><strong>Colour (Genes):</strong> R, G, B values determine behaviour. Red drives aggression and heat interaction. Green fuels metabolism and nutrient processing. Blue governs moisture affinity and psychic field interaction.</p>
              <p><strong>Shade (Strength):</strong> The alpha/opacity value determines a cell's physical strength and mass. Stronger cells are tougher but slower.</p>
              <p><strong>Energy & Charge:</strong> Cells have two life-forces. <strong>Energy</strong> is gained from the environment (heat, nutrients). <strong>Charge</strong> is gained by resonating with the abstract psychic fields (Psi, Lam, Sig).</p>
              <p><strong>Interaction:</strong> When cells meet, their fate depends on a mix of aggression and color compatibility. High compatibility leads to reproduction, creating a new cell. High aggression or low compatibility leads to combat, where the winner absorbs resources from the vanquished.</p>
            </div>
          </div>

          <!-- VIEW CONTROLS -->
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
            <canvas ref="gameCanvas" :width="boardSize" :height="boardSize" @click="handleCanvasClick" :style="canvasStyle" />
            <div v-show="scopeActive" ref="scopeBox" class="zoom-scope">
              <canvas ref="scopeCanvas"></canvas>
              <div class="scope-info">
                <div>{{ hoverInfo.x }},{{ hoverInfo.y }}</div>
                <div>H:{{ hoverInfo.heat.toFixed(2) }} M:{{ hoverInfo.moisture.toFixed(2) }} N:{{ hoverInfo.nutrient.toFixed(2) }}</div>
                <div>Ψ:{{ hoverInfo.psi.toFixed(2) }} Λ:{{ hoverInfo.lam.toFixed(2) }} Σ:{{ hoverInfo.sig.toFixed(2) }}</div>
                <div v-if="hoverInfo.cell">Cell {{ hoverInfo.cell.id }} | E:{{ hoverInfo.cell.energy.toFixed(0) }} | C:{{ hoverInfo.cell.charge.toFixed(0) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, onUnmounted, watch, reactive } from "vue";
import { throttle } from 'lodash';
import { bbyUse } from '@/composables/bbyUse.ts';

// --- TIME & FORMATTING ---
const TICKS_PER_DAY = 100;
const DAYS_PER_YEAR = 365;
function formatTicks(ticks: number) {
  if (ticks < 0) return "---";
  const totalDays = Math.floor(ticks / TICKS_PER_DAY);
  const year = Math.floor(totalDays / DAYS_PER_YEAR);
  const day = totalDays % DAYS_PER_YEAR;
  return `Y${year} D${day}`;
}

// --- WORLD & UI STATE ---
const boardSize = ref<number>(128);
function S(){ return boardSize.value; }
const gameCanvas = ref<HTMLCanvasElement | null>(null);
const stageEl = ref<HTMLDivElement | null>(null);
const scopeCanvas = ref<HTMLCanvasElement | null>(null);
const scopeBox = ref<HTMLDivElement | null>(null);
const scopeActive = ref(false);
const showLegend = ref(true);
const showParams = ref(true);
let lastMouseEvent: MouseEvent | null = null;
const { fetchBbyBookGallery } = bbyUse();
const cards = ref<{ label: string; url: string; stamp_url?: string }[]>([]);
const selectedCardLabel = ref<string | null>(null);
let loadedImageData: ImageData | null = null;

// --- ADJUSTABLE PARAMETERS ---
const params = reactive({
    aggressionFactor: 1.0,
    fertilityFactor: 1.0,
    oppositeAttraction: 1.0,
    energyToCombat: 1.0,
    chargeToCombat: 0.5,
});

// =======================================================================
// ==================== HYBRID SIMULATION CORE ===========================
// =======================================================================

// --- HYBRID CELL TYPE ---
type Cell = {
  id: number;
  r: number; g: number; b: number; a: number;
  x: number; y: number;
  alive: boolean;
  birthTick: number;
  age: number;
  
  // Sim 1 concepts
  energy: number;
  aggression: number;
  fertility: number;
  metabolism: number;
  strength: number; // alpha -> strength
  speed: number;
  
  // Sim 2 concepts
  charge: number;
  
  // Family
  parents: [number, number] | [];
};
type DeathReason = "war" | "squish" | "fade" | "starve" | "charge";

// --- WORLD STATE ---
const livingCells = ref<Cell[]>([]);
let nextCellId = 1;
const cellById: Record<number, Cell> = {};
const familyTree: Record<number, { parents: number[], children: number[] }> = {};
let spatialMap: (Cell | null)[] = [];
let tickCount = ref(0);

const stats = ref({
  reproductions: 0,
  warDeaths: 0,
  squishDeaths: 0,
  fadedDeaths: 0,
  starveDeaths: 0,
  chargeDeaths: 0,
  totalLifespan: 0,
  deadCount: 0,
});

// --- Environmental Fields (Sim 1) ---
let heatField = new Float32Array(0);
let moistureField = new Float32Array(0);
let nutrientField = new Float32Array(0);
let solidGrid = new Float32Array(0);

// --- Abstract Fields (Sim 2) ---
let fieldPsi = new Float32Array(0); // Red
let fieldLam = new Float32Array(0); // Green
let fieldSig = new Float32Array(0); // Blue
let tempField = new Float32Array(0); // for diffusion calculations

// --- Renderer buffer ---
let frame = new Uint8ClampedArray(0);
let frameImg: ImageData | null = null;

// --- RNG ---
let rng_seed = Date.now();
function rand() { rng_seed = (rng_seed * 16807 + 1) % 2147483647; return (rng_seed - 1) / 2147483646; }

// --- CONSTANTS ---
const VISIBLE_ALPHA = 20;
const FERTILITY_ALPHA_MIN = 0.3
const FERTILITY_ALPHA_MAX = 0.9
const FERTILITY_ALPHA_PEAK = 0.7
const MAX_ENERGY = 255;
const MAX_CHARGE = 255;

/* ===================== Init / Resize / UI Functions ===================== */
function I(x: number, y: number): number {
  const s = S();
  return ((x & (s - 1)) + (y & (s - 1)) * s) >>> 0;
}

function allocateWorldArrays(size:number){
  const len = size * size;
  heatField = new Float32Array(len);
  moistureField = new Float32Array(len);
  nutrientField = new Float32Array(len);
  solidGrid = new Float32Array(len);
  
  fieldPsi = new Float32Array(len);
  fieldLam = new Float32Array(len);
  fieldSig = new Float32Array(len);
  tempField = new Float32Array(len);
  
  spatialMap = new Array(len).fill(null);

  const ctx = gameCanvas.value?.getContext("2d", { willReadFrequently: true });
  if (ctx) { 
    frameImg = ctx.createImageData(size, size); 
    frame = frameImg.data;
  }
}

function clearWorld(){
  livingCells.value.length = 0;
  spatialMap.fill(null);
  Object.keys(cellById).forEach(key => delete cellById[Number(key)]);
  Object.keys(familyTree).forEach(key => delete familyTree[Number(key)]);
  
  const len = S() * S();
  for (let i = 0; i < len; i++) {
      heatField[i] = 0; moistureField[i] = 0; nutrientField[i] = 0; solidGrid[i] = 0;
      fieldPsi[i] = rand() * 0.1; fieldLam[i] = rand() * 0.1; fieldSig[i] = rand() * 0.1;
  }

  stats.value = { reproductions: 0, warDeaths: 0, squishDeaths: 0, fadedDeaths: 0, starveDeaths: 0, chargeDeaths: 0, totalLifespan: 0, deadCount: 0 };
  tickCount.value = 0;
  nextCellId = 1;
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

const pan = ref({ x: 0, y: 0 }); const baseScale = ref(1); const zoomFactor = ref(1);
const ticksPerSecond = ref(30);
const totalScale = computed(() => Math.max(1, Math.floor(baseScale.value * zoomFactor.value)));
const canvasStyle = computed(() => ({ 
  transform: `translate(${Math.round(pan.value.x)}px, ${Math.round(pan.value.y)}px) scale(${totalScale.value})`, 
  transformOrigin: "top left",
  willChange: 'transform'
}));
function zoomIn() { zoomFactor.value = Math.min(16, zoomFactor.value * 1.25); }
function zoomOut() { zoomFactor.value = Math.max(0.25, zoomFactor.value / 1.25); }
function resetView(){ pan.value = { x: 0, y: 0 }; zoomFactor.value = 1; computeBaseScale(); }
let isPanning = false; let lastPan = { x: 0, y: 0 };
function startPan(e: MouseEvent) { if (e.button !== 1 && e.button !== 2) return; isPanning = true; lastPan = { x: e.clientX, y: e.clientY }; }
function onMouseMove(e: MouseEvent) { lastMouseEvent = e; if (isPanning) { pan.value.x += e.clientX - lastPan.x; pan.value.y += e.clientY - lastPan.y; lastPan = { x: e.clientX, y: e.clientY }; } }
function endPan() { isPanning = false; }
function onWheelZoom(e: WheelEvent) { e.deltaY < 0 ? zoomIn() : zoomOut(); }
function speedUp() { ticksPerSecond.value = Math.min(240, ticksPerSecond.value + 10); }
function slowDown() { ticksPerSecond.value = Math.max(1, ticksPerSecond.value - 10); }

function computeBaseScale(){
  const stage = stageEl.value;
  if (!stage) return;
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  const s = S();
  if (w <= 0 || h <= 0 || s <= 0) return;
  baseScale.value = Math.max(1, Math.floor(Math.min(w / s, h / s)));
}
/* ===================== Main Loop ===================== */
let animationFrameId: number | null = null;
let lastTime = 0;
let timeSinceLastTick = 0;
const MAX_UPDATES_PER_FRAME = 5;

function mainLoop(timestamp: number) {
  const ctx = gameCanvas.value?.getContext("2d");
  if (!ctx) { animationFrameId = requestAnimationFrame(mainLoop); return; }
  const tickInterval = 1000 / ticksPerSecond.value;
  if(lastTime === 0) lastTime = timestamp;
  const deltaTime = timestamp - lastTime;
  lastTime = timestamp;
  timeSinceLastTick += deltaTime;
  let performed = 0;
  while (timeSinceLastTick >= tickInterval && performed < MAX_UPDATES_PER_FRAME) {
    update();
    timeSinceLastTick -= tickInterval;
    performed++;
  }
  if (performed === MAX_UPDATES_PER_FRAME) timeSinceLastTick = 0;
  drawGrid(ctx);
  if (lastMouseEvent) updateScope(lastMouseEvent);
  animationFrameId = requestAnimationFrame(mainLoop);
}

/* ===================== Simulation Update ===================== */
function diffuse(field: Float32Array, mix: number, decay: number) {
    const s=S();
    for (let y=0;y<s;y++){
      for (let x=0;x<s;x++){
        const i = I(x,y);
        const nn = (field[I(x+1,y)] + field[I(x-1,y)] + field[I(x,y+1)] + field[I(x,y-1)]) * 0.25;
        field[i] = (1-mix)*field[i] + mix*nn;
        field[i] *= decay;
      }
    }
}

function update() {
  tickCount.value++;

  // --- Field Updates ---
  // Environmental fields
  diffuse(heatField, 0.20, 0.996);
  diffuse(moistureField, 0.30, 0.997);
  diffuse(nutrientField, 0.18, 0.996);
  // Abstract fields
  diffuse(fieldPsi, 0.2, 0.99); 
  diffuse(fieldLam, 0.2, 0.99); 
  diffuse(fieldSig, 0.2, 0.99);

  const nextLivingCells = [];
  
  // --- Cell Updates ---
  for (const c of livingCells.value) {
    if (!c.alive) continue;
    c.age++;
    const idx = I(c.x, c.y);

    // --- Energy & Charge Metabolism ---
    c.energy -= c.metabolism + c.aggression * 0.05;
    
    // Gain energy from environment (Sim 1)
    const gainR = Math.min(heatField[idx], c.r/255 * 0.1); heatField[idx] -= gainR;
    const gainG = Math.min(nutrientField[idx], c.g/255 * 0.1); nutrientField[idx] -= gainG;
    const gainB = Math.min(moistureField[idx], c.b/255 * 0.1); moistureField[idx] -= gainB;
    c.energy += (gainR + gainG + gainB) * 20;
    
    // Gain charge from abstract fields (Sim 2)
    const resonance = (fieldPsi[idx]*(c.r/255))+(fieldLam[idx]*(c.g/255))+(fieldSig[idx]*(c.b/255));
    const dissonance = (fieldPsi[idx]*((255-c.r)/255))+(fieldLam[idx]*((255-c.g)/255))+(fieldSig[idx]*((255-c.b)/255));
    c.charge += (resonance - dissonance) * 0.8 - 0.2;
    
    c.energy = Math.min(MAX_ENERGY, Math.max(0, c.energy));
    c.charge = Math.min(MAX_CHARGE, Math.max(0, c.charge));

    // --- Broadcast to Fields ---
    const influence = (c.a / 255) * 0.1;
    fieldPsi[idx] += (c.r / 255) * influence;
    fieldLam[idx] += (c.g / 255) * influence;
    fieldSig[idx] += (c.b / 255) * influence;

    // --- Fading and Death Checks ---
    c.a -= 0.1; // Simple fade over time
    c.strength = c.a / 255;
    
    if (c.a < VISIBLE_ALPHA) { recordDeath(c, "fade"); continue; }
    if (c.energy <= 0) { recordDeath(c, "starve"); continue; }
    if (c.charge <= 0) { recordDeath(c, "charge"); continue; }
    
    // Update fertility based on age and alpha
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
    c.fertility = ageFactor * fertAlpha * params.fertilityFactor;

    nextLivingCells.push(c);
  }
  livingCells.value = nextLivingCells;

  // --- Movement & Interaction Slice ---
  const updatesPerTick = Math.max(1, Math.floor(livingCells.value.length / 50));
  for (let i = 0; i < updatesPerTick; i++) {
    if (livingCells.value.length === 0) break;
    const cellIndex = Math.floor(rand() * livingCells.value.length);
    const c = livingCells.value[cellIndex];
    if (c && c.alive) attemptMove(c);
  }
}

// --- Cell Creation ---
function makeCell(x: number, y: number, r: number, g: number, b: number, a: number, parents: [number, number] | [] = []): Cell {
  const A = Math.max(VISIBLE_ALPHA, a);
  const strength = (A / 255);
  
  const cell: Cell = {
    id: nextCellId++,
    r, g, b, a: A, x, y, alive: true,
    birthTick: tickCount.value, age: 0,
    energy: 100 + strength * 100,
    aggression: (r / 255) * params.aggressionFactor,
    fertility: 0,
    metabolism: 0.1 + (g / 255) * 0.2,
    strength,
    speed: 1 + Math.floor((255 - A) / 85),
    charge: 100,
    parents,
  };

  cellById[cell.id] = cell;
  familyTree[cell.id] = { parents: parents, children: [] };
  if(parents.length > 0) {
      familyTree[parents[0]]?.children.push(cell.id);
      familyTree[parents[1]]?.children.push(cell.id);
  }
  return cell;
}


// --- Movement & Interaction ---
function attemptMove(c: Cell) {
    let bestScore = -Infinity; 
    let bestDx = 0, bestDy = 0;
    const dirs = [[0,1], [0,-1], [1,0], [-1,0], [1,1], [1,-1], [-1,1], [-1,-1]].sort(() => rand() - 0.5);

    for (const [dx, dy] of dirs) {
      const nx = c.x + dx, ny = c.y + dy;
      const nIdx = I(nx, ny);

      const attractionScore = 
          (c.r / 255 * (heatField[nIdx] + fieldPsi[nIdx])) + 
          (c.g / 255 * (nutrientField[nIdx] + fieldLam[nIdx])) + 
          (c.b / 255 * (moistureField[nIdx] + fieldSig[nIdx]));

      const terrainPenalty = solidGrid[nIdx];
      const score = attractionScore - terrainPenalty;

      if (score > bestScore) {
        bestScore = score;
        bestDx = dx;
        bestDy = dy;
      }
    }

    if (bestDx !== 0 || bestDy !== 0) {
      const targetX = (c.x + bestDx + S()) % S();
      const targetY = (c.y + bestDy + S()) % S();
      const targetCell = spatialMap[I(targetX, targetY)];

      if (targetCell === null) {
        spatialMap[I(c.x, c.y)] = null;
        c.x = targetX; c.y = targetY;
        spatialMap[I(targetX, targetY)] = c;
      } else if (targetCell.alive) {
        handleInteraction(c, targetCell);
      }
    }
}

function compatibility(a: Cell, b: Cell) {
  const AR=a.r/255, AG=a.g/255, AB=a.b/255;
  const BR=b.r/255, BG=b.g/255, BB=b.b/255;
  const comp = (AR*BB + AG*BR + AB*BG) / 3; // Cross-channel complement
  const dist = Math.hypot(AR-BR, AG-BG, AB-BB) / Math.sqrt(3);
  return (0.6*comp + 0.4*(1 - dist)) * params.oppositeAttraction;
}

function handleInteraction(attacker: Cell, defender: Cell) {
  const compat = compatibility(attacker, defender);
  const pReproduction = compat * (attacker.fertility + defender.fertility) * 0.5;
  const pWar = (attacker.aggression + defender.aggression) * 0.5 * (1-compat);

  if (pReproduction > pWar && attacker.energy > 50 && defender.energy > 50) {
    const spawnLoc = findEmptyAdjacent(attacker.x, attacker.y);
    if(spawnLoc) {
      // --- Blend parents for child ---
      const totalStrength = attacker.strength + defender.strength || 1;
      const w1 = attacker.strength / totalStrength, w2 = defender.strength / totalStrength;
      const babyR = Math.round(attacker.r * w1 + defender.r * w2 + (rand() * 10 - 5));
      const babyG = Math.round(attacker.g * w1 + defender.g * w2 + (rand() * 10 - 5));
      const babyB = Math.round(attacker.b * w1 + defender.b * w2 + (rand() * 10 - 5));
      const babyA = 255;

      const newCell = makeCell(spawnLoc.x, spawnLoc.y, babyR, babyG, babyB, babyA, [attacker.id, defender.id]);
      livingCells.value.push(newCell);
      spatialMap[I(spawnLoc.x, spawnLoc.y)] = newCell;

      attacker.energy *= 0.6; defender.energy *= 0.6;
      stats.value.reproductions++;
    }
  } else {
    // --- Combat ---
    const attScore = (attacker.energy * params.energyToCombat + attacker.charge * params.chargeToCombat) * attacker.strength * attacker.aggression;
    const defScore = (defender.energy * params.energyToCombat + defender.charge * params.chargeToCombat) * defender.strength * defender.aggression;
    
    if (attScore > defScore) {
      attacker.energy = Math.min(MAX_ENERGY, attacker.energy + defender.energy * 0.5);
      attacker.charge = Math.min(MAX_CHARGE, attacker.charge + defender.charge * 0.5);
      recordDeath(defender, "war");
    } else {
      defender.energy = Math.min(MAX_ENERGY, defender.energy + attacker.energy * 0.5);
      defender.charge = Math.min(MAX_CHARGE, defender.charge + attacker.charge * 0.5);
      recordDeath(attacker, "war");
    }
  }
}

function findEmptyAdjacent(x:number, y:number): {x:number, y:number} | null {
    const dirs = [[0,1], [0,-1], [1,0], [-1,0], [1,1], [-1,-1], [-1,1], [-1,-1]].sort(() => rand() - 0.5);
    for (const [dx, dy] of dirs) {
        const nx = (x + dx + S()) % S();
        const ny = (y + dy + S()) % S();
        if (spatialMap[I(nx, ny)] === null) return {x: nx, y: ny};
    } return null;
}

function recordDeath(c: Cell, reason: DeathReason) {
  if (!c.alive) return; 
  c.alive = false;
  
  const idx = I(c.x, c.y);
  // Release resources back to the world
  nutrientField[idx] += (c.energy / MAX_ENERGY) * 0.5 + (c.g/255) * 0.2;
  heatField[idx] += (c.energy / MAX_ENERGY) * 0.2 + (c.r/255) * 0.2;
  moistureField[idx] += (c.energy / MAX_ENERGY) * 0.2 + (c.b/255) * 0.2;
  solidGrid[idx] = Math.min(6, solidGrid[idx] + c.strength * 0.5);

  spatialMap[idx] = null;

  // Stats
  if(reason === 'war') stats.value.warDeaths++;
  if(reason === 'squish') stats.value.squishDeaths++;
  if(reason === 'fade') stats.value.fadedDeaths++;
  if(reason === 'starve') stats.value.starveDeaths++;
  if(reason === 'charge') stats.value.chargeDeaths++;
  stats.value.deadCount++; 
  stats.value.totalLifespan += c.age;

  const index = livingCells.value.findIndex(cell => cell.id === c.id);
  if (index > -1) livingCells.value.splice(index, 1);
}

/* ===================== Drawing ===================== */
function drawGrid(ctx: CanvasRenderingContext2D) {
  if (!frameImg) return; 
  ctx.imageSmoothingEnabled = false; 
  const s = S();

  for (let y = 0; y < s; y++) { 
    for (let x = 0; x < s; x++) {
      const off = (x + y * s) * 4; 
      const i = I(x, y);
      
      const rock = solidGrid[i] * 30;
      const heat = heatField[i] * 50;
      const nutrient = nutrientField[i] * 50;
      const moisture = moistureField[i] * 50;
      
      frame[off] = Math.min(255, 10 + rock + heat);
      frame[off + 1] = Math.min(255, 10 + rock + nutrient);
      frame[off + 2] = Math.min(255, 10 + rock + moisture);
      frame[off + 3] = 255;
  }}

  for (const c of livingCells.value) {
    if(!c.alive) continue;
    const off = I(c.x, c.y) * 4;
    frame[off] = c.r; 
    frame[off + 1] = c.g; 
    frame[off + 2] = c.b; 
    frame[off + 3] = c.a;
    
    if (highlightedGroup.value && groupKey(c) === highlightedGroup.value) { 
        frame[off]=Math.min(255, c.r+80); 
        frame[off+1]=Math.min(255, c.g+80); 
        frame[off+2]=Math.min(255, c.b+80); 
    }
    if (selectedCell.value && c.id === selectedCell.value.id) { 
        frame[off]=255; frame[off+1]=255; frame[off+2]=0; 
    }
  }
  ctx.putImageData(frameImg, 0, 0);
}


/* ===================== Lifecycle, UI, Computed Properties ===================== */
let resizeObs: ResizeObserver | null = null;
onMounted(async () => {
  try {
    const gallery = await fetchBbyBookGallery();
    cards.value = gallery.map(card => ({ label: card.factName, url: card.url, stamp_url: card.stamp_url }));
    if (cards.value.length > 0) selectCard(cards.value[0].label);
  } catch (error) { console.error("Failed to fetch gallery:", error); }
  applyBoardSize();
  if (stageEl.value) {
    resizeObs = new ResizeObserver(() => computeBaseScale());
    resizeObs.observe(stageEl.value);
  }
  if (scopeCanvas.value) { scopeCanvas.value.width = 256; scopeCanvas.value.height = 256; }
  animationFrameId = requestAnimationFrame(mainLoop);
});

onUnmounted(() => { if (animationFrameId) cancelAnimationFrame(animationFrameId); if (resizeObs && stageEl.value) resizeObs.disconnect(); });
watch(boardSize, () => applyBoardSize());
watch(selectedCardLabel, () => loadSelectedImage());
function selectCard(label: string) { selectedCardLabel.value = label; loadSelectedImage(); }

function loadSelectedImage() {
  const selected = cards.value.find(c => c.label === selectedCardLabel.value);
  if (!selected) return;

  const img = new Image();
  img.crossOrigin = "Anonymous";
  img.src = selected.stamp_url || selected.url;

  img.onload = () => {
    const scale = Math.min(1, 64 / Math.max(img.width, img.height));
    const outW = Math.max(1, Math.floor(img.width * scale));
    const outH = Math.max(1, Math.floor(img.height * scale));

    const tempCanvas = document.createElement("canvas");
    const ctx = tempCanvas.getContext("2d", { willReadFrequently: true })!;
    tempCanvas.width = outW; tempCanvas.height = outH;
    ctx.drawImage(img, 0, 0, outW, outH);
    loadedImageData = ctx.getImageData(0, 0, outW, outH);
  };
  img.onerror = () => { console.error("Failed to load image for stamp:", img.src); loadedImageData = null; }
}

function screenToWorld(event: MouseEvent): {x: number, y: number} | null {
    const canvas = gameCanvas.value;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const scale = canvas.width / rect.width;
    const worldX = Math.floor((event.clientX - rect.left) * scale);
    const worldY = Math.floor((event.clientY - rect.top) * scale);
    return {x: worldX, y: worldY};
}

function handleCanvasClick(event: MouseEvent) {
    const coords = screenToWorld(event);
    if (!coords) return;
    const clickedCell = spatialMap[I(coords.x, coords.y)];
    if (clickedCell && clickedCell.alive) { 
        selectedCell.value = clickedCell; 
    } else { 
        placeImageAt(coords.x, coords.y); 
    }
}

function placeImageAt(worldX: number, worldY: number) {
    if (!loadedImageData) return;
    const startX = worldX - Math.floor(loadedImageData.width / 2); 
    const startY = worldY - Math.floor(loadedImageData.height / 2);
    for (let y = 0; y < loadedImageData.height; y++) { 
        for (let x = 0; x < loadedImageData.width; x++) {
            const i = (y * loadedImageData.width + x) * 4; 
            const a = loadedImageData.data[i + 3];
            if (a > 50) {
                const pX = (startX + x + S()) % S();
                const pY = (startY + y + S()) % S();
                if (!spatialMap[I(pX, pY)]) {
                    const r = loadedImageData.data[i], g = loadedImageData.data[i+1], b = loadedImageData.data[i+2];
                    const newCell = makeCell(pX, pY, r, g, b, a);
                    livingCells.value.push(newCell);
                    spatialMap[I(pX, pY)] = newCell;
                }
            }
    }}
}

// --- COMPUTED PROPERTIES ---
const elapsedTimeDisplay = computed(() => formatTicks(tickCount.value));
const avgLifespan = computed(() => stats.value.deadCount > 0 ? formatTicks(Math.floor(stats.value.totalLifespan / stats.value.deadCount)) : "---");
const avgEnergy = computed(() => livingCells.value.length > 0 ? livingCells.value.reduce((sum, c) => sum + c.energy, 0) / livingCells.value.length : 0);
const avgCharge = computed(() => livingCells.value.length > 0 ? livingCells.value.reduce((sum, c) => sum + c.charge, 0) / livingCells.value.length : 0);

const selectedCell = ref<Cell | null>(null);
function selectCellById(id: number) { const cell = cellById[id]; if (cell && cell.alive) selectedCell.value = cell; }
const selectedFamily = computed(() => {
  if (!selectedCell.value) return { parents: [], children: [] };
  const entry = familyTree[selectedCell.value.id] || { parents: [], children: [] };
  return {
    parents: entry.parents.map(id => cellById[id]).filter(c => c && c.alive),
    children: entry.children.map(id => cellById[id]).filter(c => c && c.alive),
  };
});

interface ColourGroupStat { colour: string; count: number; percentage: number; avgAge: number; avgEnergy: number; avgCharge: number; avgStrength: number; }
const GROUP_STEP = 48; const quant = (v: number) => Math.min(255, Math.round(v / GROUP_STEP) * GROUP_STEP);
function rgbToHex(r: number, g: number, b: number) { return `#${[r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')}`; }
function groupKey(c: Cell) { return rgbToHex(quant(c.r), quant(c.g), quant(c.b)); }
const groupStats = computed<ColourGroupStat[]>(() => {
  const base = { count: 0, totalAge: 0, totalEnergy: 0, totalCharge: 0, totalStrength: 0 };
  const groups: Record<string, typeof base> = {};
  for (const c of livingCells.value) {
    const key = groupKey(c); const g = groups[key] || (groups[key] = { ...base });
    g.count++; g.totalAge += c.age; g.totalEnergy += c.energy; g.totalCharge += c.charge; g.totalStrength += c.strength;
  }
  const total = livingCells.value.length;
  return Object.entries(groups).map(([colour, grp]) => ({ colour, count: grp.count,
    percentage: total ? (grp.count / total) * 100 : 0, avgAge: grp.count ? grp.totalAge / grp.count : 0,
    avgEnergy: grp.count ? grp.totalEnergy / grp.count : 0, avgCharge: grp.count ? grp.totalCharge / grp.count : 0, avgStrength: grp.count ? grp.totalStrength / grp.count : 0,
  }));
});
const sortedGroupStats = computed(() => [...groupStats.value].sort((a, b) => b.count - a.count));
const highlightedGroup = ref<string | null>(null);
function selectGroup(colour: string) { highlightedGroup.value = highlightedGroup.value === colour ? null : colour; }

const hoverInfo = ref({ x: 0, y: 0, heat: 0, moisture: 0, nutrient: 0, psi: 0, lam: 0, sig: 0, cell: null as Cell | null });
const updateScope = throttle((event: MouseEvent) => {
  if (!scopeActive.value) return;
  const scope = scopeCanvas.value, box = scopeBox.value; if (!scope || !box || !frameImg) return;
  const coords = screenToWorld(event); if (!coords) return;
  const hx = coords.x, hy = coords.y;
  const ctx = scope.getContext('2d'); if (!ctx) return;
  const SCOPE_SIZE = 9; const half = Math.floor(SCOPE_SIZE / 2); const pixelSize = scope.width / SCOPE_SIZE; const s = S();
  ctx.imageSmoothingEnabled = false; ctx.clearRect(0, 0, scope.width, scope.height);
  for (let dy = 0; dy < SCOPE_SIZE; dy++) { for (let dx = 0; dx < SCOPE_SIZE; dx++) {
      const sx = hx - half + dx, sy = hy - half + dy; let r = 0, g = 0, b = 0, a = 255;
      if (sx >= 0 && sy >= 0 && sx < s && sy < s) {
        const off = I(sx, sy) * 4; r = frame[off]; g = frame[off + 1]; b = frame[off + 2]; a = frame[off + 3];
      }
      ctx.fillStyle = `rgba(${r},${g},${b},${a/255})`; ctx.fillRect(dx * pixelSize, dy * pixelSize, pixelSize, pixelSize);
  }}
  ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(half * pixelSize, half * pixelSize, pixelSize, pixelSize);
  if (hx >= 0 && hy >= 0 && hx < s && hy < s) {
    const i = I(hx, hy);
    hoverInfo.value = { x: hx, y: hy, heat: heatField[i], moisture: moistureField[i], nutrient: nutrientField[i], psi: fieldPsi[i], lam: fieldLam[i], sig: fieldSig[i], cell: spatialMap[i] || null };
  }
  const stageRect = stageEl.value?.getBoundingClientRect(); if (!stageRect) return;
  const boxX = event.clientX - stageRect.left, boxY = event.clientY - stageRect.top;
  const offsetX = (boxX / stageRect.width < 0.5) ? 20 : -box.offsetWidth - 20;
  const offsetY = (boxY / stageRect.height < 0.5) ? 20 : -box.offsetHeight - 20;
  box.style.left = `${event.clientX + offsetX}px`; box.style.top = `${event.clientY + offsetY}px`;
}, 16);

</script>

<style scoped>
/* THIS CSS IS BASED ON THE FIRST (WORKING) VERSION FOR CORRECT LAYOUT */
.page-container { display:flex; width:100%; height:var(--full-height); box-sizing:border-box; padding:var(--padding); }
.world-layout{display:flex;flex-direction:row;width:100%;height:100%;gap:var(--spacing);overflow:hidden}
.world-left{flex:1 1 320px;min-width:320px;height:100%;display:flex;flex-direction:column}
.world-right{flex:0 1 var(--full-height);display:flex;align-items:center;justify-content:center;height:100%;max-width:var(--full-height);min-width:0;position:relative}
.vertical-panel{position:relative;width:100%;height:100%;overflow-y:auto;padding:var(--padding);background:var(--panel-colour);border:var(--border);border-radius:var(--border-radius);box-shadow:var(--box-shadow);display:flex;flex-direction:column;gap:calc(var(--spacing)*1.1)}
.vertical-panel h1{margin:0;text-align:center;line-height:1.05}
.subtitle { font-size: var(--small-font-size); text-align: center; opacity: 0.7; margin: -0.5rem 0 0.5rem; font-weight: normal; }
.world-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.group-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.group-row{display:grid;grid-template-columns: 2fr 1fr 1.5fr 1fr 1fr 1fr; gap:.25rem;position:relative;cursor:pointer; align-items: center;}
.group-row.header{font-weight:700;cursor:default}
.group-row.selected{outline:1px solid var(--accent-colour);}
.group-bar{position:absolute;top:0;left:0;bottom:0;opacity:.2;pointer-events:none}
.colour-cell{display:flex;align-items:center;gap:.25rem}
.colour-swatch{width:1rem;height:1rem;border:var(--border);border-radius:2px; flex-shrink: 0;}
.world-stage{position:relative;width:100%;height:100%;max-width:100%;max-height:100%;aspect-ratio:1/1;overflow:hidden;border:var(--border);border-radius:var(--border-radius);background:var(--bby-colour-black)}
.stack{width:100%;height:100%;display:grid;align-items:start;justify-content:start}
.stack > * { grid-area: 1 / 1; }
canvas { image-rendering:pixelated; image-rendering:crisp-edges; display:block; }
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
.card-swatch-bar{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;}
.card-swatch{border:var(--border);padding:2px;background:var(--panel-colour);cursor:pointer}
.card-swatch img{width:32px;height:32px;image-rendering:pixelated;display:block}
.card-swatch.selected{border-color:var(--accent-colour);background:var(--accent-hover)}
.cell-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.cell-colour{display:flex;align-items:center;gap:.25rem}
.family-tree{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.family-link{cursor:pointer;margin-right:.25rem;color:var(--accent-colour)}
.family-link:hover{text-decoration:underline}
.params-grid {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 0.5rem;
    align-items: center;
    font-size: var(--small-font-size);
}
.params-grid label { text-align: right; }
.params-grid input[type="range"] { width: 100%; }
@media (max-width:720px){.world-layout{flex-direction:column}.world-left{width:100%;flex-basis:auto;height:auto}.vertical-panel{overflow-y:visible}.world-right{width:100%;max-width:none;flex:0 0 auto}}
</style>