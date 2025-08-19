<!-- CHARIS CAT // bbyWorld — 2025 (Abstract Engine) -->
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
            <label class="section">select a particle stamp:</label>
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
              <span>PARTICLES: {{ livingParticles.length }}</span>
              <span>SPAWNS: {{ stats.spawns }}</span>
              <span>DECAYS: {{ stats.decays }}</span>
              <span>CHARGE AVG: {{ avgCharge.toFixed(2) }}</span>
              <span>FIELD DENSITY: {{ worldFieldDensity.toFixed(0) }}</span>
            </div>
          </div>

          <div class="grp">
            <label class="section">colour groups</label>
            <div class="group-stats">
              <div class="group-row header">
                <span>colour</span>
                <span>count</span>
                <span>%</span>
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
                <span>{{ g.avgCharge.toFixed(1) }}</span>
                <span>{{ g.avgMass.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <div class="grp" v-if="selectedParticle">
            <label class="section">particle {{ selectedParticle.id }} info</label>
            <div class="cell-stats">
              <div class="cell-colour">
                <span
                  class="colour-swatch"
                  :style="{ background: `rgba(${selectedParticle.r},${selectedParticle.g},${selectedParticle.b},${selectedParticle.a/255})` }"
                ></span>
                <span>{{ selectedParticle.r }},{{ selectedParticle.g }},{{ selectedParticle.b }},{{ selectedParticle.a }}</span>
              </div>
              <div>pos: {{ selectedParticle.x.toFixed(2) }}, {{ selectedParticle.y.toFixed(2) }}</div>
              <div>charge: {{ selectedParticle.charge.toFixed(1) }}</div>
              <div>mass: {{ (selectedParticle.a / 255).toFixed(2) }}</div>
              <div>velocity: {{ particleVelocity(selectedParticle).toFixed(2) }}</div>
            </div>
          </div>

          <div class="grp">
            <label class="section">laws of this universe</label>
            <div class="legend">
              <p><strong>Colour as Influence:</strong> Particles broadcast their colour into three abstract fields: Ψ (Red), Λ (Green), and Σ (Blue). Their colour dictates how they influence and are influenced by this field trinity, creating a proto-neural network.</p>
              <p><strong>Motion as Orbit:</strong> The fields do not attract particles directly. Instead, force is applied perpendicular to the energy gradient, causing particles to orbit areas of high influence rather than seek them. All movement is orbital, not linear.</p>
              <p><strong>Life as Resonance:</strong> A particle survives by maintaining its internal Charge. It gains Charge by resonating with the local fields its colour is attuned to. Dissonance bleeds Charge. At zero, it decays, releasing its essence back into the universe.</p>
              <p><strong>Creation from Chaos:</strong> New particles are not born; they precipitate from the fabric of space itself when the local field energy crosses a critical threshold. A new particle's colour is a complex, non-linear signature of the exact universal state at its moment of creation.</p>
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
          <canvas
            ref="gameCanvas"
            :width="boardSize"
            :height="boardSize"
            @click="placeImage"
            :style="canvasStyle"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, onUnmounted, watch } from "vue";
import { bbyUse } from '@/composables/bbyUse.ts';

// --- TIME & FORMATTING ---
const TICKS_PER_DAY = 100;
const DAYS_PER_YEAR = 365;
function formatTicks(ticks: number) {
  const totalDays = Math.floor(ticks / TICKS_PER_DAY);
  const year = Math.floor(totalDays / DAYS_PER_YEAR);
  const day = totalDays % DAYS_PER_YEAR;
  return `Year ${year} Day ${day}`;
}

// --- WORLD & UI STATE ---
const boardSize = ref<number>(128);
function S(){ return boardSize.value; }
const gameCanvas = ref<HTMLCanvasElement | null>(null);
const stageEl = ref<HTMLDivElement | null>(null);
const pan = ref({ x: 0, y: 0 });
const baseScale = ref(1);
const zoomFactor = ref(1);
const ticksPerSecond = ref(30);
const cards = ref<{ label: string; url: string; stamp_url?: string }[]>([]);
const selectedCardLabel = ref<string | null>(null);
let loadedImageData: ImageData | null = null;
const { fetchBbyBookGallery } = bbyUse();

// =======================================================================
// ==================== ABSTRACT PHYSICS & SIMULATION CORE ================
// =======================================================================

// --- The fundamental particle of matter in this universe ---
type Particle = {
  id: number;
  r: number; g: number; b: number; a: number; // The particle's "physical signature"
  x: number; y: number; // Position
  px: number; py: number; // Previous position (for Verlet integration)
  charge: number; // Internal energy, life force
  alive: boolean;
  birthTick: number;
};

// --- World State ---
const livingParticles = ref<Particle[]>([]);
let nextParticleId = 1;
const stats = ref({ spawns: 0, decays: 0 });
let tickCount = ref(0);

// --- The Fabric of the Universe: Three Interacting Abstract Fields ---
let fieldPsi = new Float32Array(0); // Influenced by Red
let fieldLam = new Float32Array(0); // Influenced by Green
let fieldSig = new Float32Array(0); // Influenced by Blue

// --- Renderer buffer ---
let frame = new Uint8ClampedArray(0);
let frameImg: ImageData | null = null;

// --- Physics Constants ---
const WORLD_DRAG = 0.97;
const MAX_CHARGE = 255;
const SPAWN_ENERGY_THRESHOLD = 1.8; // High local field density needed to spawn
const SPAWN_CHANCE = 0.0001;
const METABOLIC_COST = 0.15; // Base cost to exist
const FIELD_DIFFUSION = 0.15;
const FIELD_DECAY = 0.995;
// How fields transform each other - the core of the chaos
// Psi -> Lam, Lam -> Sig, Sig -> Psi
const FIELD_TRANSFORM_RATE = 0.02;

// --- RNG ---
let rng_seed = 1337;
function rand() {
    rng_seed = (rng_seed * 16807 + 1) % 2147483647;
    return (rng_seed - 1) / 2147483646;
}

/* ===================== Init / Resize ===================== */
function allocateWorldArrays(size:number){
  const len = size * size;
  fieldPsi = new Float32Array(len);
  fieldLam = new Float32Array(len);
  fieldSig = new Float32Array(len);

  const ctx = gameCanvas.value?.getContext("2d");
  if (ctx) {
    frameImg = ctx.createImageData(size, size);
    frame = frameImg.data;
  }
}

function clearWorld(){
  livingParticles.value.length = 0;
  fieldPsi.fill(0);
  fieldLam.fill(0);
  fieldSig.fill(0);
  stats.value = { spawns: 0, decays: 0 };
  tickCount.value = 0;
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
  const s = S();
  baseScale.value = Math.max(1, Math.floor(Math.min(stage.clientWidth / s, stage.clientHeight / s)));
}

/* ===================== Main Loop ===================== */
let animationFrameId: number | null = null;
let lastTime = 0;
let timeSinceLastTick = 0;
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

  const tickInterval = 1000 / ticksPerSecond.value;
  let performed = 0;
  while (timeSinceLastTick >= tickInterval && performed < MAX_UPDATES_PER_FRAME) {
    update();
    timeSinceLastTick -= tickInterval;
    performed++;
  }
  if (performed === MAX_UPDATES_PER_FRAME) timeSinceLastTick = 0;

  drawGrid(ctx);
  animationFrameId = requestAnimationFrame(mainLoop);
}

