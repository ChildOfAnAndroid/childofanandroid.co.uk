<!-- CHARIS CAT // bbyWorld — 2025 -->
<template>
  <div class="page-container bbyworld-page">
    <div class="world-layout">
      <div class="world-left">
        <div class="vertical-panel">
          <h1 class="page-title">bbyWorld</h1>

          <div class="grp">
            <label class="section" for="board-size">board size</label>
            <select id="board-size" v-model.number="boardSize" @change="applyBoardSize">
              <option :value="128">128 × 128</option>
              <option :value="256">256 × 256</option>
              <option :value="512">512 × 512</option>
            </select>
            <small style="opacity:.7">changing size clears the world</small>
          </div>

          <div class="grp">
            <label class="section" for="card-select">select a bby to place:</label>
            <select id="card-select" v-model="selectedCardLabel" @change="loadSelectedImage">
              <option v-for="card in cards" :value="card.label" :key="card.label">
                {{ card.label }}
              </option>
            </select>
          </div>

          <div class="grp">
            <label class="section">stats</label>
            <div class="world-stats">
              <span>CELLS: {{ livingCells.length }}</span>
              <span>WAR: {{ stats.warDeaths }}</span>
              <span>BBY: {{ stats.babyMerges }}</span>
              <span>SQUISH: {{ stats.squishDeaths }}</span>
              <span>AVG LIFE: {{ avgLifespan }}</span>
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
            <canvas v-show="scopeActive" ref="scopeCanvas" class="zoom-scope" />
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

/* ============== BOARD SIZE (dynamic) ============== */
const boardSize = ref<number>(256);           // 128 / 256 / 512
function S(){ return boardSize.value; }       // size getter everywhere

/* ===================== UI/Viewport ===================== */
const gameCanvas = ref<HTMLCanvasElement | null>(null);
const stageEl = ref<HTMLDivElement | null>(null);
const scopeCanvas = ref<HTMLCanvasElement | null>(null);

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

/* ===================== Cell / World Types ===================== */
type Species = "plasma"|"water"|"plant"|"blend";
type Heading = 0|1|2|3;
const HEADING_VECS: [number,number][] = [[1,0],[-1,0],[0,1],[0,-1]];

type GridCell = {
  r:number; g:number; b:number; a:number;
  x:number; y:number;
  energy:number; alive:boolean; birthTick:number; age:number;
  species: Species;
  aggression:number; fertility:number; metabolism:number;
  strength:number;         // alpha→weight 0..1
  heading: Heading;        // chain direction
  turnBias:number;         // smoothness (smaller = straighter)
};

/* ===================== World State ===================== */
const livingCells = ref<GridCell[]>([]);
const spatialMap = new Map<string, GridCell>();

const stats = ref({
  warDeaths: 0, babyMerges: 0, squishDeaths: 0,
  totalLifespan: 0, deadCount: 0,
});

/* Tick bookkeeping */
let animationFrameId: number | null = null;
let lastTime = 0;
let timeSinceLastTick = 0;
let tickCount = 0;

/* Fields + solids (allocated per size) */
let heatField      = new Float32Array(S()*S());
let moistureField  = new Float32Array(S()*S());
let nutrientField  = new Float32Array(S()*S());
let solidGrid      = new Float32Array(S()*S());

function I(x:number,y:number){ const s=S(); return ((x & (s-1)) + ((y & (s-1)) * s)) >>> 0; }

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
  livingCells.value.splice(0, livingCells.value.length);
  spatialMap.clear();
  stats.value = { warDeaths:0, babyMerges:0, squishDeaths:0, totalLifespan:0, deadCount:0 };
  tickCount = 0;
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
  if (scope) { scope.width = 128; scope.height = 128; }

  animationFrameId = requestAnimationFrame(mainLoop);
});

onUnmounted(() => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  if (resizeObs && stageEl.value) resizeObs.disconnect();
});

watch(boardSize, () => applyBoardSize());

