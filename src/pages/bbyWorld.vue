<!-- CHARIS CAT // bbyWorld — THE DEFINITIVE COMBINED VERSION (2025-08-20)
     Life-sim cellular automaton with RGBA field + agent layer + pixel-correct stamps.
     • Menus left, square screen, no top bar. Grid sizes 4/8/16/32/64/128.
     • Stamps: ANY pixel size (no forced 64), exact pixel→cell mapping, rotate/flip, blend modes, RGBA target, snap-to-grid or snap-to-stamp.
     • Field engine: per-channel diffuse/decay/nonlin/threshold/noise, RGB cross-talk, EMA memory (4th dim), baby-weather input.
     • Life layer: agents (spawn/move/hunt/deposit/erode/reproduce/die), spatial occupancy, group insight.
     • Input toggles: wheel zoom, touch pan/zoom (off by default), ALT+drag scope-box, hover legend.
     • Presets: save/load/export/import. Screenshot exporter.
-->

<template>
  <div class="page-container">
    <bubbleGraveyard />
    <section class="main">
      <!-- LEFT: panels -->
      <div class="left">

        <!-- STAMPS -->
        <div class="panel">
          <h3>stamps (pixel-correct)</h3>

          <div class="row">
            <button @click="refreshStamps">refresh</button>

            <label><input type="checkbox" v-model="showStampGrid"/> grid</label>

            <label>grid
              <select v-model.number="gridSize">
                <option v-for="g in GRID_SIZES" :key="g" :value="g">{{ g }}</option>
              </select>
            </label>

            <label>snap
              <select v-model="snapMode">
                <option value="grid">to {{ gridSize }}</option>
                <option value="stamp">to stamp</option>
              </select>
            </label>

            <label>alpha
              <input type="range" min="0" max="1" step="0.01" v-model.number="paintAlpha"/>
            </label>
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
              title="click to select stamp"
            >
              <img :src="s.url" :alt="s.label" />
              <div class="meta">
                <div class="lab">{{ s.label || s.file }}</div>
                <div class="sub">{{ s.author || 'unknown' }}</div>
              </div>
            </button>
            <div v-if="!stamps.length" class="empty">no *.stamp.png found</div>
          </div>
        </div>

        <!-- WORLD / VIEW / TRANSPORT -->
        <div class="panel">
          <h3>board & transport</h3>
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
            <input type="range" min="1" max="240" step="1" v-model.number="ticksPerSecond"/>
            <span class="mono">{{ ticksPerSecond }} Hz</span>

            <button :class="{active: running}" @click="toggleRun">{{ running ? 'pause' : 'run' }}</button>
            <button @click="stepOnce">step</button>
            <button @click="clearWorld">clear</button>
            <button @click="randomizeWorld">random</button>
            <button @click="saveScreenshot">screenshot</button>
          </div>
        </div>

        <!-- INPUT & DISPLAY (legacy behaviours as toggles) -->
        <div class="panel">
          <h3>ui & input</h3>
          <div class="row">
            <label><input type="checkbox" v-model="allowWheelZoom"> wheel zoom</label>
            <label><input type="checkbox" v-model="allowTouchPanZoom"> touch pan/zoom</label>
            <label><input type="checkbox" v-model="scopeEnabled"> scope (alt+drag)</label>
            <label><input type="checkbox" v-model="showLegend"> hover legend</label>
          </div>
        </div>

        <!-- FIELD ENGINE -->
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
              <div class="hint">row receives from column (A gates update)</div>
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

        <!-- LIFE LAYER -->
        <div class="panel">
          <h3>life-sim (agents)</h3>
          <fieldset>
            <legend>toggles</legend>
            <div class="row">
              <label><input type="checkbox" v-model="enableAgents"> enable life</label>
              <label><input type="checkbox" v-model="agentsDeposit"> deposit colour</label>
              <label><input type="checkbox" v-model="agentsErode"> erode A</label>
              <label><input type="checkbox" v-model="agentsHunt"> hunt neighbours</label>
            </div>
          </fieldset>
          <div class="row">
            <button @click="spawnRandom(64)">spawn 64</button>
            <button @click="killAll">kill all</button>
          </div>

          <details>
            <summary>group insight</summary>
            <div class="groups">
              <div class="ghead"><span>colour</span><span>count</span><span>%</span><span>avg age</span><span>energy</span><span>strength</span></div>
              <div class="grow" v-for="g in groups" :key="g.colour">
                <span class="colour-cell"><span class="colour-swatch" :style="{background:g.colour}"></span>{{ g.colour }}</span>
                <span>{{ g.count }}</span>
                <span>{{ g.percentage.toFixed(1) }}</span>
                <span>{{ formatTicks(g.avgAge) }}</span>
                <span>{{ g.avgEnergy.toFixed(1) }}</span>
                <span>{{ g.avgStrength.toFixed(2) }}</span>
              </div>
            </div>
          </details>
        </div>

        <!-- PRESETS -->
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

      <!-- RIGHT: square screen -->
      <div class="right">
        <div class="canvas-wrap"
             ref="canvasWrap"
             @mousedown="onPointerDown"
             @mousemove="onPointerMove"
             @mouseup="onPointerUp"
             @mouseleave="onPointerUp"
             @wheel.prevent="onWheel">
          <canvas ref="canvas" />
          <div v-if="scopeEnabled && scopeBox.active" class="scope-rect" :style="scopeStyle"></div>
          <div v-if="showLegend && hoverInfo" class="legend">
            <div class="legend-row">
              <span class="pill">x</span> {{ hoverInfo.x }} <span class="pill">y</span> {{ hoverInfo.y }}
              <span class="pill">fps</span> {{ fps.toFixed(0) }}
            </div>
            <div class="legend-row">
              <span class="pill">R</span> {{ hoverInfo.R }}
              <span class="pill">G</span> {{ hoverInfo.G }}
              <span class="pill">B</span> {{ hoverInfo.B }}
              <span class="pill">A</span> {{ hoverInfo.A }}
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, reactive, ref, computed, nextTick } from 'vue';
import bubbleGraveyard from '@/components/bubbleGraveyard.vue';