/* ===================== Simulation Update ===================== */
function update() {
  tickCount.value++;
  const s = S();
  const dt = 1.0;

  // --- 1. Particles influence the fields ---
  for (const p of livingParticles.value) {
      if (!p.alive) continue;
      const idx = I(Math.floor(p.x), Math.floor(p.y));
      const influence = (p.a / 255) * 0.1; // Mass determines influence strength
      fieldPsi[idx] += (p.r / 255) * influence;
      fieldLam[idx] += (p.g / 255) * influence;
      fieldSig[idx] += (p.b / 255) * influence;
  }

  // --- 2. Fields diffuse, decay, and chaotically transform each other ---
  diffuseAndTransform(fieldPsi, fieldSig, fieldLam); // Psi is fed by Sig, transforms into Lam
  diffuseAndTransform(fieldLam, fieldPsi, fieldSig); // Lam is fed by Psi, transforms into Sig
  diffuseAndTransform(fieldSig, fieldLam, fieldPsi); // Sig is fed by Lam, transforms into Psi

  // --- 3. Update Particles ---
  for (let i = livingParticles.value.length - 1; i >= 0; i--) {
    const p = livingParticles.value[i];
    if (!p.alive) continue;

    const mass = (p.a / 255) * 2 + 0.1; // Mass adds inertia

    // a) Calculate Force (Perpendicular to gradient)
    const { gx: psi_gx, gy: psi_gy } = getFieldGradient(fieldPsi, p.x, p.y);
    const { gx: lam_gx, gy: lam_gy } = getFieldGradient(fieldLam, p.x, p.y);
    const { gx: sig_gx, gy: sig_gy } = getFieldGradient(fieldSig, p.x, p.y);
    
    const lamForce = (p.g / 255) * 0.5;
    let fx = (-psi_gy) + (lam_gy * lamForce) + (-sig_gy);
    let fy = (psi_gx)  + (-lam_gx * lamForce) + (sig_gx);

    // b) Verlet Integration
    const vx = (p.x - p.px) * WORLD_DRAG;
    const vy = (p.y - p.py) * WORLD_DRAG;
    p.px = p.x; p.py = p.y;
    const ax = fx / mass; const ay = fy / mass;
    p.x += vx + ax * dt * dt;
    p.y += vy + ay * dt * dt;

    // c) Boundary Conditions (Wrap around)
    if (p.x < 0) p.x += s; if (p.x >= s) p.x -= s;
    if (p.y < 0) p.y += s; if (p.y >= s) p.y -= s;

    // d) Energy & Life Cycle (Resonance)
    const idx = I(Math.floor(p.x), Math.floor(p.y));
    const resonance = 
      (fieldPsi[idx] * (p.r / 255)) +
      (fieldLam[idx] * (p.g / 255)) +
      (fieldSig[idx] * (p.b / 255));
    const dissonance = 
      (fieldPsi[idx] * ((255 - p.r) / 255)) +
      (fieldLam[idx] * ((255 - p.g) / 255)) +
      (fieldSig[idx] * ((255 - p.b) / 255));
      
    const chargeDelta = (resonance - dissonance) * 0.5;
    p.charge = Math.min(MAX_CHARGE, p.charge + chargeDelta - METABOLIC_COST);

    if (p.charge <= 0) {
      recordDecay(p);
    }
  }

  // --- 4. Handle Phase Transition Spawning ---
  if (livingParticles.value.length < 2000) { // Cap particles for performance
    const spawnAttempts = Math.floor(s * s * SPAWN_CHANCE);
    for (let i = 0; i < spawnAttempts; i++) {
        const x = Math.floor(rand() * s);
        const y = Math.floor(rand() * s);
        const idx = I(x,y);
        const localEnergy = fieldPsi[idx] + fieldLam[idx] + fieldSig[idx];

        if (localEnergy > SPAWN_ENERGY_THRESHOLD) {
            const newParticle = spawn(x, y, idx);
            livingParticles.value.push(newParticle);
            stats.value.spawns++;
            fieldPsi[idx] *= 0.5; fieldLam[idx] *= 0.5; fieldSig[idx] *= 0.5;
        }
    }
  }

  // Prune dead particles
  const oldLength = livingParticles.value.length;
  livingParticles.value = livingParticles.value.filter(p => p.alive);
  stats.value.decays += oldLength - livingParticles.value.length;
}

