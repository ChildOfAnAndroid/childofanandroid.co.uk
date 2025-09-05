<!-- CHARIS CAT // bbyWorld — 2025 (The Definitive Hybrid Engine v7.1) -->
<template>
  <div class="page-container bbyworld-page">
    <div class="world-layout">
      <div class="world-left">
        <div class="vertical-panel">
          <h1 class="page-title">bbyWorld</h1>
          <h2 class="subtitle">The Engine of Emergence</h2>

          <!-- WORLD CONTROLS -->
          <div class="grp">
            <label class="section">world</label>
            <div class="row2">
              <input id="board-size" type="number" v-model.number="boardSize" min="32" step="16" title="Board Size" />
              <button class="action" @click="clearWorld">clear</button>
            </div>
          </div>
          
          <!-- PLACEMENT CONTROLS -->
          <div class="grp">
            <label class="section">select a cell stamp to place:</label>
            <div class="card-swatch-bar">
              <button v-for="card in cards" :key="card.label" class="card-swatch" :class="{ selected: selectedCardLabel?.toLowerCase() === card.label.toLowerCase() }" @click="selectCard(card.label)">
                <img :src="card.stamp_url || card.url" :alt="card.label" />
              </button>
            </div>
          </div>

          <!-- STATS -->
          <div class="grp">
            <label class="section">stats</label>
            <div class="world-stats">
              <span>TIME: {{ elapsedTimeDisplay }} | AETHER: <span :style="{color: aetherColor}">{{ aetherState }}</span></span>
              <span>CELLS: {{ livingCells.length }} | AVG LIFE: {{ avgLifespan }}</span>
              <br><span>--BIRTHS & DEATHS--</span>
              <span>REPRODUCTIONS: {{ stats.reproductions }}</span>
              <span>WAR: {{ stats.warDeaths }} | SQUISH: {{ stats.squishDeaths }} | FADE: {{ stats.fadedDeaths }}</span>
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
                <span>str</span>
              </div>
              <div class="group-row" v-for="g in sortedGroupStats" :key="g.colour" :class="{selected: highlightedGroup === g.colour}" @click="selectGroup(g.colour)">
                <div class="group-bar" :style="{ background: g.colour, width: g.percentage + '%' }"></div>
                <span class="colour-cell"><span class="colour-swatch" :style="{ background: g.colour }"></span> {{ g.colour }}</span>
                <span>{{ g.percentage.toFixed(1) }}%</span><span>{{ formatTicks(g.avgAge) }}</span>
                <span>{{ g.avgEnergy.toFixed(1) }}</span><span>{{ g.avgStrength.toFixed(2) }}</span>
              </div>
            </div>
          </div>

           <!-- ADJUSTABLE LAWS -->
          <div class="grp params-container">
            <details open>
              <summary class="section">Color Physics & Synergies</summary>
              <div class="params-grid">
                <label><span class="p-swatch" style="background:red;"></span>Red Fuel Conversion</label>
                <input type="range" v-model.number="params.redFuelConversion" min="5" max="50" step="1" /><span>x{{ params.redFuelConversion }}</span>
                <label><span class="p-swatch" style="background:red;"></span>Red Bake Rate</label>
                <input type="range" v-model.number="params.redBakeRate" min="0" max="0.1" step="0.005" /><span>+{{ params.redBakeRate.toFixed(3) }}</span>
                <label><span class="p-swatch" style="background:green;"></span>Green Crowd Penalty</label>
                <input type="range" v-model.number="params.greenCrowdPenalty" min="0" max="5" step="0.1" /><span>-{{ params.greenCrowdPenalty.toFixed(1) }}</span>
                <label><span class="p-swatch" style="background:blue;"></span>Blue Erosion Rate</label>
                <input type="range" v-model.number="params.blueErosionRate" min="0" max="0.1" step="0.005" /><span>-{{ params.blueErosionRate.toFixed(3) }}</span>
                <label><span class="p-swatch" style="background:blue;"></span>Blue Hydrodynamics</label>
                <input type="range" v-model.number="params.blueHydrodynamics" min="0" max="5" step="0.1" /><span>x{{ params.blueHydrodynamics.toFixed(1) }}</span>
                <label><span class="p-swatch" style="background:#555;"></span>Animal Gift Amount</label>
                <input type="range" v-model.number="params.animalGiftAmount" min="0" max="20" step="1" /><span>{{ params.animalGiftAmount }}</span>
                <label><span class="p-swatch" style="background:yellow;"></span>Yellow Light Boost</label>
                <input type="range" v-model.number="params.yellowLightBoost" min="0" max="0.5" step="0.01" /><span>+{{ params.yellowLightBoost.toFixed(2) }}</span>
                <label><span class="p-swatch" style="background:magenta;"></span>Magenta Steam Power</label>
                <input type="range" v-model.number="params.magentaSteamPower" min="0" max="3" step="0.1" /><span>x{{ params.magentaSteamPower.toFixed(1) }}</span>
                <label><span class="p-swatch" style="background:cyan;"></span>Cyan Growth Power</label>
                <input type="range" v-model.number="params.cyanGrowthPower" min="0" max="3" step="0.1" /><span>x{{ params.cyanGrowthPower.toFixed(1) }}</span>
              </div>
            </details>

            <details>
              <summary class="section">Life Stages & Behavior</summary>
              <div class="params-grid">
                <label>Adolescent Age</label>
                <input type="range" v-model.number="params.adolescentAge" min="50" max="500" step="10" /><span>{{ formatTicks(params.adolescentAge) }}</span>
                <label>Adult Age</label>
                <input type="range" v-model.number="params.adultAge" min="200" max="2000" step="20" /><span>{{ formatTicks(params.adultAge) }}</span>
                <label>Elder Age</label>
                <input type="range" v-model.number="params.elderAge" min="1000" max="5000" step="50" /><span>{{ formatTicks(params.elderAge) }}</span>
                <label>Teen Speed Bonus</label>
                <input type="range" v-model.number="params.teenSpeedBonus" min="1" max="3" step="0.1" /><span>x{{ params.teenSpeedBonus.toFixed(1) }}</span>
                <label>Teen Aggression</label>
                <input type="range" v-model.number="params.teenAggroBonus" min="1" max="3" step="0.1" /><span>x{{ params.teenAggroBonus.toFixed(1) }}</span>
              </div>
            </details>

            <details>
              <summary class="section">Metaphysics & Physics</summary>
              <div class="params-grid">
                 <label><span class="p-swatch" style="background:red;"></span>Aether Charge Rate</label>
                <input type="range" v-model.number="params.aetherChargeRate" min="0" max="0.01" step="0.0005" /><span>+{{ params.aetherChargeRate.toFixed(4) }}</span>
                <label><span class="p-swatch" style="background:blue;"></span>Aether Calm Rate</label>
                <input type="range" v-model.number="params.aetherCalmRate" min="0" max="0.01" step="0.0005" /><span>-{{ params.aetherCalmRate.toFixed(4) }}</span>
                 <label><span class="p-swatch" style="background:purple;"></span>Aether Aggro Effect</label>
                <input type="range" v-model.number="params.aetherAggroInfluence" min="0" max="2" step="0.1" /><span>x{{ params.aetherAggroInfluence.toFixed(1) }}</span>
                 <label><span class="p-swatch" style="background:purple;"></span>Aether Insanity Chance</label>
                <input type="range" v-model.number="params.aetherInsanityChance" min="0" max="0.001" step="0.00005" /><span>{{ (params.aetherInsanityChance*100).toFixed(3) }}%</span>
                <label>Reputation Decay</label>
                <input type="range" v-model.number="params.reputationDecay" min="0.9" max="0.999" step="0.001" /><span>x{{ params.reputationDecay.toFixed(3) }}</span>
                <label>Reputation Pacify</label>
                <input title="How much high reputation reduces the chance of being attacked." type="range" v-model.number="params.reputationPacify" min="0" max="1" step="0.05" /><span>-{{ (params.reputationPacify*100).toFixed(0) }}%</span>
                <label>Terrain Dye Rate</label>
                <input type="range" v-model.number="params.dyeDepositRate" min="0" max="5" step="0.1" /><span>x{{ params.dyeDepositRate.toFixed(1) }}</span>
                <label>Heavy Roll Chance</label>
                <input type="range" v-model.number="params.heavyRollChance" min="0" max="0.5" step="0.01" /><span>{{ (params.heavyRollChance*100).toFixed(0) }}%</span>
                <label>Energy Share Threshold</label>
                <input type="range" v-model.number="params.energyShareThreshold" min="10" max="150" step="5" /><span>{{ params.energyShareThreshold }}</span>
              </div>
            </details>
            
            <details>
              <summary class="section">Genetics & Evolution</summary>
              <div class="params-grid">
                <label>Dominance Penalty</label>
                <input type="range" v-model.number="params.dominancePenalty" min="0" max="0.5" step="0.05" /><span>{{ params.dominancePenalty.toFixed(2) }}</span>
                <label>Genetic Drift</label>
                <input type="range" v-model.number="params.geneticDrift" min="0" max="30" step="1" /><span>+/-{{ params.geneticDrift }}</span>
              </div>
            </details>
          </div>

          <!-- SELECTED CELL INFO -->
          <div class="grp" v-if="selectedCell">
            <label class="section">cell {{ selectedCell.id }} info</label>
            <div class="cell-stats">
              <div>pos: {{ selectedCell.x }}, {{ selectedCell.y }} | age: {{ formatTicks(selectedCell.age) }} ({{ selectedCell.lifeStage }})</div>
              <div>lifespan: {{ formatTicks(selectedCell.lifespan) }} | reputation: {{ selectedCell.reputation.toFixed(2) }} {{ selectedCell.isInsane ? ' (INSANE)' : ''}}</div>
              <div>energy: {{ selectedCell.energy.toFixed(1) }} | charge: {{ selectedCell.charge.toFixed(1) }} | aggr: {{ selectedCell.aggression.toFixed(2) }}</div>
              <div>cargo: {{ selectedCell.cargo.toFixed(1) }} | strength: {{ selectedCell.strength.toFixed(2) }}</div>
            </div>
             <label class="section">cell {{ selectedCell.id }} family</label>
            <FamilyTree :family="selectedFamily" :select-cell="selectCellById" />
          </div>
          
          <!-- VIEW CONTROLS -->
          <div class="grp">
            <label class="section">speed ({{ ticksPerSecond }} TPS)</label>
            <div class="row2"><button class="action" @click="slowDown">-</button><button class="action" @click="speedUp">+</button></div>
          </div>
          <div class="grp">
            <label class="section">zoom</label>
            <div class="row3"><button class="action" @click="zoomOut">-</button><div class="zoom-display">{{ (totalScale*100/baseScale).toFixed(0) }}%</div><button class="action" @click="zoomIn">+</button></div>
            <button class="action" @click="scopeActive = !scopeActive" :class="{active: scopeActive}">scope</button>
            <button class="action" @click="resetView">reset view</button>
          </div>
        </div>
      </div>

      <!-- WORLD VIEW -->
      <div class="world-right">
        <div class="world-stage" ref="stageEl" @mousedown="startPan" @mousemove="onMouseMove" @mouseup="endPan" @mouseleave="endPan" @wheel.prevent="onWheelZoom" @contextmenu.prevent >
          <div class="stack">
            <canvas ref="gameCanvas" :width="boardSize" :height="boardSize" @click="handleCanvasClick" :style="canvasStyle" />
            <div v-show="scopeActive" ref="scopeBox" class="zoom-scope">
              <canvas ref="scopeCanvas"></canvas>
              <div class="scope-info">
                <div>{{ hoverInfo.x }},{{ hoverInfo.y }} | Solid: {{ hoverInfo.solid.toFixed(2) }}</div>
                <div>H:{{ hoverInfo.heat.toFixed(2) }} M:{{ hoverInfo.moisture.toFixed(2) }} N:{{ hoverInfo.nutrient.toFixed(2) }}</div>
                <div>Ψ:{{ hoverInfo.psi.toFixed(2) }} Λ:{{ hoverInfo.lam.toFixed(2) }} Σ:{{ hoverInfo.sig.toFixed(2) }}</div>
                <div v-if="hoverInfo.cell">Cell {{ hoverInfo.cell.id }} | E:{{ hoverInfo.cell.energy.toFixed(0) }} C:{{ hoverInfo.cell.charge.toFixed(0) }}</div>
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
import { usePanZoom } from '@/composables/usePanZoom';
import { luminance, colourGroupKey } from '@/utils/colourEngine';
import { formatTicks as baseFormatTicks } from '@/utils/time';
import FamilyTree from '@/components/familyTree.vue';
import { rand, seedRand } from '@/utils/rng';
import { useSimulationSpeed } from '@/composables/useSimulationSpeed';
import { resolveCardLabel } from '@/utils/cards';

