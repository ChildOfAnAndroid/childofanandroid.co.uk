<!-- CHARIS CAT // bbyWorld — 2025 (The Definitive Hybrid Engine) -->
<template>
  <div class="page-container bbyworld-page">
    <div class="world-layout">
      <div class="world-left">
        <div class="vertical-panel">
          <h1 class="page-title">bbyWorld</h1>

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

          <div class="grp">
            <label class="section">select a cell stamp:</label>
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
              <span>CELLS: {{ livingCells.filter(c => c.alive).length }}</span>
              <span>SPAWNS: {{ stats.spawns }}</span>
              <span>AVG LIFESPAN: {{ avgLifespan }}</span>
              <br>
              <span>--DECAY REASONS--</span>
              <span>CONFLICT: {{ stats.conflicts }}</span>
              <span>CHARGE DRAIN: {{ stats.chargeDecays }}</span>
              <span>OVERCROWD: {{ stats.overcrowdDecays }}</span>
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
                <span>charge</span>
                <span>mass</span>
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
                <span>{{ g.avgCharge.toFixed(1) }}</span>
                <span>{{ g.avgMass.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <div class="grp" v-if="selectedCell">
            <label class="section">cell {{ selectedCell.id }} info</label>
            <div class="cell-stats">
              <div class="cell-colour">
                <span class="colour-swatch" :style="{ background: `rgba(${selectedCell.r},${selectedCell.g},${selectedCell.b},${selectedCell.a/255})` }"></span>
                <span>{{ selectedCell.r }},{{ selectedCell.g }},${selectedCell.b},${selectedCell.a}</span>
              </div>
              <div>pos: {{ selectedCell.x }}, {{ selectedCell.y }}</div>
              <div>age: {{ formatTicks(selectedCell.age) }}</div>
              <div>charge: {{ selectedCell.charge.toFixed(1) }}</div>
              <div>mass: {{ (selectedCell.a / 255).toFixed(2) }}</div>
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
                <span v-else>none (primordial)</span>
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

          <div class="grp">
            <label class="section">laws of this universe</label>
            <div class="legend">
              <p><strong>colour:</strong> red wants to be on fire, blue wants to be wet, green wants to grow. transparent things are less strong.</p>
              <p><strong>but:</strong> red burns lots of energy, greens need lots of room, blues pool together but slip off heights.</p>
              <p><strong>bbys:</strong> when two cells make un bby, they're a mixture of their parents. the little flashes on screen are them being born!</p>
              <p><strong>jobs:</strong> cells move toward the resources they need on the board.</p>
              <p><strong>stats:</strong> % shows each colour's share of living cells, age and energy track group averages.</p>
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
            <canvas ref="gameCanvas" :width="boardSize" :height="boardSize" @click="handleCanvasClick" :style="canvasStyle" />
            <div v-show="scopeActive" ref="scopeBox" class="zoom-scope">
              <canvas ref="scopeCanvas"></canvas>
              <div class="scope-info">
                <div>{{ hoverInfo.x }},{{ hoverInfo.y }}</div>
                <div>Ψ {{ hoverInfo.psi.toFixed(2) }} Λ {{ hoverInfo.lam.toFixed(2) }} Σ {{ hoverInfo.sig.toFixed(2) }}</div>
                <div>Solid {{ hoverInfo.solid.toFixed(2) }}</div>
                <div v-if="hoverInfo.cell">Cell {{ hoverInfo.cell.id }} | Charge {{ hoverInfo.cell.charge.toFixed(1) }}</div>
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
import { bbyUse } from '@/composables/bbyUse.ts';
import { throttle } from 'lodash';

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
let lastMouseEvent: MouseEvent | null = null;
const { fetchBbyBookGallery } = bbyUse();
const cards = ref<{ label: string; url: string; stamp_url?: string }[]>([]);
const selectedCardLabel = ref<string | null>(null);
let loadedImageData: ImageData | null = null;

// =======================================================================
// ==================== HYBRID PHYSICS & SIMULATION CORE =================
// =======================================================================

type Cell = {
  id: number;
  r: number; g: number; b: number; a: number;
  x: number; y: number;
  charge: number;
  alive: boolean;
  birthTick: number;
  age: number;
  parents: [number, number] | [];
  lastSpawnTick: number;
};
type DeathReason = "conflict" | "charge" | "overcrowd";

const livingCells = ref<Cell[]>([]);
let nextCellId = 1;
const cellById: Record<number, Cell> = {};
const familyTree: Record<number, { parents: number[], children: number[] }> = {};
const stats = ref({ spawns: 0, conflicts: 0, chargeDecays: 0, overcrowdDecays: 0, totalLifespan: 0, deadCount: 0 });
let tickCount = ref(0);
let spatialMap: (Cell | null)[] = [];

// --- The Fabric of the Universe ---
let fieldPsi = new Float32Array(0);
let fieldLam = new Float32Array(0);
let fieldSig = new Float32Array(0);
let tempField = new Float32Array(0);
let solidGrid = new Float32Array(0);

// --- Renderer buffer ---
let frame = new Uint8ClampedArray(0);
let frameImg: ImageData | null = null;

// --- Physics Constants ---
const MAX_CHARGE = 255;
const METABOLIC_COST = 0.2;
const FIELD_DIFFUSION = 0.2;
const FIELD_DECAY = 0.99;
const FIELD_TRANSFORM_RATE = 0.01;
const UPDATES_PER_TICK_DIVISOR = 50;
const SPAWN_COOLDOWN = 50;

// --- RNG & Noise ---
let rng_seed = Date.now();
function rand() { rng_seed = (rng_seed * 16807 + 1) % 2147483647; return (rng_seed - 1) / 2147483646; }
const p: number[] = []; for(let i=0; i<512; i++) p[i] = Math.floor(rand()*256);
const perm = [...p, ...p];
const fade = (t: number) => t * t * t * (t * (t * 6 - 15) + 10);
const lerp = (t: number, a: number, b: number) => a + t * (b - a);
const grad = (hash: number, x: number, y: number) => {
    const h = hash & 15;
    const u = h < 8 ? x : y, v = h < 4 ? y : h === 12 || h === 14 ? x : 0;
    return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
};
function perlinNoise(x: number, y: number) {
    const X = Math.floor(x) & 255, Y = Math.floor(y) & 255;
    x -= Math.floor(x); y -= Math.floor(y);
    const u = fade(x), v = fade(y);
    const A = perm[X] + Y, B = perm[X + 1] + Y;
    return lerp(v, lerp(u, grad(perm[A], x, y), grad(perm[B], x - 1, y)),
                   lerp(u, grad(perm[A + 1], x, y - 1), grad(perm[B + 1], x - 1, y - 1)));
}

/* ===================== Init / Resize / UI Functions (Defined Before Use) ===================== */
function allocateWorldArrays(size:number){
  const len = size * size;
  fieldPsi = new Float32Array(len); fieldLam = new Float32Array(len); fieldSig = new Float32Array(len);
  solidGrid = new Float32Array(len); tempField = new Float32Array(len);
  spatialMap = new Array(len).fill(null);
  const ctx = gameCanvas.value?.getContext("2d", { willReadFrequently: true });
  if (ctx) { frameImg = ctx.createImageData(size, size); frame = frameImg.data; }
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

function clearWorld(){
  livingCells.value.length = 0;
  spatialMap.fill(null);
  Object.keys(cellById).forEach(key => delete cellById[Number(key)]);
  Object.keys(familyTree).forEach(key => delete familyTree[Number(key)]);
  const s = S();
  for (let y = 0; y < s; y++) {
    for (let x = 0; x < s; x++) {
      const i = x + y * s;
      fieldPsi[i] = rand() * 0.1; fieldLam[i] = rand() * 0.1; fieldSig[i] = rand() * 0.1;
      const n = (perlinNoise(x / (s/4), y / (s/4)) + 1) / 2;
      solidGrid[i] = n > 0.6 ? (n - 0.6) * 10 : 0;
    }
  }
  stats.value = { spawns: 0, conflicts: 0, chargeDecays: 0, overcrowdDecays: 0, totalLifespan: 0, deadCount: 0 };
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

/* ===================== Main Loop ===================== */
let animationFrameId: number | null = null;
let lastTime = 0;
let timeSinceLastTick = 0;
const MAX_UPDATES_PER_FRAME = 5;

function mainLoop(timestamp: number) {
  const ctx = gameCanvas.value?.getContext("2d", { willReadFrequently: true });
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
function update() {
  tickCount.value++;
  const aliveCellsThisTick = livingCells.value.filter(c => c.alive);

  for (const c of aliveCellsThisTick) {
    c.age++;
    const idx = I(c.x, c.y); const influence = (c.a / 255) * 0.2;
    fieldPsi[idx] += (c.r / 255) * influence; fieldLam[idx] += (c.g / 255) * influence; fieldSig[idx] += (c.b / 255) * influence;
    const normR = c.r/255, normG = c.g/255, normB = c.b/255;
    if (normR > normG && normR > normB) solidGrid[idx] = Math.min(6, solidGrid[idx] + 0.01 * normR);
    if (normB > normR && normB > normG) solidGrid[idx] = Math.max(0, solidGrid[idx] - 0.01 * normB);
    if (normG > normR && normG > normB && solidGrid[idx] > 0) { const conversion = Math.min(solidGrid[idx], 0.01 * normG); solidGrid[idx] -= conversion; fieldLam[idx] += conversion * 5; }
  }

  diffuseAndTransform(fieldPsi, fieldSig, fieldLam); diffuseAndTransform(fieldLam, fieldPsi, fieldSig); diffuseAndTransform(fieldSig, fieldLam, fieldPsi);
  
  const nextLivingCells = [];
  for (const c of aliveCellsThisTick) {
    const idx = I(c.x, c.y); const resonance = (fieldPsi[idx]*(c.r/255))+(fieldLam[idx]*(c.g/255))+(fieldSig[idx]*(c.b/255));
    const dissonance = (fieldPsi[idx]*((255-c.r)/255))+(fieldLam[idx]*((255-c.g)/255))+(fieldSig[idx]*((255-c.b)/255));
    const chargeDelta = (resonance - dissonance) * 0.8; c.charge = Math.min(MAX_CHARGE, c.charge + chargeDelta - METABOLIC_COST);
    const neighborCount = countAdjacent(c.x, c.y);

    let stillAlive = true;
    if (neighborCount > 4) {
      const crowdPenalty = (neighborCount - 4) * 0.5; c.charge -= crowdPenalty;
      if (c.charge <= 0) {
        recordDecay(c, "overcrowd");
        stillAlive = false;
      }
    }
    if (stillAlive && c.charge <= 0) {
      recordDecay(c, "charge");
      stillAlive = false;
    }

    if(stillAlive) {
      nextLivingCells.push(c);
    }
  }
  livingCells.value = nextLivingCells;

  const updatesPerTick = Math.max(1, Math.floor(livingCells.value.length / UPDATES_PER_TICK_DIVISOR));
  for (let i = 0; i < updatesPerTick; i++) {
    if (livingCells.value.length === 0) break;
    const cellIndex = Math.floor(rand() * livingCells.value.length);
    const c = livingCells.value[cellIndex]; if (c && c.alive) attemptMove(c);
  }
}

function I(x: number, y: number): number {
  const s = S();
  return ((x & (s - 1)) + (y & (s - 1)) * s) >>> 0;
}

// --- Physics & Cell Subroutines ---
function diffuseAndTransform(field: Float32Array, feedField: Float32Array, transformField: Float32Array) {
    const s = S(); tempField.set(field);
    for (let y = 0; y < s; y++) { for (let x = 0; x < s; x++) {
        const i = I(x, y); const neighbors = (tempField[I(x + 1, y)] + tempField[I(x - 1, y)] + tempField[I(x, y + 1)] + tempField[I(x, y - 1)]) * 0.25;
        field[i] = (1 - FIELD_DIFFUSION) * tempField[i] + FIELD_DIFFUSION * neighbors; field[i] *= FIELD_DECAY;
        const transform = Math.sin(feedField[i]) * Math.tanh(transformField[i]) * FIELD_TRANSFORM_RATE;
        if (!isNaN(transform)) field[i] += transform; field[i] = isNaN(field[i]) ? 0 : Math.max(0, field[i]);
    }}
}

// NEW PHYSICS: Replaced orbital motion with direct attraction/repulsion via field resonance.
function attemptMove(c: Cell) {
    let bestScore = -Infinity; 
    let bestDx = 0, bestDy = 0;
    const dirs = [[0,1], [0,-1], [1,0], [-1,0]].sort(() => rand() - 0.5);

    for (const [dx, dy] of dirs) {
      const nx = c.x + dx, ny = c.y + dy;
      const nIdx = I(nx, ny);

      // The "Attraction Score": How much does this cell's color match the field's color at the target?
      const attractionScore = 
          (c.r / 255 * fieldPsi[nIdx]) + 
          (c.g / 255 * fieldLam[nIdx]) + 
          (c.b / 255 * fieldSig[nIdx]);

      const terrainPenalty = solidGrid[nIdx] * 2;
      const score = attractionScore - terrainPenalty;

      if (score > bestScore) {
        bestScore = score;
        bestDx = dx;
        bestDy = dy;
      }
    }

    if (bestDx !== 0 || bestDy !== 0) {
      const targetX = c.x + bestDx, targetY = c.y + bestDy;
      const targetCell = spatialMap[I(targetX, targetY)];

      if (targetCell === null) {
        spatialMap[I(c.x, c.y)] = null;
        c.x = targetX;
        c.y = targetY;
        spatialMap[I(targetX, targetY)] = c;
      } else if (targetCell.alive) {
        handleInteraction(c, targetCell);
      }
    }
}

function handleInteraction(attacker: Cell, defender: Cell) {
  const resonance = 1 - (Math.abs(attacker.r - defender.r) + Math.abs(attacker.g - defender.g) + Math.abs(attacker.b - defender.b)) / (765);
  if (resonance > 0.8 && (attacker.charge + defender.charge) > MAX_CHARGE * 1.5 && tickCount.value > attacker.lastSpawnTick + SPAWN_COOLDOWN && tickCount.value > defender.lastSpawnTick + SPAWN_COOLDOWN) {
    const spawnLoc = findEmptyAdjacent(attacker.x, attacker.y) || findEmptyAdjacent(defender.x, defender.y);
    if (spawnLoc) {
      spawn(spawnLoc.x, spawnLoc.y, { parents: [attacker, defender] });
      attacker.charge *= 0.6; defender.charge *= 0.6;
      attacker.lastSpawnTick = tickCount.value; defender.lastSpawnTick = tickCount.value;
      stats.value.spawns++;
    }
  } else {
    stats.value.conflicts++;
    const attIdx = I(attacker.x, attacker.y), defIdx = I(defender.x, defender.y);
    const attFieldAdv = (fieldPsi[attIdx]*(attacker.r/255))+(fieldLam[attIdx]*(attacker.g/255))+(fieldSig[attIdx]*(attacker.b/255));
    const defFieldAdv = (fieldPsi[defIdx]*(defender.r/255))+(fieldLam[defIdx]*(defender.g/255))+(fieldSig[defIdx]*(defender.b/255));
    const attScore = attacker.charge * (attacker.a / 255) + attFieldAdv; const defScore = defender.charge * (defender.a / 255) + defFieldAdv;
    if (attScore > defScore) {
      attacker.charge = Math.min(MAX_CHARGE, attacker.charge + defender.charge * 0.5); recordDecay(defender, "conflict");
    } else {
      defender.charge = Math.min(MAX_CHARGE, defender.charge + attacker.charge * 0.5); recordDecay(attacker, "conflict");
    }
  }
}

function spawn(x: number, y: number, options: { parents?: [Cell, Cell], color?: {r:number, g:number, b:number, a:number} } = {}): Cell {
  let r, g, b, a; let parents: [number, number] | [] = [];

  if (options.parents) {
    const [p1, p2] = options.parents;
    parents = [p1.id, p2.id];
    const totalCharge = p1.charge + p2.charge || 1;
    const w1 = p1.charge / totalCharge, w2 = p2.charge / totalCharge;

    const blendChannel = (c1: number, c2: number, mut: number) => {
      const avg = c1 * w1 + c2 * w2;
      const diff = c1 - c2;
      const drift = diff * (rand() * 0.25 - 0.125); // Bias away from the middle
      return Math.min(255, Math.max(0, Math.round(avg + drift + (rand() * mut - mut / 2))));
    };

    r = blendChannel(p1.r, p2.r, 6);
    g = blendChannel(p1.g, p2.g, 6);
    b = blendChannel(p1.b, p2.b, 6);
    a = blendChannel(p1.a, p2.a, 4);

  } else if (options.color) {
    ({r, g, b, a} = options.color);
  } else { 
    r = Math.floor(rand()*255); g = Math.floor(rand()*255); b = Math.floor(rand()*255); a = 150 + Math.floor(rand()*105); 
  }

  const wx = (x % S() + S()) % S();
  const wy = (y % S() + S()) % S();
  const newCell: Cell = { id: nextCellId++, r, g, b, a, x: wx, y: wy, parents, charge: MAX_CHARGE * 0.8, alive: true, birthTick: tickCount.value, age: 0, lastSpawnTick: tickCount.value };
  
  livingCells.value.push(newCell); 
  cellById[newCell.id] = newCell; 
  spatialMap[I(wx, wy)] = newCell;
  familyTree[newCell.id] = { parents, children: [] };
  if (options.parents) { 
    const [p1, p2] = options.parents; 
    familyTree[p1.id]?.children.push(newCell.id); 
    familyTree[p2.id]?.children.push(newCell.id); 
  }
  return newCell;
}

function recordDecay(c: Cell, reason: DeathReason) {
  if (!c.alive) return; c.alive = false;
  spatialMap[I(c.x, c.y)] = null;
  const idx = I(c.x, c.y); const energy = (c.charge + c.a) / 255;
  fieldPsi[idx] += (c.r/255)*energy; fieldLam[idx] += (c.g/255)*energy; fieldSig[idx] += (c.b/255)*energy;
  solidGrid[idx] = Math.min(6, solidGrid[idx] + (c.a / 255) * 0.2);
  if(reason === 'conflict') stats.value.conflicts++; if(reason === 'charge') stats.value.chargeDecays++; if(reason === 'overcrowd') stats.value.overcrowdDecays++;
  stats.value.deadCount++; stats.value.totalLifespan += c.age;
}
function findEmptyAdjacent(x:number, y:number): {x:number, y:number} | null {
    const dirs = [[0,1], [0,-1], [1,0], [-1,0]].sort(() => rand() - 0.5);
    for (const [dx, dy] of dirs) {
        const nx = x + dx, ny = y + dy; if (spatialMap[I(nx, ny)] === null) return {x: nx, y: ny};
    } return null;
}
function countAdjacent(x:number, y:number): number {
    let count = 0;
    for (let dy = -1; dy <= 1; dy++) { for (let dx = -1; dx <= 1; dx++) {
        if (dx === 0 && dy === 0) continue; if (spatialMap[I(x + dx, y + dy)]) count++;
    }} return count;
}

/* ===================== Drawing ===================== */
function drawGrid(ctx: CanvasRenderingContext2D) {
  if (!frameImg) return; ctx.imageSmoothingEnabled = false; const s = S();
  for (let y = 0; y < s; y++) { for (let x = 0; x < s; x++) {
      const off = (x + y * s) * 4; const ii = I(x, y); const rock = solidGrid[ii] * 30;
      frame[off] = Math.min(255, 10 + fieldPsi[ii] * 40 + rock);
      frame[off + 1] = Math.min(255, 10 + fieldLam[ii] * 40 + rock);
      frame[off + 2] = Math.min(255, 10 + fieldSig[ii] * 40 + rock);
      frame[off + 3] = 255;
  }}
  const aliveCells = livingCells.value.filter(c => c.alive);
  for (const c of aliveCells) {
    const off = (I(c.x, c.y)) * 4;
    frame[off] = c.r; frame[off + 1] = c.g; frame[off + 2] = c.b; frame[off + 3] = c.a;
    if (highlightedGroup.value && groupKey(c) === highlightedGroup.value) { frame[off]=Math.min(255, c.r+80); frame[off+1]=Math.min(255, c.g+80); frame[off+2]=Math.min(255, c.b+80); }
    if (selectedCell.value && c.id === selectedCell.value.id) { frame[off]=255; frame[off+1]=255; frame[off+2]=0; }
  }
  ctx.putImageData(frameImg, 0, 0);
}

// --- Lifecycle, UI, Computed Properties ---
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
function selectCard(label: string) { selectedCardLabel.value = label; }

// FULLY FIXED: This function now uses the robust, multi-URL-attempt logic from version 1.
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

  img.onerror = () => {
    idx++;
    if (idx < tryUrls.length) {
      img.src = tryUrls[idx];
    }
  };
  img.src = tryUrls[idx];
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
    if (clickedCell && clickedCell.alive) { selectedCell.value = clickedCell; } else { placeImageAt(coords.x, coords.y); }
}

function placeImageAt(worldX: number, worldY: number) {
    if (!loadedImageData) return;
    const startX = worldX - Math.floor(loadedImageData.width / 2); const startY = worldY - Math.floor(loadedImageData.height / 2);
    for (let y = 0; y < loadedImageData.height; y++) { for (let x = 0; x < loadedImageData.width; x++) {
        const i = (y * loadedImageData.width + x) * 4; const a = loadedImageData.data[i + 3];
        if (a > 50) {
            const pX = startX + x, pY = startY + y;
            if (!spatialMap[I(pX, pY)]) {
                const r = loadedImageData.data[i], g = loadedImageData.data[i+1], b = loadedImageData.data[i+2];
                spawn(pX, pY, { color: {r, g, b, a} });
            }
        }
    }}
}
const elapsedTimeDisplay = computed(() => formatTicks(tickCount.value));
const avgLifespan = computed(() => stats.value.deadCount > 0 ? formatTicks(Math.floor(stats.value.totalLifespan / stats.value.deadCount)) : "---");
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
interface ColourGroupStat { colour: string; count: number; percentage: number; avgAge: number; avgCharge: number; avgMass: number; }
const GROUP_STEP = 48; const quant = (v: number) => Math.min(255, Math.round(v / GROUP_STEP) * GROUP_STEP);
function rgbToHex(r: number, g: number, b: number) { return `#${[r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')}`; }
function groupKey(c: Cell) { return rgbToHex(quant(c.r), quant(c.g), quant(c.b)); }
const groupStats = computed<ColourGroupStat[]>(() => {
  const base = { count: 0, totalAge: 0, totalCharge: 0, totalMass: 0 };
  const groups: Record<string, typeof base> = {}; const living = livingCells.value.filter(c => c.alive);
  for (const c of living) {
    const key = groupKey(c); const g = groups[key] || (groups[key] = { ...base });
    g.count++; g.totalAge += c.age; g.totalCharge += c.charge; g.totalMass += c.a / 255;
  }
  const total = living.length;
  return Object.entries(groups).map(([colour, grp]) => ({ colour, count: grp.count,
    percentage: total ? (grp.count / total) * 100 : 0, avgAge: grp.count ? grp.totalAge / grp.count : 0,
    avgCharge: grp.count ? grp.totalCharge / grp.count : 0, avgMass: grp.count ? grp.totalMass / grp.count : 0,
  }));
});
const sortedGroupStats = computed(() => [...groupStats.value].sort((a, b) => b.count - a.count));
const highlightedGroup = ref<string | null>(null);
function selectGroup(colour: string) { highlightedGroup.value = highlightedGroup.value === colour ? null : colour; }
const hoverInfo = ref({ x: 0, y: 0, psi: 0, lam: 0, sig: 0, solid: 0, cell: null as Cell | null });
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
    const ii = I(hx, hy);
    hoverInfo.value = { x: hx, y: hy, psi: fieldPsi[ii], lam: fieldLam[ii], sig: fieldSig[ii], solid: solidGrid[ii], cell: spatialMap[ii] || null };
  }
  const stageRect = stageEl.value?.getBoundingClientRect(); if (!stageRect) return;
  const boxX = event.clientX - stageRect.left, boxY = event.clientY - stageRect.top;
  const offsetX = (boxX / stageRect.width < 0.5) ? 20 : -box.offsetWidth - 20;
  const offsetY = (boxY / stageRect.height < 0.5) ? 20 : -box.offsetHeight - 20;
  box.style.left = `${event.clientX + offsetX}px`; box.style.top = `${event.clientY + offsetY}px`;
}, 16);
</script>

<style scoped>
/* THIS CSS IS NOW BASED ON THE FIRST (WORKING) VERSION FOR CORRECT LAYOUT */
.page-container { display:flex; width:100%; height:var(--full-height); box-sizing:border-box; padding:var(--padding); }
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
.card-swatch-bar{display:flex;flex-wrap:wrap;gap:.5rem}
.card-swatch{border:var(--border);padding:2px;background:var(--panel-colour);cursor:pointer}
.card-swatch img{width:32px;height:32px;image-rendering:pixelated;display:block}
.card-swatch.selected{border-color:var(--accent-colour);background:var(--accent-hover)}
.cell-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.cell-colour{display:flex;align-items:center;gap:.25rem}
.family-tree{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.family-link{cursor:pointer;margin-right:.25rem;color:var(--accent-colour)}
.family-link:hover{text-decoration:underline}
@media (max-width:720px){.world-layout{flex-direction:column}.world-left{width:100%;flex-basis:auto;height:auto}.vertical-panel{overflow-y:visible}.world-right{width:100%;max-width:none;flex:0 0 auto}}
</style>