/* ===================== Main Loop ===================== */
function mainLoop(timestamp: number) {
  const ctx = gameCanvas.value?.getContext("2d");
  if (!ctx) { animationFrameId = requestAnimationFrame(mainLoop); return; }

  const deltaTime = timestamp - lastTime;
  lastTime = timestamp;
  timeSinceLastTick += deltaTime;

  while (timeSinceLastTick >= tickInterval.value) {
    update();
    timeSinceLastTick -= tickInterval.value;
  }
  drawGrid(ctx);
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

function worldTick(){
  // Baby colour biases fields *gently*
  const skyR = (Number(currentColour.r)||0)/255 * 0.004;
  const skyG = (Number(currentColour.g)||0)/255 * 0.004;
  const skyB = (Number(currentColour.b)||0)/255 * 0.004;

  const s=S();
  for (let y=0;y<s;y++){
    for (let x=0;x<s;x++){
      const i = I(x,y);
      if (solidGrid[i] > 0){
        nutrientField[i] += Math.min(0.02*solidGrid[i], 0.05);
        heatField[i] *= 0.999;
      }
      heatField[i]     += skyR;
      moistureField[i] += skyB;
      nutrientField[i] += skyG;
    }
  }
  diffuseDecay(heatField,     0.20, 0.996);
  diffuseDecay(moistureField, 0.30, 0.997);
  diffuseDecay(nutrientField, 0.18, 0.996);
}

function update() {
  tickCount++;
  worldTick();

  // metabolism & micro-reactions
  for (const c of livingCells.value){
    c.energy -= c.metabolism;
    c.age += 1;
    if (c.energy <= 0){ recordDeath(c, "squish"); continue; }

    const ii = I(c.x,c.y);
    if (c.species === "water")  heatField[ii] *= 0.985;
    if (c.species === "plasma") nutrientField[ii] = Math.max(0, nutrientField[ii] - 0.008);
    if (c.species === "plant")  nutrientField[ii] += 0.004;
  }

  // move slice
  const updatesPerTick = Math.ceil(livingCells.value.length / 100) || 1;
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

function speciesFromRGB(r:number,g:number,b:number): Species {
  const R = r/255, G = g/255, B = b/255;
  const m = Math.max(R,G,B), sum = R+G+B;
  if (sum === 0) return "blend";
  const close = (a:number,b:number)=> Math.abs(a-b) < 0.12;
  if ((close(R,G)&&R>0.3) || (close(R,B)&&R>0.3) || (close(G,B)&&G>0.3)) return "blend";
  return (m===R?"plasma":m===B?"water":"plant");
}

const ALPHA_MIN = 0.01

function makeCell(px:number,py:number,r:number,g:number,b:number,a:number): GridCell {
  const sp = speciesFromRGB(r,g,b);
  const A = Math.max(ALPHA_MIN, a);
  const strength = (A/255);              // weight 0..1
  let energy = 60 + strength*140;
  let metabolism = 0.18 + (g/255)*0.20;  // green=hungry growth
  let aggression  = (r/255)*0.9;         // red=fighty
  let fertility   = 0.25 + (b/255)*0.5;  // blue=bonding

  if (sp === "plasma")   { energy += 20; metabolism += 0.05; fertility += 0.05; }
  if (sp === "water")    { metabolism -= 0.05; aggression *= 0.5; fertility += 0.1; }
  if (sp === "plant")    { metabolism += 0.08; aggression *= 0.6; }

  const heading = (Math.floor(rand()*4) as Heading);
  return { r,g,b,a, x:px,y:py, energy, alive:true, birthTick:tickCount, age:0,
           species: sp, aggression, fertility, metabolism,
           strength, heading, turnBias: 0.3 + (1 - strength)*0.4 };
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
      if (a > ALPHA_MIN) {
        const newX = startGridX + x;
        const newY = startGridY + y;
        const key = `${newX},${newY}`;
        if (newX>=0 && newX<S() && newY>=0 && newY<S() && !spatialMap.get(key)) {
          const cell = makeCell(newX, newY, pixels[i], pixels[i+1], pixels[i+2], a);
          livingCells.value.push(cell);
          spatialMap.set(key, cell);
        }
      }
    }
  }
}

/* ===================== Movement / Chains ===================== */
function chooseChainDir(cell:GridCell): [number,number,Heading] {
  const prefs: {h:Heading, score:number}[] = [];
  for (let h=0 as Heading; h<4; h=(h+1) as Heading){
    const [dx,dy] = HEADING_VECS[h];
    const nx = (cell.x + dx + S()) % S();
    const ny = (cell.y + dy + S()) % S();
    const i = I(nx,ny);

    const heat = heatField[i], wet = moistureField[i], nut = nutrientField[i];
    let want = 0;
    if (cell.species === "plasma") want =  (+heat*1.2) + (-wet*0.8) + (+nut*0.2);
    else if (cell.species === "water") want = (-heat*0.7) + (+wet*1.2) + (+nut*0.4);
    else if (cell.species === "plant") want = (-heat*0.6) + (+wet*0.8) + (+nut*1.1);
    else                               want = (+heat*0.4) + (+wet*0.6) + (+nut*0.6);

    const solidPenalty = solidGrid[i] * (0.3 + 0.7*cell.strength);
    const same = (h === cell.heading) ? 1 : 0;
    const turnPenalty = (h === cell.heading ? 0 : cell.turnBias);

    let score = want + same*0.15 - turnPenalty - solidPenalty;
    score += (1 - cell.strength) * wet * 0.2;
    score += (rand()-0.5)*0.05;

    prefs.push({h: h as Heading, score});
  }
  prefs.sort((a,b)=>b.score - a.score);
  const best = prefs[0];
  const [dx,dy] = HEADING_VECS[best.h];
  return [dx,dy,best.h];
}