// --- TIME & FORMATTING ---
const TICKS_PER_DAY=100, DAYS_PER_YEAR=365;
const formatTicks=(ticks:number)=>baseFormatTicks(ticks, TICKS_PER_DAY, DAYS_PER_YEAR);

// --- UI STATE ---
const boardSize=ref<number>(128); function S(){return boardSize.value;}
const gameCanvas=ref<HTMLCanvasElement|null>(null), stageEl=ref<HTMLDivElement|null>(null);
const scopeCanvas=ref<HTMLCanvasElement|null>(null), scopeBox=ref<HTMLDivElement|null>(null);
const scopeActive=ref(false);
let lastMouseEvent:MouseEvent|null=null;
const { fetchBbyBookGallery }=bbyUse();
const cards=ref<{label:string; url:string; stamp_url?:string}[]>([]);
const selectedCardLabel=ref<string|null>(null);
let loadedImageData:ImageData|null=null;

// --- ADJUSTABLE PARAMETERS ---
const params = reactive({
    redFuelConversion: 25, redBakeRate: 0.01,
    greenCrowdPenalty: 2.0,
    blueErosionRate: 0.01, blueHydrodynamics: 2.0,
    animalGiftAmount: 10, yellowLightBoost: 0.1,
    magentaSteamPower: 1.5, cyanGrowthPower: 1.5,
    heavyRollChance: 0.1, energyShareThreshold: 50, reputationDecay: 0.995, reputationPacify: 0.5,
    dominancePenalty: 0.1, geneticDrift: 12,
    adolescentAge: 200, adultAge: 1000, elderAge: 3000,
    teenSpeedBonus: 1.5, teenAggroBonus: 1.5,
    aetherChargeRate: 0.001, aetherCalmRate: 0.001, aetherAggroInfluence: 1.0, aetherInsanityChance: 0.0001,
    dyeDepositRate: 1.0,
});