/* ——— util ——— */
const clamp01 = (x:number)=> x<0?0:(x>1?1:x);
const lerp = (a:number,b:number,t:number)=> a+(b-a)*t;
const makeOffscreen = (w:number, h:number): HTMLCanvasElement | OffscreenCanvas => {
  try { if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(w, h); } catch {}
  const c = document.createElement('canvas'); c.width = w; c.height = h; return c;
};

/* ——— channels & typed params to avoid TS7053 ——— */
const CHS = ['R','G','B','A'] as const;
type Ch = typeof CHS[number];
const RGB = ['R','G','B'] as const;
type RGBCh = typeof RGB[number];

type Params = { [k in Ch]: { diffuse:number, decay:number, nonlin:number, thresh:number, noise:number } };

/* ——— grid / board ——— */
const GRID_SIZES = [4,8,16,32,64,128] as const;
const gridSize = ref<number>(32);
type SnapMode = 'grid'|'stamp';
const snapMode = ref<SnapMode>('grid');

const boardSizeOptions = [256, 384, 512, 768];
const boardSize = ref<number>(512);

/* ——— canvas / camera / sim cadence ——— */
const canvas = ref<HTMLCanvasElement|null>(null);
const canvasWrap = ref<HTMLDivElement|null>(null);
const ctx = ref<CanvasRenderingContext2D|null>(null);

const zoom = ref<number>(1);
const camX = ref<number>(0);
const camY = ref<number>(0);

const ticksPerSecond = ref<number>(60);
const running = ref<boolean>(true);
const fps = ref<number>(0);

let rafId = 0, lastTickMs = 0, frameCounter = 0, frameTimeAcc = 0;

/* ——— world buffers (double) ——— */
let worldW = 0, worldH = 0;
let bufA: Float32Array; // current
let bufB: Float32Array; // next
let memBuf: Float32Array; // EMA memory
const worldWRef = ref<number>(0);
const worldHRef = ref<number>(0);

/* ——— field params ——— */
const params = reactive<Params>({
  R: { diffuse: 0.18, decay: 0.012, nonlin: 6.0, thresh: 0.15, noise: 0.000 },
  G: { diffuse: 0.22, decay: 0.010, nonlin: 7.0, thresh: 0.20, noise: 0.000 },
  B: { diffuse: 0.16, decay: 0.014, nonlin: 6.5, thresh: 0.18, noise: 0.000 },
  A: { diffuse: 0.08, decay: 0.004, nonlin: 4.0, thresh: 0.05, noise: 0.000 },
});

/* ——— RGB cross-talk (A gates activity) ——— */
const crosstalk = reactive<Record<RGBCh, Record<RGBCh, number>>>(
  { R:{R:0.0,G:0.45,B:-0.15}, G:{R:-0.25,G:0.0,B:0.40}, B:{R:0.35,G:-0.20,B:0.0} }
);

