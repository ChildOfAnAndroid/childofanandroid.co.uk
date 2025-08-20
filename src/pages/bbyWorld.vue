<!-- CHARIS CAT // bbyWorld — THE DEFINITIVE VERSION (2025-08-19)
     Life-sim cellular automaton with RGBA channel coupling + stamp painter.
     • EXACT stamp use: expects 64×64 *.stamp.png from /api/gallery and fetches via /api/gallery/file/<file>
     • Emergent behaviour: per-channel diffusion/decay/nonlinearity, cross-talk, stochasticity, memory (4th dimension), baby-weather field
     • User controls: board size, zoom/pan, tick rate, RGBA params, coupling, noise, memory, presets, export/import, screenshot
     • Painter: choose stamp, rotate/flip, alpha, additive/overwrite, brush mode (single/drag), grid snapping
     • Performance: double-buffered Float32 arrays; single canvas render; requestAnimationFrame drive
-->

<template>
  <div class="bbyworld-page">
    <header class="toolbar">
      <h1 class="title">bbyWorld</h1>

      <div class="row">
        <label>board</label>
        <select v-model.number="boardSize" @change="rebuildWorld">
          <option v-for="s in boardSizeOptions" :key="s" :value="s">{{ s }} × {{ s }}</option>
        </select>

        <label>zoom</label>
        <input type="range" min="0.25" max="8" step="0.01" v-model.number="zoom" @input="requestRender"/>
        <button @click="fitToScreen">fit</button>
        <button @click="resetView">100%</button>

        <label>tick</label>
        <input type="range" min="1" max="240" step="1" v-model.number="ticksPerSecond"/><span class="mono">{{ ticksPerSecond }} Hz</span>

        <button :class="{active: running}" @click="toggleRun">{{ running ? 'pause' : 'run' }}</button>
        <button @click="stepOnce">step</button>
        <button @click="clearWorld">clear</button>
        <button @click="randomizeWorld">random</button>

        <button @click="saveScreenshot">screenshot</button>
      </div>
    </header>

    <section class="main">
      <div class="left">
        <div class="canvas-wrap"
             @mousedown="onPointerDown"
             @mousemove="onPointerMove"
             @mouseup="onPointerUp"
             @mouseleave="onPointerUp"
             @wheel.prevent="onWheel"
             ref="canvasWrap">
          <canvas ref="canvas" />
          <div class="hud">
            <span>FPS {{ fps.toFixed(0) }}</span>
            <span>⟂ {{ worldWidth }}×{{ worldHeight }}</span>
            <span>zoom {{ zoom.toFixed(2) }}×</span>
            <span v-if="selectedStamp">stamp {{ selectedStamp.label }} (64×64)</span>
          </div>
        </div>

        <details class="presets">
          <summary>presets</summary>
          <div class="row">
            <input v-model="presetName" placeholder="name your preset"/>
            <button @click="savePreset">save</button>
            <select v-model="selectedPreset">
              <option disabled value="">load…</option>
              <option v-for="p in presetKeys" :key="p" :value="p">{{ p }}</option>
            </select>
            <button :disabled="!selectedPreset" @click="loadPreset">load</button>
            <button :disabled="!selectedPreset" @click="deletePreset">delete</button>
            <button @click="exportPreset">export</button>
            <label class="import">
              import <input type="file" accept="application/json" @change="importPreset"/>
            </label>
          </div>
        </details>
      </div>

      <div class="right">
        <div class="panel">
          <h3>stamps (64×64)</h3>
          <div class="row">
            <button @click="refreshStamps">refresh</button>
            <label><input type="checkbox" v-model="showStampGrid"/> grid</label>
            <label>alpha <input type="range" min="0" max="1" step="0.01" v-model.number="paintAlpha"/></label>
          </div>

          <div class="row">
            <label>mode</label>
            <select v-model="paintMode">
              <option value="add">add</option>
              <option value="overwrite">overwrite</option>
              <option value="subtract">subtract</option>
              <option value="multiply">multiply</option>
            </select>
            <label>channel</label>
            <select v-model="paintChannel">
              <option value="rgba">RGBA</option>
              <option value="r">R</option>
              <option value="g">G</option>
              <option value="b">B</option>
              <option value="a">A</option>
            </select>
          </div>

          <div class="row">
            <label>rotate</label>
            <button @click="rotLeft">⟲</button>
            <button @click="rotRight">⟳</button>
            <label><input type="checkbox" v-model="flipX"/> flipX</label>
            <label><input type="checkbox" v-model="flipY"/> flipY</label>
            <label><input type="checkbox" v-model="snapToGrid"/> snap</label>
          </div>

          <div class="stamp-list">
            <button
              v-for="s in stamps"
              :key="s.file"
              :class="['stamp', {sel: selectedStamp && selectedStamp.file === s.file}]"
              @click="selectStamp(s)"
            >
              <img :src="s.url" :alt="s.label" />
              <div class="meta">
                <div class="lab">{{ s.label || 'unnamed' }}</div>
                <div class="sub">{{ s.author || 'unknown' }}</div>
              </div>
            </button>
            <div v-if="!stamps.length" class="empty">no *.stamp.png found</div>
          </div>
        </div>

        <div class="panel">
          <h3>emergence — RGBA engine</h3>

          <fieldset>
            <legend>per-channel dynamics</legend>
            <div class="grid2">
              <div v-for="ch in CHS" :key="ch" class="col">
                <h4>{{ ch }}</h4>
                <label>diffuse
                  <input type="range" min="0" max="1" step="0.001" v-model.number="params[ch].diffuse"/>
                </label>
                <label>decay
                  <input type="range" min="0" max="1" step="0.001" v-model.number="params[ch].decay"/>
                </label>
                <label>nonlinearity
                  <input type="range" min="0" max="20" step="0.1" v-model.number="params[ch].nonlin"/>
                </label>
                <label>threshold
                  <input type="range" min="-1" max="2" step="0.001" v-model.number="params[ch].thresh"/>
                </label>
                <label>noise
                  <input type="range" min="0" max="0.5" step="0.001" v-model.number="params[ch].noise"/>
                </label>
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend>cross-talk (R,G,B only)</legend>
            <div class="matrix">
              <div class="mrow header">
                <span></span><span>←R</span><span>←G</span><span>←B</span>
              </div>
              <div v-for="row in RGB" :key="row" class="mrow">
                <span class="rowlab">{{ row }}</span>
                <input v-for="col in RGB"
                       :key="row+col"
                       type="range" min="-2" max="2" step="0.01"
                       v-model.number="crosstalk[row][col]"/>
              </div>
              <div class="hint">row receives from column (A modulates update rate)</div>
            </div>
          </fieldset>

          <fieldset>
            <legend>memory & weather (4th dimension)</legend>
            <label>memory mix
              <input type="range" min="0" max="1" step="0.001" v-model.number="memoryMix"/>
            </label>
            <label>weather strength
              <input type="range" min="0" max="1" step="0.001" v-model.number="weatherStrength"/>
            </label>
            <div class="row">
              <label><input type="checkbox" v-model="weatherEnabled"/> baby weather</label>
              <button @click="nudgeWeather">nudge</button>
            </div>
          </fieldset>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