// =======================================================================
// ==================== HYBRID SIMULATION CORE v7 ========================
// =======================================================================
type LifeStage = 'INFANT' | 'ADOLESCENT' | 'ADULT' | 'ELDER';
type Heading = 0|1|2|3; const HEADING_VECS: [number,number][] = [[1,0],[-1,0],[0,1],[0,-1]];
type Cell = {
  id: number; r: number; g: number; b: number; a: number;
  x: number; y: number; alive: boolean; birthTick: number; age: number;
  energy: number; charge: number; aggression: number; baseAggression: number; fertility: number;
  metabolism: number; strength: number; speed: number; heading: Heading;
  lifespan: number; cargo: number; friends: Record<number, number>; decayRate: number;
  parents: number[]; lifeStage: LifeStage; reputation: number; isInsane: boolean;
};
type DeathReason = "war" | "squish" | "fade";

// --- WORLD STATE ---
const livingCells = ref<Cell[]>([]);
let nextCellId = 1; const cellById: Record<number, Cell> = {};
const familyTree: Record<number, { parents: number[], children: number[] }> = {};
let spatialMap: (Cell | null)[] = []; let tickCount = ref(0);
const stats = ref({ warDeaths: 0, squishDeaths: 0, fadedDeaths: 0, reproductions: 0, totalLifespan: 0, deadCount: 0 });
let heatField=new Float32Array(0), moistureField=new Float32Array(0), nutrientField=new Float32Array(0), solidGrid=new Float32Array(0);
let fieldPsi=new Float32Array(0), fieldLam=new Float32Array(0), fieldSig=new Float32Array(0);
let dyeRField=new Float32Array(0), dyeGField=new Float32Array(0), dyeBField=new Float32Array(0);
const aetherCharge = ref(0);
let frame=new Uint8ClampedArray(0), frameImg:ImageData|null=null;
seedRand(Date.now());
const p: number[] = []; for(let i=0; i<512; i++) p[i] = Math.floor(rand()*256);
const perm = [...p, ...p];
const fade = (t: number) => t*t*t*(t*(t*6-15)+10); const lerp = (t:number,a:number,b:number) => a+t*(b-a);
const grad = (hash:number,x:number,y:number) => {const h=hash&15,u=h<8?x:y,v=h<4?y:h===12||h===14?x:0; return ((h&1)===0?u:-u)+((h&2)===0?v:-v);};
function perlinNoise(x:number,y:number){const X=Math.floor(x)&255,Y=Math.floor(y)&255; x-=Math.floor(x); y-=Math.floor(y); const u=fade(x),v=fade(y); const A=perm[X]+Y,B=perm[X+1]+Y; return lerp(v,lerp(u,grad(perm[A],x,y),grad(perm[B],x-1,y)),lerp(u,grad(perm[A+1],x,y-1),grad(perm[B+1],x-1,y-1)));}

const VISIBLE_ALPHA=20, FERTILITY_ALPHA_MIN=0.3, FERTILITY_ALPHA_MAX=0.9, FERTILITY_ALPHA_PEAK=0.7;
const MIN_DECAY_RATE=0.05, MAX_DECAY_RATE=0.2;