function I(x: number, y: number) { const s = S(); return ((x & (s-1)) + (y * s)) >>> 0; }

// --- Abstract Physics Subroutines ---

function diffuseAndTransform(field: Float32Array, feedField: Float32Array, transformField: Float32Array) {
    const s = S();
    const tempField = new Float32Array(field);
    for (let y = 0; y < s; y++) {
        for (let x = 0; x < s; x++) {
            const i = I(x, y);
            const neighbors = (
                tempField[I(x + 1, y)] + tempField[I(x - 1, y)] +
                tempField[I(x, y + 1)] + tempField[I(x, y - 1)]
            ) * 0.25;
            field[i] = (1 - FIELD_DIFFUSION) * tempField[i] + FIELD_DIFFUSION * neighbors;
            field[i] *= FIELD_DECAY;
            field[i] += Math.sin(feedField[i]) * transformField[i] * FIELD_TRANSFORM_RATE;
            field[i] = Math.max(0, field[i]);
        }
    }
}

function getFieldGradient(field: Float32Array, x: number, y: number) {
  const gx = (field[I(Math.floor(x + 1), Math.floor(y))] - field[I(Math.floor(x - 1), Math.floor(y))]) * 0.5;
  const gy = (field[I(Math.floor(x), Math.floor(y + 1))] - field[I(Math.floor(x), Math.floor(y - 1))]) * 0.5;
  return { gx, gy };
}

function spawn(x: number, y: number, fieldIndex: number): Particle {
  const psi = fieldPsi[fieldIndex];
  const lam = fieldLam[fieldIndex];
  const sig = fieldSig[fieldIndex];
  
  const r_raw = Math.floor(Math.abs(Math.sin(psi * 3.14) * 255));
  const g_raw = Math.floor(Math.abs(Math.cos(lam * 3.14) * 255));
  const b_raw = Math.floor(Math.abs(Math.sin(sig * 3.14) * 255));

  const r = r_raw ^ g_raw;
  const g = g_raw ^ b_raw;
  const b = b_raw ^ r;

  const particle: Particle = {
    id: nextParticleId++,
    r, g, b, a: 150 + Math.floor(rand() * 105),
    x, y, px: x, py: y,
    charge: MAX_CHARGE / 2,
    alive: true,
    birthTick: tickCount.value,
  };
  return particle;
}