// ————— utilities
const clamp01 = (x:number)=> x<0?0:(x>1?1:x);
const lerp = (a:number,b:number,t:number)=> a+(b-a)*t;

import { onMounted, onBeforeUnmount, reactive, ref, computed, nextTick } from 'vue';

// Strongly-typed channel sets for templates
const CHS = ['R','G','B','A'] as const;
type Ch = typeof CHS[number];
const RGB = ['R','G','B'] as const;
type RGBCh = typeof RGB[number];

const boardSizeOptions = [256, 384, 512, 768]; // you wanted selectable board size
const boardSize = ref<number>(512);

const canvas = ref<HTMLCanvasElement|null>(null);
const canvasWrap = ref<HTMLDivElement|null>(null);
const ctx = ref<CanvasRenderingContext2D|null>(null);

// view / camera
const zoom = ref<number>(1);
const camX = ref<number>(0);
const camY = ref<number>(0);

// sim
const ticksPerSecond = ref<number>(60);
const running = ref<boolean>(true);
const fps = ref<number>(0);

let rafId = 0;
let lastTickMs = 0;
let frameCounter = 0;
let frameTimeAcc = 0;

// world buffers (double)
let worldW = 0, worldH = 0;
let bufA: Float32Array; // current
let bufB: Float32Array; // next
let memBuf: Float32Array; // EMA memory (4D)
const worldWRef = ref<number>(0);
const worldHRef = ref<number>(0);
Object.defineProperty(window, 'bbydbg', { value: { get buf(){return bufA}, get W(){return worldW}, get H(){return worldH} }, writable: false });

// per-channel params
type Params = { [k in Ch]: { diffuse:number, decay:number, nonlin:number, thresh:number, noise:number } };

const params = reactive<Params>({
  R: { diffuse: 0.18, decay: 0.012, nonlin: 6.0, thresh: 0.15, noise: 0.000 },
  G: { diffuse: 0.22, decay: 0.010, nonlin: 7.0, thresh: 0.20, noise: 0.000 },
  B: { diffuse: 0.16, decay: 0.014, nonlin: 6.5, thresh: 0.18, noise: 0.000 },
  A: { diffuse: 0.08, decay: 0.004, nonlin: 4.0, thresh: 0.05, noise: 0.000 },
});