/* ——— memory & baby-weather ——— */
const memoryMix = ref<number>(0.08);
const weatherStrength = ref<number>(0.20);
const weatherEnabled = ref<boolean>(true);
let weatherRGB: [number,number,number] = [0.2,0.2,0.25];
async function pollWeather(){
  if(!weatherEnabled.value) return;
  try{
    const r = await fetch('/api/state', { cache: 'no-store' });
    if (r.ok){
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
  }catch(_){}
}
function nudgeWeather(){
  const j = (Math.random()*2-1)*0.1;
  weatherRGB = [
    clamp01(weatherRGB[0] + j + (Math.random()-0.5)*0.05),
    clamp01(weatherRGB[1] + j + (Math.random()-0.5)*0.05),
    clamp01(weatherRGB[2] + j + (Math.random()-0.5)*0.05),
  ];
}

/* ——— stamps (pixel-correct; ANY size) ——— */
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

/* ——— input toggles (legacy parity) ——— */
const allowWheelZoom = ref<boolean>(false);
const allowTouchPanZoom = ref<boolean>(false); // (we don’t attach any unless true)
const scopeEnabled = ref<boolean>(false);
const showLegend = ref<boolean>(false);

type HoverInfo = { x:number,y:number,R:number,G:number,B:number,A:number };
const hoverInfo = ref<HoverInfo|null>(null);
const scopeBox = reactive({ active:false, x0:0, y0:0, x1:0, y1:0 });
const scopeStyle = computed(()=> {
  if (!scopeBox.active || !canvas.value) return {};
  const dpr = window.devicePixelRatio||1;
  const cw = canvas.value.width, ch = canvas.value.height;
  const x = Math.min(scopeBox.x0, scopeBox.x1);
  const y = Math.min(scopeBox.y0, scopeBox.y1);
  const w = Math.abs(scopeBox.x1 - scopeBox.x0)+1;
  const h = Math.abs(scopeBox.y1 - scopeBox.y0)+1;
  const sx = Math.round((x - camX.value) * zoom.value + cw/2);
  const sy = Math.round((y - camY.value) * zoom.value + ch/2);
  const sw = Math.round(w * zoom.value);
  const sh = Math.round(h * zoom.value);
  return { left: sx/dpr+'px', top: sy/dpr+'px', width: sw/dpr+'px', height: sh/dpr+'px' };
});

/* ——— life layer (agents) ——— */
const enableAgents = ref<boolean>(true);
const agentsDeposit = ref<boolean>(true);
const agentsErode = ref<boolean>(true);
const agentsHunt = ref<boolean>(true);

type Agent = {
  x:number, y:number, alive:boolean,
  r:number, g:number, b:number, a:number,
  energy:number, strength:number, mass:number, charge:number, age:number
};
const living = reactive<Agent[]>([]);
const spatialMap: Record<number, Agent|undefined> = Object.create(null);

const I = (x:number,y:number)=> {
  const xx = ((x%worldW)+worldW)%worldW;
  const yy = ((y%worldH)+worldH)%worldH;
  return (yy*worldW + xx)|0;
};

function spawn(x:number,y:number, col?:{r:number,g:number,b:number,a?:number}) {
  if (!worldW || !worldH) return;
  const ii = I(x,y); if (spatialMap[ii]) return;
  const a:Agent = {
    x:(x|0), y:(y|0), alive:true,
    r:(col?.r ?? (200+Math.random()*55))/255,
    g:(col?.g ?? (180+Math.random()*55))/255,
    b:(col?.b ?? (220+Math.random()*35))/255,
    a:((col?.a ?? 255)/255),
    energy: 10 + Math.random()*10,
    strength: 0.5 + Math.random()*0.5,
    mass: 1.0, charge: (Math.random()*2-1)*0.05,
    age: 0
  };
  living.push(a); spatialMap[ii] = a;
}
function spawnRandom(n=32){
  for(let k=0;k<n;k++){
    spawn(Math.floor(Math.random()*worldW), Math.floor(Math.random()*worldH), {
      r: (Math.random()*255)|0, g: (Math.random()*255)|0, b: (Math.random()*255)|0, a: 255
    });
  }
}
function killAll(){
  living.splice(0,living.length);
  for (const k in spatialMap) delete spatialMap[k as any];
}

function neighbourCount(x:number,y:number){
  let c=0;
  const xm=(x-1+worldW)%worldW, xp=(x+1)%worldW;
  const ym=(y-1+worldH)%worldH, yp=(y+1)%worldH;
  if (spatialMap[I(xm,ym)]) c++; if (spatialMap[I(x,ym)]) c++; if (spatialMap[I(xp,ym)]) c++;
  if (spatialMap[I(xm,y )]) c++;                                   if (spatialMap[I(xp,y )]) c++;
  if (spatialMap[I(xm,yp)]) c++; if (spatialMap[I(x,yp)]) c++; if (spatialMap[I(xp,yp)]) c++;
  return c;
}
function getAffinity(x:number,y:number,a:Agent){
  const i = (I(x,y)<<2);
  const R = bufA[i  ], G = bufA[i+1], B = bufA[i+2], A = bufA[i+3];
  const colourLike = a.r*R + a.g*G + a.b*B;
  const gate = 0.2 + 0.8*A;
  return colourLike*gate - neighbourCount(x,y)*0.02;
}
function moveSolid(a:Agent, nx:number, ny:number){
  const oldI = I(a.x,a.y), newI = I(nx,ny);
  if (spatialMap[newI]) return false;
  delete spatialMap[oldI];
  a.x = ((nx%worldW)+worldW)%worldW;
  a.y = ((ny%worldH)+worldH)%worldH;
  spatialMap[I(a.x,a.y)] = a;
  return true;
}
function deposit(a:Agent){
  if (!agentsDeposit.value) return;
  const i = (I(a.x,a.y)<<2);
  bufA[i  ] = clamp01(bufA[i  ] + 0.02*a.r);
  bufA[i+1] = clamp01(bufA[i+1] + 0.02*a.g);
  bufA[i+2] = clamp01(bufA[i+2] + 0.02*a.b);
  bufA[i+3] = clamp01(bufA[i+3] + 0.04*a.a);
}
function erodeSolid(a:Agent){
  if (!agentsErode.value) return;
  const i = (I(a.x,a.y)<<2);
  bufA[i+3] = clamp01(bufA[i+3] - 0.03*a.strength);
}
function worldTickAgents(){
  if (!enableAgents.value || living.length===0) return;
  const dirs = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,1],[1,-1],[-1,-1]];
  for (let idx=0; idx<living.length; idx++){
    const a = living[idx]; if (!a.alive) continue;
    a.age += 1; a.energy -= 0.01;

    if (agentsHunt.value){
      for (const [dx,dy] of dirs){
        const n = spatialMap[I(a.x+dx, a.y+dy)];
        if (n && n!==a && (a.strength>n.strength) && Math.random()<0.02){
          n.alive = false; delete spatialMap[I(n.x,n.y)];
          a.energy += 5; a.strength += 0.02;
        }
      }
    }

    let best = {score:-1e9, dx:0, dy:0};
    for (const [dx,dy] of dirs){
      const s = getAffinity(a.x+dx, a.y+dy, a);
      if (s>best.score) best = {score:s, dx, dy};
    }
    moveSolid(a, a.x+best.dx, a.y+best.dy);
    deposit(a); erodeSolid(a);

    if (a.energy>20 && Math.random()<0.005){
      const d = dirs[(Math.random()*dirs.length)|0];
      spawn(a.x+d[0], a.y+d[1], { r:Math.round(a.r*255), g:Math.round(a.g*255), b:Math.round(a.b*255), a:Math.round(a.a*255) });
      a.energy *= 0.5;
    }
    if (a.energy<=0 && Math.random()<0.02){
      a.alive=false; delete spatialMap[I(a.x,a.y)];
    }
  }
  for (let i=living.length-1;i>=0;i--) if(!living[i].alive) living.splice(i,1);
}
const groups = computed(()=> {
  const map = new Map<string,{count:number, age:number, energy:number, strength:number}>();
  for (const a of living){
    const colour = `rgb(${Math.round(a.r*255)},${Math.round(a.g*255)},${Math.round(a.b*255)})`;
    const g = map.get(colour) || {count:0, age:0, energy:0, strength:0};
    g.count++; g.age+=a.age; g.energy+=a.energy; g.strength+=a.strength; map.set(colour, g);
  }
  const total = living.length||1;
  return [...map.entries()].map(([colour,g])=>({
    colour, count:g.count, percentage:100*g.count/total,
    avgAge:g.age/g.count, avgEnergy:g.energy/g.count, avgStrength:g.strength/g.count
  }));
});
function formatTicks(t:number){ return `${Math.round(t)}t`; }