/* ===================== Init / Resize / UI Functions ===================== */
function I(x:number, y:number): number { const s=S(); return ((x&(s-1))+(y&(s-1))*s)>>>0; }
function allocateWorldArrays(size:number){
  const len=size*size;
  heatField=new Float32Array(len); moistureField=new Float32Array(len); nutrientField=new Float32Array(len); solidGrid=new Float32Array(len);
  fieldPsi=new Float32Array(len); fieldLam=new Float32Array(len); fieldSig=new Float32Array(len);
  dyeRField=new Float32Array(len); dyeGField=new Float32Array(len); dyeBField=new Float32Array(len);
  spatialMap=new Array(len).fill(null);
  const ctx=gameCanvas.value?.getContext("2d",{willReadFrequently:true}); if(ctx){frameImg=ctx.createImageData(size,size); frame=frameImg.data;}
}
function clearWorld(){
  livingCells.value.length=0; spatialMap.fill(null);
  Object.keys(cellById).forEach(key=>delete cellById[Number(key)]); Object.keys(familyTree).forEach(key=>delete familyTree[Number(key)]);
  const s=S(); for(let y=0; y<s; y++) for(let x=0; x<s; x++){ const i=I(x,y); const n=(perlinNoise(x/(s/4),y/(s/4))+1)/2; solidGrid[i]=n>0.6?(n-0.6)*10:0; heatField[i]=0; moistureField[i]=0; nutrientField[i]=0; fieldPsi[i]=0; fieldLam[i]=0; fieldSig[i]=0; dyeRField[i]=0; dyeGField[i]=0; dyeBField[i]=0;}
  stats.value={warDeaths:0,squishDeaths:0,fadedDeaths:0,reproductions:0,totalLifespan:0,deadCount:0};
  tickCount.value=0; nextCellId=1; aetherCharge.value=0;
}
function applyBoardSize(){pan.value={x:0,y:0}; zoomFactor.value=1; const c=gameCanvas.value; if(c){c.width=S(); c.height=S();} allocateWorldArrays(S()); clearWorld(); computeBaseScale();}
const { ticksPerSecond, tickInterval, speedUp, slowDown } = useSimulationSpeed(30);
const { pan, baseScale, zoomFactor, totalScale, canvasStyle, zoomIn, zoomOut, resetView, startPan, onMouseMove: panZoomMouseMove, endPan, onWheelZoom, computeBaseScale } = usePanZoom(stageEl, boardSize, { maxZoom: 16 });
function onMouseMove(e:MouseEvent){ lastMouseEvent=e; panZoomMouseMove(e); }

/* ===================== Main Loop ===================== */
let animationFrameId:number|null=null, lastTime=0, timeSinceLastTick=0; const MAX_UPDATES_PER_FRAME=5;
function mainLoop(timestamp:number) {
  const ctx=gameCanvas.value?.getContext("2d"); if(!ctx){animationFrameId=requestAnimationFrame(mainLoop); return;}
  if(lastTime===0)lastTime=timestamp; const deltaTime=timestamp-lastTime; lastTime=timestamp; timeSinceLastTick+=deltaTime;
  const interval=tickInterval.value; let performed=0; while(timeSinceLastTick>=interval&&performed<MAX_UPDATES_PER_FRAME){update(); timeSinceLastTick-=interval; performed++;}
  if(performed===MAX_UPDATES_PER_FRAME)timeSinceLastTick=0;
  drawGrid(ctx); if(lastMouseEvent)updateScope(lastMouseEvent); animationFrameId=requestAnimationFrame(mainLoop);
}

/* ===================== Simulation Update ===================== */
function diffuse(field:Float32Array,mix:number,decay:number){const s=S(),tF=new Float32Array(field); for(let y=0;y<s;y++){for(let x=0;x<s;x++){const i=I(x,y); const n=(tF[I(x+1,y)]+tF[I(x-1,y)]+tF[I(x,y+1)]+tF[I(x,y-1)])*0.25; field[i]=(1-mix)*tF[i]+mix*n; field[i]*=decay;}}}