// 3×3 cross-talk for RGB (A acts as gate)
const crosstalk = reactive<Record<RGBCh, Record<RGBCh, number>>>(
  {
    R: { R:  0.0, G:  0.45, B: -0.15 },
    G: { R: -0.25, G:  0.0,  B:  0.40 },
    B: { R:  0.35, G: -0.20, B:  0.0  },
  }
);

// memory + weather
const memoryMix = ref<number>(0.08); // EMA factor
const weatherStrength = ref<number>(0.20);
const weatherEnabled = ref<boolean>(true);
let weatherRGB: [number,number,number] = [0.2,0.2,0.25];
async function pollWeather(){
  if(!weatherEnabled.value) return;
  try{
    const r = await fetch('/api/state', { cache: 'no-store' });
    if(r.ok){
      const j = await r.json();
      if (Array.isArray(j.babyColour) && j.babyColour.length>=3){
        const [r8,g8,b8] = j.babyColour;
        const tRGB:[number,number,number]=[r8/255,g8/255,b8/255];
        weatherRGB = [
          lerp(weatherRGB[0], tRGB[0], 0.35),
          lerp(weatherRGB[1], tRGB[1], 0.35),
          lerp(weatherRGB[2], tRGB[2], 0.35),
        ];
      }
    }
  }catch(_){} // silent if endpoint absent
}
function nudgeWeather(){
  // small random push that blends with baby colour; feels alive even without endpoint
  const j = (Math.random()*2-1)*0.1;
  weatherRGB = [
    clamp01(weatherRGB[0] + j + (Math.random()-0.5)*0.05),
    clamp01(weatherRGB[1] + j + (Math.random()-0.5)*0.05),
    clamp01(weatherRGB[2] + j + (Math.random()-0.5)*0.05),
  ];
}

// painter
type Stamp = { file:string, label:string, author?:string, url:string, bmp: ImageBitmap };
const stamps = ref<Stamp[]>([]);
const selectedStamp = ref<Stamp|null>(null);
const showStampGrid = ref<boolean>(true);
const paintAlpha = ref<number>(0.85);
const paintMode = ref<'add'|'overwrite'|'subtract'|'multiply'>('add');
const paintChannel = ref<'rgba'|'r'|'g'|'b'|'a'>('rgba');
const flipX = ref<boolean>(false);
const flipY = ref<boolean>(false);
const snapToGrid = ref<boolean>(true);
let rotQuarterTurns = 0;

// pointer state
let isPanning = false;
let isPainting = false;
let lastPaintX = -9999, lastPaintY = -9999;

// presets
const PRESET_KEY = 'bbyworld.presets.v1';
const presetName = ref<string>('');
const selectedPreset = ref<string>('');
const presetMap = reactive<Record<string, any>>(JSON.parse(localStorage.getItem(PRESET_KEY)||'{}'));
const presetKeys = computed(()=> Object.keys(presetMap).sort());

// computed refs for template (world size)
const worldWComputed = computed(()=> worldWRef.value);
const worldHComputed = computed(()=> worldHRef.value);
Object.defineProperty(window, 'bbyW', { get(){return worldWComputed.value} });
Object.defineProperty(window, 'bbyH', { get(){return worldHComputed.value} });


// ————— world setup
function rebuildWorld(){
  running.value = false;
  worldW = worldH = boardSize.value;
  worldWRef.value = worldW; worldHRef.value = worldH;
  bufA = new Float32Array(worldW*worldH*4);
  bufB = new Float32Array(worldW*worldH*4);
  memBuf = new Float32Array(worldW*worldH*4);
  bufA.fill(0); bufB.fill(0); memBuf.fill(0);
  resizeCanvas();
  requestRender();
  nextTick(()=> running.value = true);
}

function clearWorld(){
  bufA.fill(0); bufB.fill(0); memBuf.fill(0);
  requestRender();
}
function randomizeWorld(){
  for(let i=0;i<bufA.length;i++){
    // light random soup; alpha slightly higher to gate activity
    if ((i & 3)===3) bufA[i] = Math.random()*0.4; // A
    else bufA[i] = Math.random()*0.2;
  }
  requestRender();
}