function recordDecay(p: Particle) {
  if (!p.alive) return;
  p.alive = false;
  const idx = I(Math.floor(p.x), Math.floor(p.y));
  const energy = (p.charge + p.a) / 255;
  fieldPsi[idx] += (p.r / 255) * energy;
  fieldLam[idx] += (p.g / 255) * energy;
  fieldSig[idx] += (p.b / 255) * energy;
}

/* ===================== Drawing ===================== */
function drawGrid(ctx: CanvasRenderingContext2D) {
  if (!frameImg) return;
  ctx.imageSmoothingEnabled = false;
  const s = S();

  for (let y = 0; y < s; y++) {
    for (let x = 0; x < s; x++) {
      const off = (x + y * s) * 4;
      const ii = I(x, y);
      frame[off]     = Math.min(255, fieldPsi[ii] * 50);
      frame[off + 1] = Math.min(255, fieldLam[ii] * 50);
      frame[off + 2] = Math.min(255, fieldSig[ii] * 50);
      frame[off + 3] = 255;
    }
  }

  for (const p of livingParticles.value) {
    if (!p.alive) continue;
    const ix = Math.floor(p.x);
    const iy = Math.floor(p.y);
    if (ix >=0 && ix < s && iy >= 0 && iy < s) {
        const off = (ix + iy * s) * 4;
        frame[off]     = p.r;
        frame[off + 1] = p.g;
        frame[off + 2] = p.b;
        frame[off + 3] = p.a;
    }
  }
  ctx.putImageData(frameImg, 0, 0);
}

// --- UI Functions, Computed Properties, Lifecycle Hooks ---

onMounted(async () => {
  try {
    const gallery = await fetchBbyBookGallery();
    cards.value = gallery.map(card => ({
      label: card.factName,
      url: card.url,
      stamp_url: card.stamp_url,
    }));
    if (cards.value.length > 0) {
      selectCard(cards.value[0].label);
    }
  } catch (error) { console.error("Failed to fetch gallery:", error); }
  applyBoardSize();
  animationFrameId = requestAnimationFrame(mainLoop);
});
onUnmounted(() => { if (animationFrameId) cancelAnimationFrame(animationFrameId); });
watch(boardSize, () => applyBoardSize());
watch(selectedCardLabel, () => loadSelectedImage());

const totalScale = computed(() => Math.max(1, Math.round(baseScale.value * zoomFactor.value)));
const canvasStyle = computed(() => ({
  transform: `translate(${Math.round(pan.value.x)}px, ${Math.round(pan.value.y)}px) scale(${totalScale.value})`,
  transformOrigin: "top left",
}));

function zoomIn() { zoomFactor.value = Math.min(8, zoomFactor.value * 1.25); }
function zoomOut() { zoomFactor.value = Math.max(0.25, zoomFactor.value / 1.25); }
function resetView(){ pan.value = { x: 0, y: 0 }; zoomFactor.value = 1; computeBaseScale(); }

let isPanning = false; let lastPan = { x: 0, y: 0 };
function startPan(e: MouseEvent) { if (e.button !== 1 && e.button !== 2) return; isPanning = true; lastPan = { x: e.clientX, y: e.clientY }; }
function onMouseMove(e: MouseEvent) { if (isPanning) { pan.value.x += e.clientX - lastPan.x; pan.value.y += e.clientY - lastPan.y; lastPan = { x: e.clientX, y: e.clientY }; } }
function endPan() { isPanning = false; }
function onWheelZoom(e: WheelEvent) { e.deltaY < 0 ? zoomIn() : zoomOut(); }
function speedUp() { ticksPerSecond.value = Math.min(240, ticksPerSecond.value + 10); }
function slowDown() { ticksPerSecond.value = Math.max(1, ticksPerSecond.value - 10); }
function selectCard(label: string) { selectedCardLabel.value = label; }

function loadSelectedImage() {
  const selected = cards.value.find(c => c.label === selectedCardLabel.value);
  if (!selected) return;
  const img = new Image();
  img.crossOrigin = "Anonymous";
  img.onload = () => {
    const tempCanvas = document.createElement("canvas");
    const ctx = tempCanvas.getContext("2d", { willReadFrequently: true })!;
    tempCanvas.width = img.width; tempCanvas.height = img.height;
    ctx.drawImage(img, 0, 0);
    loadedImageData = ctx.getImageData(0, 0, img.width, img.height);
  };
  img.src = selected.stamp_url || selected.url;
}