function update() {
  tickCount.value++;
  diffuse(heatField,0.2,0.996); diffuse(moistureField,0.3,0.997); diffuse(nutrientField,0.18,0.996);
  diffuse(fieldPsi,0.2,0.99); diffuse(fieldLam,0.2,0.99); diffuse(fieldSig,0.2,0.99);
  diffuse(dyeRField,0.1,0.999); diffuse(dyeGField,0.1,0.999); diffuse(dyeBField,0.1,0.999);
  aetherCharge.value*=0.995;

  const rankMap=new Map<string,number>(); sortedGroupStats.value.forEach((g,i)=>rankMap.set(g.colour,i));

  for(let i=livingCells.value.length-1; i>=0; i--){
    const c=livingCells.value[i]; if(!c.alive)continue; c.age++; updateLifeStage(c); c.reputation*=params.reputationDecay; const idx=I(c.x,c.y);

    c.energy-=c.metabolism+(c.aggression*0.05); c.a-=c.decayRate; c.strength=c.a/255;
    const nR=c.r/255, nG=c.g/255, nB=c.b/255;

    let energyGain=0;
    if(c.r>150&&nR>nG&&nR>nB){const f=Math.min(0.02*nR,nutrientField[idx]); nutrientField[idx]-=f; energyGain+=f*params.redFuelConversion; if(f===0)c.energy-=0.2; solidGrid[idx]=Math.min(6,solidGrid[idx]+params.redBakeRate); moistureField[idx]*=1-(params.redBakeRate*5); aetherCharge.value=Math.min(1,aetherCharge.value+params.aetherChargeRate*nR);}
    else{const gR=Math.min(heatField[idx],nR*0.1); heatField[idx]-=gR; const gG=Math.min(nutrientField[idx],nG*0.1); nutrientField[idx]-=gG; const gB=Math.min(moistureField[idx],nB*0.1); moistureField[idx]-=gB; energyGain+=(gR+gG+gB)*15;}
    c.energy=Math.min(255,c.energy+energyGain);
    const resonance=(fieldPsi[idx]*nR)+(fieldLam[idx]*nG)+(fieldSig[idx]*nB); c.charge=Math.min(255,c.charge+resonance*0.8-0.15);
    
    if(c.b>150&&nB>nR&&nB>nG){if(solidGrid[idx]>0){const e=Math.min(solidGrid[idx],params.blueErosionRate*nB); solidGrid[idx]-=e; nutrientField[idx]+=e*0.5; moistureField[idx]+=e*0.5;} aetherCharge.value=Math.max(-1,aetherCharge.value-params.aetherCalmRate*nB);}
    if(c.g>150&&nG>nR&&nG>nB){const n=countAdjacent(c.x,c.y); if(n>2)c.energy-=(n-2)*params.greenCrowdPenalty; else if(n<2)c.energy+=0.5;}
    if(c.g>200&&c.r>200&&c.b<100){for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){if(dx===0&&dy===0)continue; const n=spatialMap[I(c.x+dx,c.y+dy)]; if(n?.alive)n.energy=Math.min(255,n.energy+params.yellowLightBoost);}}
    if((c.r+c.g+c.b<100)||(c.r>150&&c.b>150&&c.g<100)){if(c.cargo<20&&nutrientField[idx]>0.01){const t=Math.min(0.05,nutrientField[idx]); nutrientField[idx]-=t; c.cargo+=t*50;} for(const[dx,dy]of HEADING_VECS){const n=spatialMap[I(c.x+dx,c.y+dy)]; if(n?.alive&&c.energy>n.energy+params.energyShareThreshold&&(c.friends[n.id]||0)>1){const xfer=Math.min(params.animalGiftAmount,c.energy-n.energy); n.energy+=xfer; c.energy-=xfer; adjustAffinity(c,n,0.5); break;}}}
    if(nR>0.3&&nB>0.3){const take=Math.min(0.01*Math.min(nR,nB),moistureField[idx]); moistureField[idx]-=take; heatField[idx]+=take*params.magentaSteamPower;}
    if(nG>0.3&&nB>0.3){const take=Math.min(0.01*Math.min(nG,nB),nutrientField[idx]); nutrientField[idx]-=take; moistureField[idx]+=take*params.cyanGrowthPower;}

    const influence=c.a/255*0.1; fieldPsi[idx]+=nR*influence; fieldLam[idx]+=nG*influence; fieldSig[idx]+=nB*influence;
    const dyeRate=params.dyeDepositRate; dyeRField[idx]=Math.min(255,dyeRField[idx]+c.r*dyeRate*0.01); dyeGField[idx]=Math.min(255,dyeGField[idx]+c.g*dyeRate*0.01); dyeBField[idx]=Math.min(255,dyeBField[idx]+c.b*dyeRate*0.01);

    if(aetherCharge.value > 0.8 && rand() < params.aetherInsanityChance) c.isInsane = true;
    if(c.a<VISIBLE_ALPHA||c.energy<=0||c.charge<=0){recordDeath(c,"fade"); continue;}
    
    let fert=0; if((c.lifeStage==='ADULT'||c.lifeStage==='ELDER')&&!c.isInsane){const ageF=Math.min(1,c.age/c.lifespan),alphaN=c.a/255; let fertA=0; if(alphaN>=FERTILITY_ALPHA_MIN&&alphaN<=FERTILITY_ALPHA_MAX){fertA=(alphaN<=FERTILITY_ALPHA_PEAK)?(alphaN-FERTILITY_ALPHA_MIN)/(FERTILITY_ALPHA_PEAK-FERTILITY_ALPHA_MIN):(FERTILITY_ALPHA_MAX-alphaN)/(FERTILITY_ALPHA_MAX-FERTILITY_ALPHA_PEAK);} const rank=rankMap.get(groupKey(c))??10; fert=ageF*fertA*(1.0-(rank*params.dominancePenalty));}
    c.fertility=fert;
  }
  
  for(const c of livingCells.value){if(c.strength>0.8&&solidGrid[I(c.x,c.y)]>2.5&&rand()<params.heavyRollChance){let b:[number,number]|null=null,l=solidGrid[I(c.x,c.y)]; for(const[dx,dy]of HEADING_VECS){const nI=I(c.x+dx,c.y+dy); if(!spatialMap[nI]&&solidGrid[nI]<l-0.5){l=solidGrid[nI];b=[c.x+dx,c.y+dy];}} if(b)performMove(c,b[0],b[1]);}}
  const updatesPerTick=Math.max(1,Math.floor(livingCells.value.length/50));
  for(let i=0;i<updatesPerTick;i++){const cell=livingCells.value[Math.floor(rand()*livingCells.value.length)]; if(cell?.alive)attemptMove(cell);}
}

function updateLifeStage(c:Cell){
  const s=c.lifeStage; if(c.age>params.elderAge)c.lifeStage='ELDER'; else if(c.age>params.adultAge)c.lifeStage='ADULT'; else if(c.age>params.adolescentAge)c.lifeStage='ADOLESCENT'; else c.lifeStage='INFANT';
  if(s===c.lifeStage)return; let aM=1.0,sM=1.0;
  if(c.lifeStage==='ADOLESCENT'){aM=params.teenAggroBonus; sM=params.teenSpeedBonus;} else if(c.lifeStage==='INFANT'||c.lifeStage==='ELDER'){sM=0.5;}
  c.aggression=c.baseAggression*aM*(1+aetherCharge.value*params.aetherAggroInfluence); c.speed=1+Math.floor((255-c.a)/85)*sM;
}