// ————— stamps
async function refreshStamps(){
  try{
    const r = await fetch('/api/gallery', { cache: 'no-store' });
    const j = await r.json();
    // accept either shape: {url,...} or {file,...}
    const raw = Array.isArray(j) ? j : (j.items || []);
    const onlyStamps = raw.filter((it:any)=> (it.file && typeof it.file==='string' && it.file.endsWith('.stamp.png')) || (it.url && (''+it.url).endsWith('.stamp.png')));
    const list:Stamp[] = [];
    for (const it of onlyStamps){
      const file = it.file || it.url.split('/').pop();
      const url = it.url || `/api/gallery/file/${file}`;
      // fetch image as bitmap
      const imgRes = await fetch(url, { cache: 'force-cache' });
      const blob = await imgRes.blob();
      const bmp = await createImageBitmap(blob);
      if (bmp.width!==64 || bmp.height!==64){
        console.warn('Stamp not 64×64; using anyway but mapped as 64 cells:', file, bmp.width, bmp.height);
      }
      list.push({ file, label: it.label || file, author: it.author, url, bmp });
    }
    stamps.value = list;
    if (!selectedStamp.value && list.length) selectedStamp.value = list[0];
  }catch(err){
    console.error('stamp refresh failed', err);
  }
}
function selectStamp(s:Stamp){ selectedStamp.value = s; }
function rotLeft(){ rotQuarterTurns = (rotQuarterTurns+3)%4; }
function rotRight(){ rotQuarterTurns = (rotQuarterTurns+1)%4; }

// ————— canvas & view
function resizeCanvas(){
  const c = canvas.value!, w = canvasWrap.value!.clientWidth, h = canvasWrap.value!.clientHeight;
  const dpr = window.devicePixelRatio||1;
  c.width = Math.max(1, Math.floor(w*dpr));
  c.height = Math.max(1, Math.floor(h*dpr));
  c.style.width = `${w}px`;
  c.style.height = `${h}px`;
  ctx.value = c.getContext('2d', { alpha: false })!;
  requestRender();
}
function resetView(){
  zoom.value = 1;
  camX.value = (worldW/2)|0;
  camY.value = (worldH/2)|0;
  requestRender();
}
function fitToScreen(){
  if(!canvasWrap.value) return;
  const w = canvasWrap.value.clientWidth, h = canvasWrap.value.clientHeight;
  const z = Math.min(w/worldW, h/worldH);
  zoom.value = z;
  camX.value = worldW/2;
  camY.value = worldH/2;
  requestRender();
}
function screenToWorld(sx:number, sy:number){
  const cw = canvas.value!.width, ch = canvas.value!.height;
  const wx = (sx - cw/2)/zoom.value + camX.value;
  const wy = (sy - ch/2)/zoom.value + camY.value;
  return { x: wx, y: wy };
}

// ————— painting
function applyStampAt(worldX:number, worldY:number){
  if(!selectedStamp.value) return;
  // top-left so center by half stamp
  let x0 = Math.round(worldX - 32);
  let y0 = Math.round(worldY - 32);
  if (snapToGrid.value){
    x0 = Math.round(x0);
    y0 = Math.round(y0);
  }
  // draw bitmap into a temp canvas to read pixels (honours rotation/flip)
  const off = new OffscreenCanvas(64,64);
  const octx = off.getContext('2d')!;
  octx.save();
  octx.translate(32,32);
  if (flipX.value) octx.scale(-1, 1);
  if (flipY.value) octx.scale( 1,-1);
  octx.rotate(rotQuarterTurns * Math.PI/2);
  octx.drawImage(selectedStamp.value.bmp, -32, -32);
  octx.restore();
  const img = octx.getImageData(0,0,64,64).data;

  // blend into bufA
  const mode = paintMode.value;
  const alpha = paintAlpha.value;
  const pick = paintChannel.value;

  for (let sy=0; sy<64; sy++){
    const wy = (y0 + sy + worldH) % worldH;
    for (let sx=0; sx<64; sx++){
      const wx = (x0 + sx + worldW) % worldW;
      const si = (sy*64 + sx)*4;
      const r = img[si  ]/255;
      const g = img[si+1]/255;
      const b = img[si+2]/255;
      const a = (img[si+3]/255) * alpha;

      if (a<=0) continue;

      const i = (wy*worldW + wx)*4;
      // get current
      const R = bufA[i  ], G = bufA[i+1], B = bufA[i+2], A = bufA[i+3];

      // choose source by channel selection
      const srcR = (pick==='rgba'||pick==='r') ? r : 0;
      const srcG = (pick==='rgba'||pick==='g') ? g : 0;
      const srcB = (pick==='rgba'||pick==='b') ? b : 0;
      const srcA = (pick==='rgba'||pick==='a') ? a : 0;

      const blend = (dst:number, src:number)=>{
        if (mode==='overwrite') return lerp(dst, src, a);
        if (mode==='add')       return clamp01(dst + src*a);
        if (mode==='subtract')  return clamp01(dst - src*a);
        if (mode==='multiply')  return clamp01(dst * (1 - a + src*a));
        return dst;
      };

      bufA[i  ] = blend(R, srcR);
      bufA[i+1] = blend(G, srcG);
      bufA[i+2] = blend(B, srcB);
      bufA[i+3] = blend(A, srcA);
    }
  }

  requestRender();
}