function placeImage(event: MouseEvent) {
    const canvas = gameCanvas.value; if (!canvas || !loadedImageData) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = (event.clientX - rect.left) / totalScale.value + (pan.value.x / totalScale.value * -1);
    const clickY = (event.clientY - rect.top) / totalScale.value + (pan.value.y / totalScale.value * -1);
    const startX = clickX - loadedImageData.width / 2;
    const startY = clickY - loadedImageData.height / 2;

    for (let y = 0; y < loadedImageData.height; y++) {
        for (let x = 0; x < loadedImageData.width; x++) {
            const i = (y * loadedImageData.width + x) * 4;
            const a = loadedImageData.data[i + 3];
            if (a > 50) {
                const p: Particle = {
                    id: nextParticleId++, alive: true, birthTick: tickCount.value,
                    r: loadedImageData.data[i], g: loadedImageData.data[i+1], b: loadedImageData.data[i+2], a,
                    x: startX + x, y: startY + y, px: startX + x, py: startY + y,
                    charge: MAX_CHARGE,
                };
                livingParticles.value.push(p);
            }
        }
    }
}

const elapsedTimeDisplay = computed(() => formatTicks(tickCount.value));
const avgCharge = computed(() => livingParticles.value.length ? livingParticles.value.reduce((acc, p) => acc + p.charge, 0) / livingParticles.value.length : 0);
const worldFieldDensity = computed(() => {
    let total = 0;
    for(let i=0; i<fieldPsi.length; i++) total += fieldPsi[i] + fieldLam[i] + fieldSig[i];
    return total;
});
const selectedParticle = ref<Particle | null>(null);
function particleVelocity(p: Particle): number { const vx = p.x - p.px; const vy = p.y - p.py; return Math.sqrt(vx * vx + vy * vy); }

// --- Group Stats Implementation ---
interface ColourGroupStat {
  colour: string;
  count: number;
  percentage: number;
  avgCharge: number;
  avgMass: number;
}
const GROUP_STEP = 48;
const quant = (v: number) => Math.min(255, Math.round(v / GROUP_STEP) * GROUP_STEP);
function rgbToHex(r: number, g: number, b: number) { return `#${[r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')}`; }
function groupKey(p: Particle) { return rgbToHex(quant(p.r), quant(p.g), quant(p.b)); }

const groupStats = computed<ColourGroupStat[]>(() => {
  const base = { count: 0, totalCharge: 0, totalMass: 0 };
  const groups: Record<string, typeof base> = {};
  for (const p of livingParticles.value) {
    if (!p.alive) continue;
    const key = groupKey(p);
    const g = groups[key] || (groups[key] = { ...base });
    g.count++;
    g.totalCharge += p.charge;
    g.totalMass += p.a / 255;
  }
  const total = livingParticles.value.length;
  return Object.entries(groups).map(([colour, grp]) => ({
    colour,
    count: grp.count,
    percentage: total ? (grp.count / total) * 100 : 0,
    avgCharge: grp.count ? grp.totalCharge / grp.count : 0,
    avgMass: grp.count ? grp.totalMass / grp.count : 0,
  }));
});
const sortedGroupStats = computed(() => [...groupStats.value].sort((a, b) => b.count - a.count));
const highlightedGroup = ref<string | null>(null);
function selectGroup(colour: string) {
  highlightedGroup.value = highlightedGroup.value === colour ? null : colour;
}

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
.group-row{display:grid;grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap:.25rem;position:relative;cursor:pointer; align-items: center;}
.group-row.header{font-weight:700;cursor:default}
.group-row.selected{outline:1px solid var(--accent-colour);}
.group-bar{position:absolute;top:0;left:0;bottom:0;opacity:.2;pointer-events:none}
.colour-cell{display:flex;align-items:center;gap:.25rem}
.colour-swatch{width:1rem;height:1rem;border:var(--border);border-radius:2px; flex-shrink: 0;}
.world-stage{position:relative;width:100%;height:100%;max-width:100%;max-height:100%;aspect-ratio:1/1;overflow:hidden;border:var(--border);border-radius:var(--border-radius);background:var(--bby-colour-black)}
canvas {
  image-rendering:pixelated;
  image-rendering:crisp-edges;
  display:block;
  /* width: 100%;
  height: 100%; */
}
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
@media (max-width:720px){.world-layout{flex-direction:column}.world-left{width:100%;flex-basis:auto;height:auto}.vertical-panel{overflow-y:visible}.world-right{width:100%;max-width:none;flex:0 0 auto}}
</style>