/* ——— world setup ——— */
function rebuildWorld(){
  running.value = false;
  worldW = worldH = boardSize.value;
  worldWRef.value = worldW; worldHRef.value = worldH;
  bufA = new Float32Array(worldW*worldH*4);
  bufB = new Float32Array(worldW*worldH*4);
  memBuf = new Float32Array(worldW*worldH*4);
  bufA.fill(0); bufB.fill(0); memBuf.fill(0);
  killAll();
  resizeCanvas();
  requestRender();
  nextTick(()=> running.value = true);
}
function clearWorld(){ bufA.fill(0); bufB.fill(0); memBuf.fill(0); killAll(); requestRender(); }
function randomizeWorld(){
  for(let i=0;i<bufA.length;i++){
    if ((i & 3)===3) bufA[i] = Math.random()*0.4; // A a little higher
    else bufA[i] = Math.random()*0.2;
  }
  requestRender();
}

/* ——— stamps ——— */
async function refreshStamps(){
  try{
    const r = await fetch('/api/gallery', { cache: 'no-store' });
    const j = await r.json();
    const raw = Array.isArray(j) ? j : (j.items || []);
    const onlyStamps = raw.filter((it:any)=> (it.file && typeof it.file==='string' && it.file.endsWith('.stamp.png')) || (it.url && (''+it.url).endsWith('.stamp.png')));
    const list:Stamp[] = [];
    for (const it of onlyStamps){
      const file = it.file || (it.url.split('/').pop() ?? 'stamp.png');
      const url = it.url || `/api/gallery/file/${file}`;
      const imgRes = await fetch(url, { cache: 'force-cache' });
      const blob = await imgRes.blob();
      const bmp = await createImageBitmap(blob);
      list.push({ file, label: it.label || file, author: it.author, url, bmp });
    }
    stamps.value = list;
    if (!selectedStamp.value && list.length) selectedStamp.value = list[0];
  }catch(err){ console.error('stamp refresh failed', err); }
}
function selectStamp(s:Stamp){ selectedStamp.value = s; }
function rotLeft(){ rotQuarterTurns = (rotQuarterTurns+3)%4; }
function rotRight(){ rotQuarterTurns = (rotQuarterTurns+1)%4; }