// ————— pointer handlers
function onPointerDown(e:MouseEvent){
  if (e.button===1 || (e.button===0 && e.shiftKey)){ // middle mouse or shift-drag = pan
    isPanning = true;
    lastPaintX = e.clientX; lastPaintY = e.clientY;
    return;
  }
  if (e.button===0){
    isPainting = true;
    paintAtEvent(e, true);
  }
}
function onPointerMove(e:MouseEvent){
  if (isPanning){
    const dx = e.clientX - lastPaintX;
    const dy = e.clientY - lastPaintY;
    lastPaintX = e.clientX; lastPaintY = e.clientY;
    camX.value -= dx/zoom.value;
    camY.value -= dy/zoom.value;
    requestRender();
    return;
  }
  if (isPainting) paintAtEvent(e, false);
}
function onPointerUp(_e:MouseEvent){
  isPanning = false;
  isPainting = false;
}
function onWheel(e:WheelEvent){
  const delta = Math.sign(e.deltaY) * 0.1;
  const pre = zoom.value;
  const worldBefore = screenToWorld(e.offsetX * (window.devicePixelRatio||1), e.offsetY * (window.devicePixelRatio||1));
  zoom.value = clamp01(pre * (1 - delta));
  if (zoom.value<0.25) zoom.value = 0.25;
  if (zoom.value>8) zoom.value = 8;
  const worldAfter = screenToWorld(e.offsetX * (window.devicePixelRatio||1), e.offsetY * (window.devicePixelRatio||1));
  camX.value += (worldBefore.x - worldAfter.x);
  camY.value += (worldBefore.y - worldAfter.y);
  requestRender();
}
function paintAtEvent(e:MouseEvent, force:boolean){
  const rect = canvas.value!.getBoundingClientRect();
  const sx = (e.clientX - rect.left) * (window.devicePixelRatio||1);
  const sy = (e.clientY - rect.top) * (window.devicePixelRatio||1);
  const w = screenToWorld(sx, sy);
  const wx = Math.round(w.x);
  const wy = Math.round(w.y);
  if (force || Math.hypot(wx-lastPaintX, wy-lastPaintY)>8){
    applyStampAt(wx, wy);
    lastPaintX = wx; lastPaintY = wy;
  }
}