function makeCell(x:number,y:number,r:number,g:number,b:number,a:number,parentLifespan?:number,parents:number[]=[]): Cell{
  const A=Math.max(VISIBLE_ALPHA,a), strength=A/255; const lifespan=(parentLifespan||(TICKS_PER_DAY*10+rand()*TICKS_PER_DAY*20))+(rand()-0.5)*(TICKS_PER_DAY*5); const bA=(r/255)*1.2;
  const c:Cell={id:nextCellId++,r,g,b,a:A,x,y,alive:true,birthTick:tickCount.value,age:0,energy:120+strength*100,charge:120,aggression:bA,baseAggression:bA,fertility:0,metabolism:0.1+(g/255)*0.2,strength,speed:1,heading:Math.floor(rand()*4)as Heading,lifespan,cargo:0,friends:{},decayRate:MIN_DECAY_RATE+rand()*(MAX_DECAY_RATE-MIN_DECAY_RATE),parents,lifeStage:'INFANT',reputation:0,isInsane:false};
  cellById[c.id]=c; familyTree[c.id]={parents,children:[]}; if(parents.length===2){familyTree[parents[0]]?.children.push(c.id); familyTree[parents[1]]?.children.push(c.id);}
  return c;
}
function mergeBaby(p1:Cell,p2:Cell,x:number,y:number): Cell{
  const tS=p1.strength+p2.strength||1; const b=(c1:number,c2:number)=>{const avg=c1*(p1.strength/tS)+c2*(p2.strength/tS),d=(c1-c2)*(rand()*0.3-0.15); const m=params.geneticDrift; return Math.min(255,Math.max(0,Math.round(avg+d+(rand()*m-m/2))));}
  const baby=makeCell(x,y,b(p1.r,p2.r),b(p1.g,p2.g),b(p1.b,p2.b),255,(p1.lifespan+p2.lifespan)/2,[p1.id,p2.id]);
  p1.energy*=0.7; p2.energy*=0.7; stats.value.reproductions++; adjustAffinity(p1,p2,2); adjustAffinity(p1,baby,3); adjustAffinity(p2,baby,3); p1.reputation+=1; p2.reputation+=1;
  return baby;
}
function compatibility(a:Cell,b:Cell){const d=Math.hypot(a.r-b.r,a.g-b.g,a.b-b.b)/441; return 1-d;}
function adjustAffinity(a:Cell,b:Cell,d:number){const c=(v:number)=>Math.min(10,Math.max(-10,v)); a.friends[b.id]=c((a.friends[b.id]||0)+d); b.friends[a.id]=c((b.friends[a.id]||0)+d);}
function handleInteraction(attacker:Cell,defender:Cell){
  const aff=(attacker.friends[defender.id]||0)+(defender.friends[attacker.id]||0); const pR=attacker.fertility*defender.fertility*(1-compatibility(attacker,defender));
  if(pR>0.1&&aff>-2&&attacker.energy>80&&defender.energy>80){const s=findEmptyAdjacent(attacker.x,attacker.y); if(s){const b=mergeBaby(attacker,defender,s.x,s.y); livingCells.value.push(b); spatialMap[I(b.x,b.y)]=b;}}
  else{const pacifism = Math.max(0, defender.reputation * params.reputationPacify); const aS=(attacker.energy+attacker.charge)*attacker.aggression * (1-pacifism),dS=(defender.energy+defender.charge)*(1+defender.strength-attacker.strength); if(aS>dS){attacker.energy=Math.min(255,attacker.energy+defender.energy*0.5); recordDeath(defender,"war"); attacker.reputation-=.5;} else {defender.energy=Math.min(255,defender.energy+attacker.energy*0.5); recordDeath(attacker,"war"); defender.reputation-=.5;} adjustAffinity(attacker,defender,-1.5);}
}
function recordDeath(c:Cell,reason:DeathReason){
  if(!c.alive)return; c.alive=false; const idx=I(c.x,c.y);
  nutrientField[idx]+=(c.energy/255)*0.5+(c.g/255)*0.2+c.cargo*0.01; heatField[idx]+=(c.energy/255)*0.2+(c.r/255)*0.2; solidGrid[idx]=Math.min(6,solidGrid[idx]+c.strength*0.5); spatialMap[idx]=null;
  stats.value[reason==="squish"?"squishDeaths":reason==="fade"?"fadedDeaths":"warDeaths"]++; stats.value.deadCount++; stats.value.totalLifespan+=c.age;
  const i=livingCells.value.findIndex(cell=>cell.id===c.id); if(i>-1)livingCells.value.splice(i,1);
}
function attemptMove(c:Cell){
  const isGas=c.r>200&&c.g>200&&c.b>200, isWater=c.b>150&&c.b>c.r&&c.b>c.g; let bestScore=-Infinity, bestDir:[number,number]|null=null;
  const dirs=[[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,1]].sort(()=>rand()-0.5);
  for(const[dx,dy]of dirs){
    const nx=c.x+dx,ny=c.y+dy,ni=I(nx,ny);
    let score=(heatField[ni]*(c.r/255)+nutrientField[ni]*(c.g/255)+moistureField[ni]*(c.b/255))*10;
    score+=(dyeRField[ni]*(c.r/255)+dyeGField[ni]*(c.g/255)+dyeBField[ni]*(c.b/255))*0.1;
    score-=solidGrid[ni]*(isGas?0.2:1.0); if(isWater)score-=solidGrid[ni]*params.blueHydrodynamics;
    const n=spatialMap[ni]; if(n){score-=(1-((n.friends[c.id]||0)+(n.reputation/10))/20); if(isGas)score+=2;}
    if(c.isInsane) score += rand()*5;
    if(score>bestScore){bestScore=score; bestDir=[dx,dy];}
  }
  if(bestDir){const[dx,dy]=bestDir,tX=(c.x+dx+S())%S(),tY=(c.y+dy+S())%S(),tC=spatialMap[I(tX,tY)]; if(!tC)performMove(c,tX,tY); else if(tC.alive){if(!c.isInsane&&!tC.isInsane&&(compatibility(c,tC)>0.7||(c.friends[tC.id]||0)>1))congaMove(c,dx,dy); else handleInteraction(c,tC);}}
}
function performMove(m:Cell,x:number,y:number){spatialMap[I(m.x,m.y)]=null; m.x=x; m.y=y; spatialMap[I(x,y)]=m;}
function congaMove(start:Cell,dx:number,dy:number):boolean{
  const chain:Cell[]=[start]; let current=start;
  for(let i=0;i<livingCells.value.length;i++){
    const nX=(current.x+dx+S())%S(), nY=(current.y+dy+S())%S(), nC=spatialMap[I(nX,nY)];
    if(!nC){for(let j=chain.length-1;j>=0;j--){const c=chain[j]; performMove(c,(c.x+dx+S())%S(),(c.y+dy+S())%S()); adjustAffinity(start,c,0.05);} return true;}
    if(nC.alive&&!nC.isInsane&&((start.friends[nC.id]||0)>1||compatibility(current,nC)>0.8)){chain.push(nC); current=nC;}
    else{const v=chain.length>1?chain[chain.length-1]:start; if(v.strength<nC.strength)recordDeath(v,"squish"); else recordDeath(nC,"squish"); return false;}
  }
  return false;
}
function findEmptyAdjacent(x:number,y:number):{x:number,y:number}|null{const d=[[0,1],[0,-1],[1,0],[-1,0]].sort(()=>rand()-0.5); for(const[dx,dy]of d){const nx=(x+dx+S())%S(),ny=(y+dy+S())%S(); if(spatialMap[I(nx,ny)]===null)return{x:nx,y:ny};} return null;}
function countAdjacent(x:number,y:number):number{let c=0; for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){if((dx!==0||dy!==0)&&spatialMap[I(x+dx,y+dy)])c++;} return c;}