function attemptMove(cell:GridCell, dx:number, dy:number): boolean {
  const newX = (cell.x + dx + S()) % S();
  const newY = (cell.y + dy + S()) % S();
  const key = `${newX},${newY}`;
  const target = spatialMap.get(key);
  const tIndex = I(newX,newY);

  if (solidGrid[tIndex] > 0){
    if (cell.species === "water"){
      const erode = Math.min(solidGrid[tIndex], 0.05 + 0.1*(cell.energy/200));
      solidGrid[tIndex] -= erode;
      moistureField[tIndex] += erode*0.5;

      const px = (newX + dx + S()) % S();
      const py = (newY + dy + S()) % S();
      if (!spatialMap.get(`${px},${py}`)){
        const moved = solidGrid[tIndex]*0.6;
        solidGrid[I(px,py)] += moved;
        solidGrid[tIndex]   -= moved;
      }
      if (!target && solidGrid[tIndex] < 0.2) {
        performMove(cell, newX, newY);
        return true;
      }
    } else {
      const stuckP = Math.min(0.9, (0.2 + 0.6*cell.strength) * Math.min(1, solidGrid[tIndex]/3));
      if (rand() < stuckP) return false;
    }
  }

  if (!target){
    performMove(cell, newX, newY);
    return true;
  }

  if (target.alive){
    const pCompat = Math.min(1, compatibility(cell,target) * 0.8 + (cell.fertility+target.fertility)*0.1);
    const pWar    = Math.min(1, (cell.aggression+target.aggression)*0.35 + (heatField[tIndex]*0.25));

    if (pCompat >= pWar){
      const baby = mergeBaby(cell, target, newX, newY);
      recordDeath(cell, "squish");
      recordDeath(target, "squish");
      livingCells.value.push(baby);
      spatialMap.set(key, baby);
      stats.value.babyMerges++;
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
        cell.energy = Math.min(cell.energy + 20, 260);
        performMove(cell, newX, newY);
        return true;
      } else {
        recordDeath(cell, "war");
        return false;
      }
    }
  }

  return false;
}

function performMove(moving:GridCell, toX:number, toY:number){
  spatialMap.delete(`${moving.x},${moving.y}`);
  moving.x = toX; moving.y = toY;
  spatialMap.set(`${toX},${toY}`, moving);
}

/* ===================== Interactions ===================== */
function pickRandomLivingCell(): GridCell | null {
  if (livingCells.value.length === 0) return null;
  return livingCells.value[Math.floor(rand()*livingCells.value.length)];
}

function compatibility(a:GridCell,b:GridCell){
  // cross-channel complement: blue↔red, red↔green, green↔blue
  const AR=a.r/255, AG=a.g/255, AB=a.b/255;
  const BR=b.r/255, BG=b.g/255, BB=b.b/255;
  const comp = (AR*BB + AG*BR + AB*BG);
  const dist = Math.hypot(AR-BR, AG-BG, AB-BB);
  return 0.6*comp + 0.4*dist;
}

function mergeBaby(cell:GridCell,target:GridCell,x:number,y:number): GridCell {
  const totalE = Math.max(1, cell.energy + target.energy);
  const babyR = Math.min(255, Math.round((cell.r*cell.energy + target.r*target.energy)/totalE + (rand()*6-3)));
  const babyG = Math.min(255, Math.round((cell.g*cell.energy + target.g*target.energy)/totalE + (rand()*6-3)));
  const babyB = Math.min(255, Math.round((cell.b*cell.energy + target.b*target.energy)/totalE + (rand()*6-3)));
  const babyA = Math.min(255, Math.round((cell.a + target.a)/2 + (rand()*20-10)));
  const kid = makeCell(x,y,babyR,babyG,babyB,babyA);
  kid.energy = Math.min(totalE * 0.85, 240);
  kid.aggression += (rand()*0.1-0.05);
  kid.fertility  += (rand()*0.1-0.05);
  kid.metabolism += (rand()*0.04-0.02);
  return kid;
}