// ————— sim core
function idx(x:number,y:number){ return ((y*worldW + x)<<2); } // *4
function lapSample(buf:Float32Array, x:number, y:number, chOfs:number){
  const xm = (x-1+worldW)%worldW, xp = (x+1)%worldW;
  const ym = (y-1+worldH)%worldH, yp = (y+1)%worldH;
  const c  = buf[idx(x ,y )+chOfs];
  const n  = buf[idx(x ,ym)+chOfs];
  const s  = buf[idx(x ,yp)+chOfs];
  const w  = buf[idx(xm,y )+chOfs];
  const e  = buf[idx(xp,y )+chOfs];
  const nw = buf[idx(xm,ym)+chOfs];
  const ne = buf[idx(xp,ym)+chOfs];
  const sw = buf[idx(xm,yp)+chOfs];
  const se = buf[idx(xp,yp)+chOfs];
  // 3x3 laplacian-ish (normalized)
  // weights: center -1, orth 0.2, diag 0.05 (sum ~0)
  return ( (n+s+w+e)*0.2 + (nw+ne+sw+se)*0.05 - c*1.0 );
}
function step(){
  // one CA step over the whole grid
  const p = params;
  for (let y=0; y<worldH; y++){
    for (let x=0; x<worldW; x++){
      const i = idx(x,y);
      const R = bufA[i  ], G = bufA[i+1], B = bufA[i+2], A = bufA[i+3];

      // laplacians
      const LR = lapSample(bufA, x,y,0);
      const LG = lapSample(bufA, x,y,1);
      const LB = lapSample(bufA, x,y,2);
      const LA = lapSample(bufA, x,y,3);

      // weather input (RGB), gated by A
      const wR = weatherRGB[0]*weatherStrength.value*A;
      const wG = weatherRGB[1]*weatherStrength.value*A;
      const wB = weatherRGB[2]*weatherStrength.value*A;

      // RGB cross-talk: row receives from column
      const xR = crosstalk.R.R*R + crosstalk.R.G*G + crosstalk.R.B*B;
      const xG = crosstalk.G.R*R + crosstalk.G.G*G + crosstalk.G.B*B;
      const xB = crosstalk.B.R*R + crosstalk.B.G*G + crosstalk.B.B*B;

      // noisy inputs
      const nR = (Math.random()*2-1) * p.R.noise;
      const nG = (Math.random()*2-1) * p.G.noise;
      const nB = (Math.random()*2-1) * p.B.noise;
      const nA = (Math.random()*2-1) * p.A.noise;

      // base updates
      let r = R + p.R.diffuse*LR - p.R.decay*R + xR*A + wR + nR;
      let g = G + p.G.diffuse*LG - p.G.decay*G + xG*A + wG + nG;
      let b = B + p.B.diffuse*LB - p.B.decay*B + xB*A + wB + nB;
      let a = A + p.A.diffuse*LA - p.A.decay*A + nA;

      // simple parametric nonlinearity per channel (smooth step around thresh)
      const act = (v:number, k:number, t:number)=> 1/(1+Math.exp(-(v - t)*k));
      r = lerp(r, act(r, p.R.nonlin, p.R.thresh), 0.5);
      g = lerp(g, act(g, p.G.nonlin, p.G.thresh), 0.5);
      b = lerp(b, act(b, p.B.nonlin, p.B.thresh), 0.5);
      a = lerp(a, act(a, p.A.nonlin, p.A.thresh), 0.5);

      // memory (EMA 4D)
      const mi = i;
      memBuf[mi  ] = lerp(memBuf[mi  ], r, memoryMix.value);
      memBuf[mi+1] = lerp(memBuf[mi+1], g, memoryMix.value);
      memBuf[mi+2] = lerp(memBuf[mi+2], b, memoryMix.value);
      memBuf[mi+3] = lerp(memBuf[mi+3], a, memoryMix.value);

      // final blend: current pulled slightly toward memory to stabilise/bloom structures
      r = lerp(r, memBuf[mi  ], 0.25);
      g = lerp(g, memBuf[mi+1], 0.25);
      b = lerp(b, memBuf[mi+2], 0.25);
      a = lerp(a, memBuf[mi+3], 0.25);

      bufB[i  ] = clamp01(r);
      bufB[i+1] = clamp01(g);
      bufB[i+2] = clamp01(b);
      bufB[i+3] = clamp01(a);
    }
  }
  // swap
  const t = bufA; bufA = bufB; bufB = t;
}

// ————— render
let needsRender = true;
function requestRender(){ needsRender = true; }
function render(){
  const c = canvas.value!, context = ctx.value!;
  context.save();
  // clear
  context.fillStyle = '#0b0c0f';
  context.fillRect(0,0,c.width,c.height);

  // transform to world
  context.translate(c.width/2, c.height/2);
  context.scale(zoom.value, zoom.value);
  context.translate(-camX.value, -camY.value);

  // draw world buffer -> imageData (chunked)
  const img = context.createImageData(worldW, worldH);
  const data = img.data;

  // slight colour grading from memory to give vibe
  for (let i=0, j=0; i<bufA.length; i+=4, j+=4){
    const R = bufA[i  ], G = bufA[i+1], B = bufA[i+2], A = bufA[i+3];
    // mix current with soft memory glow
    const mR = memBuf[i  ], mG = memBuf[i+1], mB = memBuf[i+2];
    const glow = 0.20;
    const r = clamp01(lerp(R, mR, glow));
    const g = clamp01(lerp(G, mG, glow));
    const b = clamp01(lerp(B, mB, glow));
    // A modulates brightness
    const br = 0.6 + 0.6*A;
    data[j  ] = Math.floor(255 * clamp01(r * br));
    data[j+1] = Math.floor(255 * clamp01(g * br));
    data[j+2] = Math.floor(255 * clamp01(b * br));
    data[j+3] = 255;
  }

  // nearest-neighbour draw at world scale
  const off = new OffscreenCanvas(worldW, worldH);
  const octx = off.getContext('2d')!;
  octx.putImageData(img, 0, 0);
  context.imageSmoothingEnabled = false;
  context.drawImage(off, 0,0, worldW, worldH);

  // stamp overlay grid + ghost (preview)
  if (showStampGrid.value){
    context.strokeStyle = 'rgba(255,255,255,0.05)';
    context.lineWidth = 1 / zoom.value;
    for (let x=0; x<=worldW; x+=64){
      context.beginPath(); context.moveTo(x,0); context.lineTo(x,worldH); context.stroke();
    }
    for (let y=0; y<=worldH; y+=64){
      context.beginPath(); context.moveTo(0,y); context.lineTo(worldW,y); context.stroke();
    }
  }

  context.restore();

  needsRender = false;
}