/* ===================== Drawing & UI ===================== */
function drawGrid(ctx: CanvasRenderingContext2D){
  if(!frameImg)return; ctx.imageSmoothingEnabled=false; const s=S();
  for(let y=0;y<s;y++){for(let x=0;x<s;x++){const off=(x+y*s)*4,i=I(x,y); const rock=solidGrid[i]*30,heat=heatField[i]*50,nutr=nutrientField[i]*50,moist=moistureField[i]*50; const dyeA=Math.min(0.4,(dyeRField[i]+dyeGField[i]+dyeBField[i])/765); const bR=10+rock+heat,bG=10+rock+nutr,bB=10+rock+moist; frame[off]=Math.min(255,bR*(1-dyeA)+dyeRField[i]*dyeA); frame[off+1]=Math.min(255,bG*(1-dyeA)+dyeGField[i]*dyeA); frame[off+2]=Math.min(255,bB*(1-dyeA)+dyeBField[i]*dyeA); frame[off+3]=255;}}
  for(const c of livingCells.value){if(!c.alive)continue; const off=I(c.x,c.y)*4; if(c.isInsane){const grey=luminance(c); frame[off]=grey;frame[off+1]=grey;frame[off+2]=grey;}else{frame[off]=c.r;frame[off+1]=c.g;frame[off+2]=c.b;} frame[off+3]=c.a;}
  ctx.putImageData(frameImg,0,0);
}
let resizeObs:ResizeObserver|null=null;
onMounted(async()=>{try{const g=await fetchBbyBookGallery(); cards.value=g.map(c=>({label:c.factName,url:c.url,stamp_url:c.stamp_url})); if(cards.value.length>0)selectCard(cards.value[0].label);}catch(e){console.error("Failed to fetch gallery:",e);} applyBoardSize(); if(stageEl.value){resizeObs=new ResizeObserver(()=>computeBaseScale()); resizeObs.observe(stageEl.value);} if(scopeCanvas.value){scopeCanvas.value.width=256; scopeCanvas.value.height=256;} animationFrameId=requestAnimationFrame(mainLoop);});
onUnmounted(()=>{if(animationFrameId)cancelAnimationFrame(animationFrameId); if(resizeObs&&stageEl.value)resizeObs.disconnect();});
watch(boardSize,()=>applyBoardSize()); watch(selectedCardLabel,()=>loadSelectedImage());
function selectCard(label:string){
  selectedCardLabel.value = resolveCardLabel(cards.value, label);
  loadSelectedImage();
}
function loadSelectedImage(){
  const label=selectedCardLabel.value;
  const sel=label?cards.value.find(c=>c.label.toLowerCase()===label.toLowerCase()):undefined;
  if(!sel)return;
  selectedCardLabel.value=sel.label;
  const urls:string[]=[]; if(sel.stamp_url)urls.push(sel.stamp_url); urls.push(sel.url.replace(/\.png$/i,'.stamp.png')); urls.push(sel.url); const img=new Image(); img.crossOrigin="Anonymous"; let i=0;
  img.onload=()=>{const max=64, sc=Math.min(1,max/Math.max(img.width,img.height)), w=Math.max(1,Math.floor(img.width*sc)), h=Math.max(1,Math.floor(img.height*sc)); const can=document.createElement("canvas"), ctx=can.getContext("2d",{willReadFrequently:true})!; can.width=w; can.height=h; ctx.imageSmoothingEnabled=false; ctx.drawImage(img,0,0,w,h); loadedImageData=ctx.getImageData(0,0,w,h);};
  img.onerror=()=>{i++; if(i<urls.length){img.src=urls[i];}else{console.error("Failed to load stamp:",sel.label); loadedImageData=null;}}; img.src=urls[i];
}
function screenToWorld(e:MouseEvent):{x:number,y:number}|null{const c=gameCanvas.value; if(!c)return null; const r=c.getBoundingClientRect(), sc=c.width/r.width; return{x:Math.floor((e.clientX-r.left)*sc),y:Math.floor((e.clientY-r.top)*sc)};}
function handleCanvasClick(e:MouseEvent){const c=screenToWorld(e); if(!c)return; const cell=spatialMap[I(c.x,c.y)]; if(cell?.alive){selectedCell.value=cell;}else{placeImageAt(c.x,c.y);}}
function placeImageAt(wX:number,wY:number){if(!loadedImageData)return; const sX=wX-Math.floor(loadedImageData.width/2),sY=wY-Math.floor(loadedImageData.height/2); for(let y=0;y<loadedImageData.height;y++){for(let x=0;x<loadedImageData.width;x++){const i=(y*loadedImageData.width+x)*4,a=loadedImageData.data[i+3]; if(a>50){const pX=(sX+x+S())%S(),pY=(sY+y+S())%S(); if(!spatialMap[I(pX,pY)]){const[r,g,b]=[loadedImageData.data[i],loadedImageData.data[i+1],loadedImageData.data[i+2]]; const n=makeCell(pX,pY,r,g,b,a); livingCells.value.push(n); spatialMap[I(pX,pY)]=n;}}}}}
const elapsedTimeDisplay=computed(()=>formatTicks(tickCount.value));
const avgLifespan=computed(()=>stats.value.deadCount>0?formatTicks(stats.value.totalLifespan/stats.value.deadCount):"---");
const aetherState=computed(()=>{if(aetherCharge.value>0.5)return'FRENZIED'; if(aetherCharge.value<-0.5)return'CALM'; return'NEUTRAL';});
const aetherColor=computed(()=>{const v=Math.round(127+aetherCharge.value*127); return`rgb(${v},127,${255-v})`;});
const selectedCell=ref<Cell|null>(null); function selectCellById(id:number){const c=cellById[id]; if(c?.alive)selectedCell.value=c;}
const selectedFamily=computed(()=>{if(!selectedCell.value)return{parents:[],children:[]}; const e=familyTree[selectedCell.value.id]||{parents:[],children:[]}; return{parents:e.parents.map(id=>cellById[id]).filter((c):c is Cell=>!!c?.alive),children:e.children.map(id=>cellById[id]).filter((c):c is Cell=>!!c?.alive),};});
interface CGS{colour:string;count:number;percentage:number;avgAge:number;avgEnergy:number;avgStrength:number;}
function groupKey(c:Cell){return colourGroupKey(c.r,c.g,c.b);}
const groupStats=computed<CGS[]>(()=>{const b={count:0,totalAge:0,totalEnergy:0,totalStrength:0}; const g:Record<string,typeof b>={}; for(const c of livingCells.value){const k=groupKey(c); const gr=g[k]||(g[k]={...b}); gr.count++; gr.totalAge+=c.age; gr.totalEnergy+=c.energy; gr.totalStrength+=c.strength;} const t=livingCells.value.length; return Object.entries(g).map(([colour,grp])=>({colour,count:grp.count,percentage:t?(grp.count/t)*100:0,avgAge:grp.count?grp.totalAge/grp.count:0,avgEnergy:grp.count?grp.totalEnergy/grp.count:0,avgStrength:grp.count?grp.totalStrength/grp.count:0,}));});
const sortedGroupStats=computed(()=>[...groupStats.value].sort((a,b)=>b.count-a.count)); const highlightedGroup=ref<string|null>(null);
function selectGroup(c:string){highlightedGroup.value=highlightedGroup.value===c?null:c;}
const hoverInfo=ref({x:0,y:0,heat:0,moisture:0,nutrient:0,solid:0,psi:0,lam:0,sig:0,dyeR:0,dyeG:0,dyeB:0,cell:null as Cell|null});
const updateScope=throttle((e:MouseEvent)=>{if(!scopeActive.value)return; const s=scopeCanvas.value,b=scopeBox.value; if(!s||!b||!frameImg)return; const c=screenToWorld(e); if(!c)return; const hx=c.x,hy=c.y; const ctx=s.getContext('2d'); if(!ctx)return; const SS=9,h=Math.floor(SS/2),pS=s.width/SS,sz=S(); ctx.imageSmoothingEnabled=false; ctx.clearRect(0,0,s.width,s.height); for(let dy=0;dy<SS;dy++){for(let dx=0;dx<SS;dx++){const sx=hx-h+dx,sy=hy-h+dy; let r=0,g=0,bl=0,a=255; if(sx>=0&&sy>=0&&sx<sz&&sy<sz){const o=I(sx,sy)*4; r=frame[o];g=frame[o+1];bl=frame[o+2];a=frame[o+3];} ctx.fillStyle=`rgba(${r},${g},${bl},${a/255})`; ctx.fillRect(dx*pS,dy*pS,pS,pS);}} ctx.strokeStyle='#fff'; ctx.lineWidth=2; ctx.strokeRect(h*pS,h*pS,pS,pS); if(hx>=0&&hy>=0&&hx<sz&&hy<sz){const i=I(hx,hy); hoverInfo.value={x:hx,y:hy,heat:heatField[i],moisture:moistureField[i],nutrient:nutrientField[i],solid:solidGrid[i],psi:fieldPsi[i],lam:fieldLam[i],sig:fieldSig[i],dyeR:Math.round(dyeRField[i]),dyeG:Math.round(dyeGField[i]),dyeB:Math.round(dyeBField[i]),cell:spatialMap[i]||null};} const sr=stageEl.value?.getBoundingClientRect(); if(!sr)return; const bX=e.clientX-sr.left,bY=e.clientY-sr.top; const oX=(bX/sr.width<0.5)?20:-b.offsetWidth-20,oY=(bY/sr.height<0.5)?20:-b.offsetHeight-20; b.style.left=`${e.clientX+oX}px`; b.style.top=`${e.clientY+oY}px`;},16);
</script>