function recordDeath(cell: GridCell, reason: "war" | "squish") {
  if (!cell.alive) return;
  cell.alive = false;

  stats.value.totalLifespan += tickCount - cell.birthTick;
  stats.value.deadCount++;
  if (reason === "war") stats.value.warDeaths++;
  if (reason === "squish") stats.value.squishDeaths++;

  const i = I(cell.x, cell.y);
  const solidAdd = 0.2 + 0.8*cell.strength; // alpha = stronger rock
  solidGrid[i] = Math.min(solidGrid[i] + solidAdd, 6);

  const energy = cell.energy;
  moistureField[i] += (cell.species==="water") ? energy*0.02 : 0.01*energy;
  heatField[i]     += (cell.species==="plasma")? energy*0.03 : 0.005*energy;
  nutrientField[i] += (cell.species==="plant") ? energy*0.04 : 0.01*energy;

  spatialMap.delete(`${cell.x},${cell.y}`);
  const index = livingCells.value.findIndex(c => c === cell);
  if (index > -1) livingCells.value.splice(index, 1);
}

function deposit(cell:GridCell){
  const i = I(cell.x, cell.y);
  if (cell.species === "plasma" ) heatField[i]     += 0.12 + 0.08*(cell.energy/200);
  if (cell.species === "water"  ) moistureField[i] += 0.15 + 0.06*(cell.energy/200);
  if (cell.species === "plant"  ) nutrientField[i] += 0.10 + 0.10*(cell.energy/200);
  if (cell.species === "blend"  ) { heatField[i]+=0.05; moistureField[i]+=0.05; nutrientField[i]+=0.05; }
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

      frame[off  ] = r;
      frame[off+1] = g;
      frame[off+2] = b;
      frame[off+3] = 255;
    }
  }

  // cells on top
  for (const c of livingCells.value){
    const off = (c.x + c.y*s)*4;
    frame[off  ] = c.r;
    frame[off+1] = c.g;
    frame[off+2] = c.b;
    frame[off+3] = 255;
  }

  ctx.putImageData(frameImg, 0, 0);
}

/* ===================== Scope ===================== */
const updateScope = throttle((event: MouseEvent) => {
  if (!scopeActive.value) return;
  const canvas = gameCanvas.value;
  const scope = scopeCanvas.value;
  if (!canvas || !scope || !frameImg) return;
  const rect = canvas.getBoundingClientRect();
  const hx = Math.floor((event.clientX - rect.left) * (canvas.width / rect.width));
  const hy = Math.floor((event.clientY - rect.top) * (canvas.height / rect.height));
  const ctx = scope.getContext('2d');
  if (!ctx) return;
  const SCOPE_SIZE = 5;
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
  scope.style.left = `${event.clientX + 20}px`;
  scope.style.top = `${event.clientY + 20}px`;
}, 16);

/* ===================== Derived ===================== */
const avgLifespan = computed(() => {
  return stats.value.deadCount > 0
    ? (stats.value.totalLifespan / stats.value.deadCount).toFixed(1)
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
.world-stage{position:relative;width:100%;height:100%;max-width:100%;max-height:100%;aspect-ratio:1/1;overflow:hidden;border:var(--border);border-radius:var(--border-radius);background:var(--bby-colour-black)}
.world-stage .stack{width:100%;height:100%;display:grid;align-items:start;justify-content:start}
.world-stage .stack canvas:not(.zoom-scope){grid-area:1/1;image-rendering:pixelated}
.zoom-scope{position:fixed;width:128px;height:128px;border:var(--border);border-radius:var(--border-radius);background:var(--bby-colour-black);pointer-events:none;image-rendering:pixelated}
.grp{display:flex;flex-direction:column;gap:.5rem}
.section{font-size:var(--small-font-size);text-align:center;opacity:.85;letter-spacing:.1em;text-transform:uppercase}
.action{display:block;width:100%;padding:.4rem .5rem;transition:all .2s ease-out;text-align:center}
.action.active,.action:active{background:var(--accent-hover);border-color:var(--accent-colour)!important}
.row2{display:grid;grid-template-columns:repeat(2,1fr);gap:.5rem}
.row3{display:grid;grid-template-columns:1fr auto 1fr;gap:.5rem;align-items:center}
.zoom-display{text-align:center;font-size:var(--small-font-size)}
@media (max-width:720px){.world-layout{flex-direction:column}.world-left{width:100%;flex-basis:auto;height:auto}.vertical-panel{overflow-y:visible}.world-right{width:100%;max-width:none;flex:0 0 auto}}
</style>