// ————— main loop
function tick(ts:number){
  const dt = Math.max(0, ts - lastTickMs);
  lastTickMs = ts;
  frameCounter++;
  frameTimeAcc += dt;
  if (frameTimeAcc >= 500){
    fps.value = frameCounter * 1000 / frameTimeAcc;
    frameCounter = 0;
    frameTimeAcc = 0;
  }

  // schedule sim steps to roughly match ticksPerSecond
  const steps = Math.max(1, Math.round(ticksPerSecond.value/60)); // do multiple per frame if needed
  if (running.value){
    for (let k=0;k<steps;k++) step();
    needsRender = true;
  }

  if (needsRender) render();
  rafId = requestAnimationFrame(tick);
}

// ————— controls
function toggleRun(){ running.value = !running.value; }
function stepOnce(){ if(!running.value){ step(); requestRender(); } }

// ————— screenshots
function saveScreenshot(){
  if(!canvas.value) return;
  // render at 1:1 world scale into offscreen for crispness
  const off = document.createElement('canvas');
  off.width = worldW; off.height = worldH;
  const octx = off.getContext('2d')!;
  const img = octx.createImageData(worldW, worldH);
  const data = img.data;
  for (let i=0, j=0; i<bufA.length; i+=4, j+=4){
    const R = bufA[i  ], G = bufA[i+1], B = bufA[i+2], A = bufA[i+3];
    const br = 0.6 + 0.6*A;
    data[j  ] = Math.floor(255*clamp01(lerp(R, memBuf[i  ], 0.2)*br));
    data[j+1] = Math.floor(255*clamp01(lerp(G, memBuf[i+1], 0.2)*br));
    data[j+2] = Math.floor(255*clamp01(lerp(B, memBuf[i+2], 0.2)*br));
    data[j+3] = 255;
  }
  octx.putImageData(img,0,0);
  const a = document.createElement('a');
  a.download = `bbyWorld_${worldW}x${worldH}_${Date.now()}.png`;
  a.href = off.toDataURL('image/png');
  a.click();
}