<style scoped>
.page-container { display:flex; width:100%; height:var(--full-height); box-sizing:border-box; padding:var(--padding); }
.world-layout{display:flex;flex-direction:row;width:100%;height:100%;gap:var(--spacing);overflow:hidden}
.world-left{flex:1 1 320px;min-width:320px;height:100%;display:flex;flex-direction:column}
.world-right{flex:0 1 var(--full-height);display:flex;align-items:center;justify-content:center;height:100%;max-width:var(--full-height);min-width:0;position:relative}
.vertical-panel{position:relative;width:100%;height:100%;overflow-y:auto;padding:var(--padding);background:var(--panel-colour);border:var(--border);border-radius:var(--border-radius);box-shadow:var(--box-shadow);display:flex;flex-direction:column;gap:calc(var(--spacing)*1.1)}
.vertical-panel h1{margin:0;text-align:center;line-height:1.05}
.subtitle { font-size: var(--small-font-size); text-align: center; opacity: 0.7; margin: -0.5rem 0 0.5rem; font-weight: normal; }
.world-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.group-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.group-row{display:grid;grid-template-columns: 2fr 1fr 1.5fr 1fr 1fr; gap:.25rem;position:relative;cursor:pointer; align-items: center;}
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
.section{font-size:var(--small-font-size);text-align:center;opacity:.85;letter-spacing:.1em;text-transform:uppercase; cursor: pointer;}
.action{display:block;width:100%;padding:.4rem .5rem;transition:all .2s ease-out;text-align:center}
.action.active,.action:active{background:var(--accent-hover);border-color:var(--accent-colour)!important}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:.5rem}
.row3{display:grid;grid-template-columns:1fr auto 1fr;gap:.5rem;align-items:center}
#board-size{width:100%;text-align:center}
.card-swatch-bar{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;}
.card-swatch{border:var(--border);padding:2px;background:var(--panel-colour);cursor:pointer}
.card-swatch img{height:32px; image-rendering:pixelated; display:block}
.card-swatch.selected{border-color:var(--accent-colour);background:var(--accent-hover)}
.cell-stats{display:flex;flex-direction:column;gap:.25rem;font-size:var(--small-font-size)}
.params-container { gap: 0.75rem; }
.params-container details { border: var(--border); border-radius: var(--border-radius-small); padding: 0.5rem; }
.params-container summary { padding-bottom: 0.5rem; font-weight: bold;}
.params-grid { display: grid; grid-template-columns: auto 1fr auto; gap: 0.5rem 0.75rem; align-items: center; font-size: var(--small-font-size); }
.params-grid label { text-align: right; display:flex; align-items:center; gap: 0.4rem; justify-content: flex-end;}
.params-grid input[type="range"] { width: 100%; }
.p-swatch { width: 0.6rem; height: 0.6rem; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.2); }
@media (max-width:720px){.world-layout{flex-direction:column}.world-left{width:100%;flex-basis:auto;height:auto}.vertical-panel{overflow-y:visible}.world-right{width:100%;max-width:none;flex:0 0 auto}}
</style>