/* ——— canvas & view ——— */
function resizeCanvas(){
  const c = canvas.value!, wrap = canvasWrap.value!;
  const w = wrap.clientWidth, h = wrap.clientHeight;
  const side = Math.max(1, Math.floor(Math.min(w, h)));
  const dpr = window.devicePixelRatio || 1;
  c.width = side * dpr;
  c.height = side * dpr;
  c.style.width = side + 'px';
  c.style.height = side + 'px';
  ctx.value = c.getContext('2d', { alpha: false })!;
  requestRender();
}
function resetView(){ zoom.value = 1; camX.value = (worldW/2)|0; camY.value = (worldH/2)|0; requestRender(); }
function fitToScreen(){
  if(!canvasWrap.value) return;
  const w = canvasWrap.value.clientWidth, h = canvasWrap.value.clientHeight;
  const z = Math.min(w/worldW, h/worldH);
  zoom.value = z; camX.value = worldW/2; camY.value = worldH/2; requestRender();
}
function screenToWorld(sx:number, sy:number){
  const cw = canvas.value!.width, ch = canvas.value!.height;
  const wx = (sx - cw/2)/zoom.value + camX.value;
  const wy = (sy - ch/2)/zoom.value + camY.value;
  return { x: wx, y: wy };
}

/* ——— painting (pixel-correct) ——— */
function applyStampAt(worldX:number, worldY:number){
  if(!selectedStamp.value) return;
  const sw = selectedStamp.value.bmp.width|0;
  const sh = selectedStamp.value.bmp.height|0;
  const cx = (sw/2)|0, cy = (sh/2)|0;

  let x0 = Math.round(worldX - cx);
  let y0 = Math.round(worldY - cy);

  if (snapToGrid.value){
    if (snapMode.value === 'grid'){
      const g = gridSize.value | 0;
      x0 = Math.round(Math.round(x0 / g) * g);
      y0 = Math.round(Math.round(y0 / g) * g);
    } else {
      x0 = Math.round(Math.round(x0 / sw) * sw);
      y0 = Math.round(Math.round(y0 / sh) * sh);
    }
  }

  const off = makeOffscreen(sw, sh) as any;
  const octx = off.getContext('2d')!;
  octx.save();
  octx.translate(sw/2, sh/2);
  if (flipX.value) octx.scale(-1, 1);
  if (flipY.value) octx.scale( 1,-1);
  octx.rotate(rotQuarterTurns * Math.PI/2);
  octx.drawImage(selectedStamp.value.bmp, -sw/2, -sh/2);
  octx.restore();
  const img = octx.getImageData(0,0,sw,sh).data;

  const mode = paintMode.value, alpha = paintAlpha.value, pick = paintChannel.value;

  for (let sy=0; sy<sh; sy++){
    const wy = (y0 + sy + worldH) % worldH;
    for (let sx=0; sx<sw; sx++){
      const wx = (x0 + sx + worldW) % worldW;
      const si = (sy*sw + sx)*4;
      const r = img[si  ]/255, g = img[si+1]/255, b = img[si+2]/255;
      const a = (img[si+3]/255) * alpha;
      if (a<=0) continue;

      const i = (wy*worldW + wx)*4;
      const R = bufA[i  ], G = bufA[i+1], B = bufA[i+2], A = bufA[i+3];

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

/* ——— pointer handlers ——— */
let isPanning = false;
let isPainting = false;
let lastPaintX = -9999, lastPaintY = -9999;

function getWorldFromEvent(e:MouseEvent){
  const rect = canvas.value!.getBoundingClientRect();
  const sx = (e.clientX - rect.left) * (window.devicePixelRatio||1);
  const sy = (e.clientY - rect.top) * (window.devicePixelRatio||1);
  return screenToWorld(sx, sy);
}

function onPointerDown(e:MouseEvent){
  // scope
  if (scopeEnabled.value && e.altKey){
    const p = getWorldFromEvent(e);
    scopeBox.active = true; scopeBox.x0 = scopeBox.x1 = Math.round(p.x); scopeBox.y0 = scopeBox.y1 = Math.round(p.y);
    return;
  }
  // pan (middle or shift+left)
  if (e.button===1 || (e.button===0 && e.shiftKey)){
    isPanning = true; lastPaintX = e.clientX; lastPaintY = e.clientY; return;
  }
  // paint
  if (e.button===0){ isPainting = true; paintAtEvent(e, true); }
}
function onPointerMove(e:MouseEvent){
  if (showLegend.value){
    const p = getWorldFromEvent(e);
    const xi = Math.max(0, Math.min(worldW-1, Math.round(p.x)));
    const yi = Math.max(0, Math.min(worldH-1, Math.round(p.y)));
    const i = (yi*worldW + xi)*4;
    hoverInfo.value = {
      x: xi, y: yi,
      R: Math.round(bufA[i  ]*255), G: Math.round(bufA[i+1]*255),
      B: Math.round(bufA[i+2]*255), A: Math.round(bufA[i+3]*255),
    };
  }
  if (scopeEnabled.value && scopeBox.active){
    const p = getWorldFromEvent(e);
    scopeBox.x1 = Math.round(p.x); scopeBox.y1 = Math.round(p.y);
    return requestRender();
  }
  if (isPanning){
    const dx = e.clientX - lastPaintX;
    const dy = e.clientY - lastPaintY;
    lastPaintX = e.clientX; lastPaintY = e.clientY;
    camX.value -= dx/zoom.value;
    camY.value -= dy/zoom.value;
    return requestRender();
  }
  if (isPainting) paintAtEvent(e, false);
}
function onPointerUp(_e:MouseEvent){
  isPanning = false; isPainting = false;
  if (scopeEnabled.value) scopeBox.active = false;
}
function onWheel(e:WheelEvent){
  if (!allowWheelZoom.value) return; // strict
  const delta = Math.sign(e.deltaY) * 0.1;
  const pre = zoom.value;
  const worldBefore = screenToWorld(e.offsetX * (window.devicePixelRatio||1), e.offsetY * (window.devicePixelRatio||1));
  zoom.value = clamp01(pre * (1 - delta));
  if (zoom.value<0.25) zoom.value = 0.25;
  if (zoom.value>8)    zoom.value = 8;
  const worldAfter = screenToWorld(e.offsetX * (window.devicePixelRatio||1), e.offsetY * (window.devicePixelRatio||1));
  camX.value += (worldBefore.x - worldAfter.x);
  camY.value += (worldBefore.y - worldAfter.y);
  requestRender();
}
function paintAtEvent(e:MouseEvent, force:boolean){
  const p = getWorldFromEvent(e);
  const wx = Math.round(p.x), wy = Math.round(p.y);
  if (force || Math.hypot(wx-lastPaintX, wy-lastPaintY)>8){
    applyStampAt(wx, wy);
    lastPaintX = wx; lastPaintY = wy;
  }
}

/* ——— sim core (field) ——— */
function idx(x:number,y:number){ return ((y*worldW + x)<<2); }
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
  return ( (n+s+w+e)*0.2 + (nw+ne+sw+se)*0.05 - c*1.0 );
}
function step(){
  for (let y=0; y<worldH; y++){
    for (let x=0; x<worldW; x++){
      const i = idx(x,y);
      const R = bufA[i  ], G = bufA[i+1], B = bufA[i+2], A = bufA[i+3];

      const LR = lapSample(bufA, x,y,0);
      const LG = lapSample(bufA, x,y,1);
      const LB = lapSample(bufA, x,y,2);
      const LA = lapSample(bufA, x,y,3);

      // weather input (RGB), gated by A
      const wR = weatherRGB[0]*weatherStrength.value*A;
      const wG = weatherRGB[1]*weatherStrength.value*A;
      const wB = weatherRGB[2]*weatherStrength.value*A;

      // RGB cross-talk: row receives from columns
      const xR = crosstalk.R.R*R + crosstalk.R.G*G + crosstalk.R.B*B;
      const xG = crosstalk.G.R*R + crosstalk.G.G*G + crosstalk.G.B*B;
      const xB = crosstalk.B.R*R + crosstalk.B.G*G + crosstalk.B.B*B;

      const nR = (Math.random()*2-1) * params.R.noise;
      const nG = (Math.random()*2-1) * params.G.noise;
      const nB = (Math.random()*2-1) * params.B.noise;
      const nA = (Math.random()*2-1) * params.A.noise;

      let r = R + params.R.diffuse*LR - params.R.decay*R + xR*A + wR + nR;
      let g = G + params.G.diffuse*LG - params.G.decay*G + xG*A + wG + nG;
      let b = B + params.B.diffuse*LB - params.B.decay*B + xB*A + wB + nB;
      let a = A + params.A.diffuse*LA - params.A.decay*A + nA;

      const act = (v:number, k:number, t:number)=> 1/(1+Math.exp(-(v - t)*k));
      r = lerp(r, act(r, params.R.nonlin, params.R.thresh), 0.5);
      g = lerp(g, act(g, params.G.nonlin, params.G.thresh), 0.5);
      b = lerp(b, act(b, params.B.nonlin, params.B.thresh), 0.5);
      a = lerp(a, act(a, params.A.nonlin, params.A.thresh), 0.5);

      // memory (EMA)
      memBuf[i  ] = lerp(memBuf[i  ], r, memoryMix.value);
      memBuf[i+1] = lerp(memBuf[i+1], g, memoryMix.value);
      memBuf[i+2] = lerp(memBuf[i+2], b, memoryMix.value);
      memBuf[i+3] = lerp(memBuf[i+3], a, memoryMix.value);

      r = lerp(r, memBuf[i  ], 0.25);
      g = lerp(g, memBuf[i+1], 0.25);
      b = lerp(b, memBuf[i+2], 0.25);
      a = lerp(a, memBuf[i+3], 0.25);

      bufB[i  ] = clamp01(r);
      bufB[i+1] = clamp01(g);
      bufB[i+2] = clamp01(b);
      bufB[i+3] = clamp01(a);
    }
  }
  // swap
  const t = bufA; bufA = bufB; bufB = t;
}

/* ——— render ——— */
let needsRender = true;
function requestRender(){ needsRender = true; }
function render(){
  const c = canvas.value!, context = ctx.value!;
  context.save();
  // clear
  context.fillStyle = '#0b0c0f';
  context.fillRect(0,0,c.width,c.height);

  // world transform
  context.translate(c.width/2, c.height/2);
  context.scale(zoom.value, zoom.value);
  context.translate(-camX.value, -camY.value);

  // write pixels
  const img = context.createImageData(worldW, worldH);
  const data = img.data;

  for (let i=0, j=0; i<bufA.length; i+=4, j+=4){
    const R = bufA[i  ], G = bufA[i+1], B = bufA[i+2], A = bufA[i+3];
    const mR = memBuf[i  ], mG = memBuf[i+1], mB = memBuf[i+2];
    const glow = 0.20;
    const r = clamp01(lerp(R, mR, glow));
    const g = clamp01(lerp(G, mG, glow));
    const b = clamp01(lerp(B, mB, glow));
    const br = 0.6 + 0.6*A;
    data[j  ] = Math.floor(255 * clamp01(r * br));
    data[j+1] = Math.floor(255 * clamp01(g * br));
    data[j+2] = Math.floor(255 * clamp01(b * br));
    data[j+3] = 255;
  }

  // NN upscale
  const off = makeOffscreen(worldW, worldH) as any;
  const octx = off.getContext('2d')!;
  octx.putImageData(img, 0, 0);
  context.imageSmoothingEnabled = false;
  context.drawImage(off, 0,0, worldW, worldH);

  // stamp/grid overlay
  if (showStampGrid.value){
    context.strokeStyle = 'rgba(255,255,255,0.06)';
    context.lineWidth = 1 / zoom.value;
    const g = gridSize.value | 0;
    for (let x=0; x<=worldW; x+=g){ context.beginPath(); context.moveTo(x,0); context.lineTo(x,worldH); context.stroke(); }
    for (let y=0; y<=worldH; y+=g){ context.beginPath(); context.moveTo(0,y); context.lineTo(worldW,y); context.stroke(); }
  }

  context.restore();
  needsRender = false;
}

/* ——— main loop ——— */
function tick(ts:number){
  const dt = Math.max(0, ts - lastTickMs);
  lastTickMs = ts;
  frameCounter++; frameTimeAcc += dt;
  if (frameTimeAcc >= 500){
    fps.value = frameCounter * 1000 / frameTimeAcc;
    frameCounter = 0; frameTimeAcc = 0;
  }

  const steps = Math.max(1, Math.round(ticksPerSecond.value/60));
  if (running.value){
    for (let k=0;k<steps;k++){
      step();             // field
      worldTickAgents();  // life
    }
    needsRender = true;
  }

  if (needsRender) render();
  rafId = requestAnimationFrame(tick);
}

function toggleRun(){
  running.value = !running.value;
}

function stepOnce(){
  // one manual step regardless of running state
  step();             // field engine
  worldTickAgents();  // life layer
  requestRender();
}

/* ——— screenshots ——— */
function saveScreenshot(){
  if(!canvas.value) return;
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

/* ——— presets IO ——— */
const PRESET_KEY = 'bbyworld.presets.v1';
const presetName = ref<string>('');
const selectedPreset = ref<string>('');
const presetMap = reactive<Record<string, any>>(JSON.parse(localStorage.getItem(PRESET_KEY)||'{}'));
const presetKeys = computed(()=> Object.keys(presetMap).sort());

function snapState(){
  return {
    boardSize: boardSize.value,
    params: JSON.parse(JSON.stringify(params)),
    crosstalk: JSON.parse(JSON.stringify(crosstalk)),
    memoryMix: memoryMix.value,
    weatherStrength: weatherStrength.value,
    weatherEnabled: weatherEnabled.value,
    ticksPerSecond: ticksPerSecond.value,
    life: {
      enableAgents: enableAgents.value,
      agentsDeposit: agentsDeposit.value,
      agentsErode: agentsErode.value,
      agentsHunt: agentsHunt.value
    }
  };
}
function applyState(s:any){
  if (!s) return;
  if (s.boardSize && s.boardSize!==boardSize.value){ boardSize.value = s.boardSize; rebuildWorld(); }
  Object.assign(params.R, s.params?.R||{});
  Object.assign(params.G, s.params?.G||{});
  Object.assign(params.B, s.params?.B||{});
  Object.assign(params.A, s.params?.A||{});
  (['R','G','B'] as RGBCh[]).forEach(row=>{
    if (s.crosstalk && s.crosstalk[row]) Object.assign(crosstalk[row], s.crosstalk[row]);
  });
  if (typeof s.memoryMix==='number') memoryMix.value = s.memoryMix;
  if (typeof s.weatherStrength==='number') weatherStrength.value = s.weatherStrength;
  if (typeof s.weatherEnabled==='boolean') weatherEnabled.value = s.weatherEnabled;
  if (typeof s.ticksPerSecond==='number') ticksPerSecond.value = s.ticksPerSecond;
  if (s.life){
    if (typeof s.life.enableAgents==='boolean') enableAgents.value = s.life.enableAgents;
    if (typeof s.life.agentsDeposit==='boolean') agentsDeposit.value = s.life.agentsDeposit;
    if (typeof s.life.agentsErode==='boolean') agentsErode.value = s.life.agentsErode;
    if (typeof s.life.agentsHunt==='boolean') agentsHunt.value = s.life.agentsHunt;
  }
  requestRender();
}
function savePreset(){
  const name = (presetName.value||'preset').trim();
  if (!name) return;
  presetMap[name] = snapState();
  localStorage.setItem(PRESET_KEY, JSON.stringify(presetMap));
  presetName.value = '';
}
function loadPreset(){ if (!selectedPreset.value) return; applyState(presetMap[selectedPreset.value]); }
function deletePreset(){ if (!selectedPreset.value) return; delete presetMap[selectedPreset.value]; localStorage.setItem(PRESET_KEY, JSON.stringify(presetMap)); selectedPreset.value = ''; }
function exportPreset(){
  const blob = new Blob([JSON.stringify(snapState(), null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.download = `bbyWorld_preset_${Date.now()}.json`;
  a.href = URL.createObjectURL(blob);
  a.click();
}
function importPreset(e:Event){
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0]; if (!file) return;
  const fr = new FileReader();
  fr.onload = ()=> { try{ const s = JSON.parse(String(fr.result)); applyState(s); } catch(err){ console.error('bad preset json', err); } };
  fr.readAsText(file);
}

/* ——— lifecycle ——— */
onMounted(async ()=>{
  window.addEventListener('resize', resizeCanvas);
  rebuildWorld();
  resizeCanvas();
  resetView();
  await refreshStamps();
  rafId = requestAnimationFrame(tick);

  // gentle baby weather
  const wTimer = setInterval(pollWeather, 1200);
  (window as any).__bbyWeatherTimer = wTimer;

  // touch handlers only if enabled (off by default)
  if (allowTouchPanZoom.value){
    // you can wire legacy gestures here if you want behind the toggle
  }
});
onBeforeUnmount(()=>{
  cancelAnimationFrame(rafId);
  window.removeEventListener('resize', resizeCanvas);
  if ((window as any).__bbyWeatherTimer) clearInterval((window as any).__bbyWeatherTimer);
});

</script>

<style scoped>
.page-container { display:flex; flex-direction:column; width:100%; height:var(--full-height); padding:var(--padding); box-sizing:border-box; overflow:hidden; }
.main { display:grid; grid-template-columns: 320px 1fr; gap: var(--spacing); width:100%; height:100%; }

/* left column: panels */
.left { display:flex; flex-direction:column; gap: var(--spacing); overflow:auto; padding-right:2px; }
.panel, .presets { background: var(--panel-colour); border: var(--border); border-radius: var(--border-radius); padding: var(--padding); box-shadow: var(--box-shadow); }
.panel h3 { margin:0 0 8px; font-size: var(--font-size); color: var(--font-colour); }
.grid2 { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: var(--spacing); }
.col { background: var(--bby-colour-dark); border: 1px solid var(--bby-colour-black); border-radius: 8px; padding: 8px; }
.row { display:flex; gap: 8px; align-items:center; flex-wrap:wrap; }

.stamp-list { display:grid; grid-template-columns: repeat(auto-fill, minmax(120px,1fr)); gap:8px; max-height: 40vh; overflow:auto; }
.stamp { display:flex; flex-direction:column; gap:4px; background:var(--bby-colour-black); border:1px solid var(--bby-colour-dark); border-radius:8px; padding:6px; cursor:pointer; }
.stamp.sel { outline:2px solid var(--bby-colour); }
.stamp img { width:100%; image-rendering:pixelated; border-radius:4px; border:1px solid var(--bby-colour-dark); background:var(--bby-colour-black); }
.stamp .lab { color: var(--font-colour); font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.stamp .sub { color: #9db2d1; font-size:11px; opacity:0.9; }

.right { display:flex; flex-direction:column; gap: var(--spacing); min-width: 0; align-items: start; }
.canvas-wrap {
  position:relative;
  flex:1;
  min-height: 320px;
  background: var(--bby-colour-black);
  border: var(--border);
  border-radius: var(--border-radius);
  overflow:hidden;
  aspect-ratio: 1 / 1;  /* square screen */
  align-self: start;
}
.canvas-wrap canvas { display:block; width:100%; height:100%; image-rendering: pixelated; cursor: crosshair; }

.scope-rect {
  position:absolute;
  border:2px dashed rgba(255,255,255,0.6);
  background: rgba(255,255,255,0.06);
  pointer-events:none;
}
.legend {
  position:absolute; left:6px; top:6px;
  display:flex; flex-direction:column; gap:2px;
  font-size: 11px; line-height: 1.15;
  background: rgba(0,0,0,0.45);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius:6px; padding:4px 6px; pointer-events:none;
}
.legend-row { display:flex; gap:8px; align-items:center; color: #dbe7ff; }
.pill {
  background: var(--bby-colour-dark);
  color: var(--font-colour);
  padding: 0 4px;
  border-radius: 4px;
  font-weight: 800;
  font-size: 0.70rem;
}
.groups { display:grid; gap:6px; }
.ghead, .grow { display:grid; grid-template-columns: 1fr 60px 44px 80px 70px 80px; gap:8px; align-items:center; }
.colour-cell { display:flex; align-items:center; gap:6px; }
.colour-swatch { width:14px; height:14px; border-radius:3px; border:1px solid rgba(255,255,255,.2); }

input[type="range"] { width:120px; accent-color: var(--bby-colour); }
select, input[type="text"] { background: var(--bby-colour-black); border: 1px solid var(--bby-colour-dark); color: var(--font-colour); border-radius:6px; padding:6px 8px; }
label.import input { display:none; }
</style>