// ————— presets IO
function snapState(){
  return {
    boardSize: boardSize.value,
    params: JSON.parse(JSON.stringify(params)),
    crosstalk: JSON.parse(JSON.stringify(crosstalk)),
    memoryMix: memoryMix.value,
    weatherStrength: weatherStrength.value,
    weatherEnabled: weatherEnabled.value,
    ticksPerSecond: ticksPerSecond.value,
  };
}
function applyState(s:any){
  if (!s) return;
  if (s.boardSize && s.boardSize!==boardSize.value){
    boardSize.value = s.boardSize;
    rebuildWorld();
  }
  Object.assign(params.R, s.params?.R||{});
  Object.assign(params.G, s.params?.G||{});
  Object.assign(params.B, s.params?.B||{});
  Object.assign(params.A, s.params?.A||{});
  ['R','G','B'].forEach((row:any)=>{
    if (s.crosstalk && s.crosstalk[row]){
      Object.assign((crosstalk as any)[row], s.crosstalk[row]);
    }
  });
  if (typeof s.memoryMix==='number') memoryMix.value = s.memoryMix;
  if (typeof s.weatherStrength==='number') weatherStrength.value = s.weatherStrength;
  if (typeof s.weatherEnabled==='boolean') weatherEnabled.value = s.weatherEnabled;
  if (typeof s.ticksPerSecond==='number') ticksPerSecond.value = s.ticksPerSecond;
  requestRender();
}
function savePreset(){
  const name = (presetName.value||'preset').trim();
  if (!name) return;
  presetMap[name] = snapState();
  localStorage.setItem(PRESET_KEY, JSON.stringify(presetMap));
  presetName.value = '';
}
function loadPreset(){
  if (!selectedPreset.value) return;
  applyState(presetMap[selectedPreset.value]);
}
function deletePreset(){
  if (!selectedPreset.value) return;
  delete presetMap[selectedPreset.value];
  localStorage.setItem(PRESET_KEY, JSON.stringify(presetMap));
  selectedPreset.value = '';
}
function exportPreset(){
  const blob = new Blob([JSON.stringify(snapState(), null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.download = `bbyWorld_preset_${Date.now()}.json`;
  a.href = URL.createObjectURL(blob);
  a.click();
}
function importPreset(e:Event){
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const fr = new FileReader();
  fr.onload = ()=> {
    try{ const s = JSON.parse(String(fr.result)); applyState(s); }
    catch(err){ console.error('bad preset json', err); }
  };
  fr.readAsText(file);
}

// ————— lifecycle
onMounted(async ()=>{
  window.addEventListener('resize', resizeCanvas);
  rebuildWorld();
  resizeCanvas();
  resetView();
  await refreshStamps();
  rafId = requestAnimationFrame(tick);

  // gentle weather polling loop
  const wTimer = setInterval(pollWeather, 1200);
  (window as any).__bbyWeatherTimer = wTimer;
});
onBeforeUnmount(()=>{
  cancelAnimationFrame(rafId);
  window.removeEventListener('resize', resizeCanvas);
  if ((window as any).__bbyWeatherTimer) clearInterval((window as any).__bbyWeatherTimer);
});

// expose to template with distinct names to avoid shadowing
const worldWidth = worldWComputed;
const worldHeight = worldHComputed;
</script>

<style scoped>
:root { --bg:#0a0b0e; --ink:#e6e7ee; --mut:#9aa0aa; --acc:#47f; --a2:#7cf; --hi:#4f8; --warn:#f75; }
* { box-sizing: border-box; }
.bbyworld-page {
  display:flex; flex-direction:column; gap:12px;
  background:var(--bg); color:var(--ink); height:100%;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Inter, Arial, "Apple Color Emoji", "Segoe UI Emoji";
}
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; opacity:0.8; }
.title { font-size:18px; margin:0 12px 0 0; }
.toolbar { display:flex; align-items:center; gap:12px; padding:10px 12px; border-bottom:1px solid #151820; background:#0c0e13; position:sticky; top:0; z-index:2; }
.toolbar .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.toolbar label { color:var(--mut); font-size:12px; }
.toolbar button { background:#141824; color:#cfe3ff; border:1px solid #1d2333; padding:6px 10px; border-radius:6px; cursor:pointer; }
.toolbar button.active { background:#1b2840; border-color:#2a3e67; color:#bfe2ff; }
.toolbar select, .toolbar input[type="range"] { accent-color:#87b3ff; }

.main { display:flex; gap:12px; padding:0 12px 12px; height:100%; }
.left { flex:2; display:flex; flex-direction:column; gap:12px; min-width:300px; }
.right { flex:1; display:flex; flex-direction:column; gap:12px; min-width:320px; }

.canvas-wrap { position:relative; flex:1; background:#05060a; border:1px solid #151820; border-radius:8px; overflow:hidden; }
.canvas-wrap canvas { display:block; width:100%; height:100%; image-rendering: pixelated; cursor: crosshair; }
.hud { position:absolute; left:8px; bottom:8px; display:flex; gap:10px; background:rgba(0,0,0,0.35); border:1px solid rgba(255,255,255,0.07); padding:4px 8px; border-radius:6px; font-size:12px; color:#c9d1e1; }
.presets { background:#0c0e13; border:1px solid #151a22; border-radius:8px; padding:8px 12px; }
.presets summary { cursor:pointer; user-select:none; color:#b7c7e8; margin-bottom:6px; }
.row { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }

.panel { background:#0c0f15; border:1px solid #151a22; border-radius:10px; padding:10px 12px; }
.panel h3 { margin:0 0 8px; font-size:14px; color:#bcd4ff; }
.grid2 { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:8px; }
.col { background:#0d1118; border:1px solid #151b24; border-radius:8px; padding:8px; }
.col h4 { margin:0 0 6px; font-size:13px; color:#bfe2ff; }

.matrix { display:flex; flex-direction:column; gap:6px; }
.mrow { display:grid; grid-template-columns: 48px 1fr 1fr 1fr; gap:8px; align-items:center; }
.mrow.header { color:#9fb2d8; opacity:0.9; }
.rowlab { color:#9fb2d8; }
.matrix input[type="range"] { width:100%; accent-color:#7db7ff; }
.hint { font-size:12px; color:#8da2bb; opacity:0.8; }

.stamp-list { display:grid; grid-template-columns: repeat(auto-fill, minmax(120px,1fr)); gap:8px; max-height:40vh; overflow:auto; padding:2px; }
.stamp { display:flex; flex-direction:column; gap:4px; background:#0c1016; border:1px solid #151b24; border-radius:8px; padding:6px; cursor:pointer; }
.stamp.sel { outline:2px solid #4aa8ff; }
.stamp img { width:100%; image-rendering: pixelated; border-radius:4px; border:1px solid #141a22; background:#05070b; }
.stamp .meta { display:flex; flex-direction:column; line-height:1.1; }
.stamp .lab { color:#cbe0ff; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.stamp .sub { color:#9db2d1; font-size:11px; opacity:0.9; }
.empty { padding:8px; color:#8ca0b8; font-size:12px; }

input[type="range"] { width:120px; }
select, input[type="text"] { background:#0f1420; border:1px solid #1a2232; color:#dde6f7; border-radius:6px; padding:6px 8px; }
label.import input { display:none; }
</style>