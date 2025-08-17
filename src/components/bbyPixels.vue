<!-- CHARIS CAT // CHILD OF AN ANDROID - 2025 -->
<template>
  <div class="lab-wrap">
    <div ref="stack" class="stack">
      <BbySprite v-if="!isTestCanvas" ref="spriteComp" />
      <canvas ref="overlay" class="overlay"
        @pointerdown="onDown" @pointermove="onPointerMove"
        @pointerup="onUp" @pointerleave="onPointerLeave"></canvas>
    </div>
  </div>
</template>

<!-- In your bbyPixels.vue file -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, defineProps, defineExpose, computed, watch } from 'vue';
import { throttle } from 'lodash';
import BbySprite from '@/components/bbySprite.vue';
import { bbyUse } from '@/composables/bbyUse.ts';
import { stepColourOnce } from '@/utils/colourEngine';
import type { EQType, RgbColor } from '@/utils/colourEngine';

type RgbaColor = { r: number; g: number; b: number; a: number };
type Mode = 'paint' | 'blend' | 'erase' | 'eyedropper' | 'behind';
type StrokeState = { brushColor: RgbColor; };
let strokeState: StrokeState | null = null;
const props = defineProps<{ hexColor: string; mode: Mode; isScopeCursorActive: boolean; activeEQs: Set<EQType>; userSetColor: RgbColor; bbyColor: RgbColor; rainbowInfluence: number; userColorInfluence: number; bbyInfluence: number; redInfluence: number; greenInfluence: number; blueInfluence: number; tempo: number; blendOpacity: number; isTestCanvas?: boolean; spriteWidth?: number; spriteHeight?: number; resolution?: number; }>();
const emit = defineEmits(['color-picked', 'color-hovered']);

let SPRITE_W = 64, SPRITE_H = 64;
defineExpose({ clearOverlay, exportCanvas, exportCompositeCanvas });

const { bbyState, sendBbyPaintColour, paintOverlayData, sendPixelUpdate, tickPaint } = bbyUse();
const throttledReactionUpdate = throttle((r:number,g:number,b:number)=>sendBbyPaintColour(r,g,b),300);
let pixelUpdateBatch: {x:number,y:number,r:number,g:number,b:number,a:number}[] = [];
const throttledSendBatch = throttle(()=>{ if(pixelUpdateBatch.length){ sendPixelUpdate(pixelUpdateBatch); pixelUpdateBatch=[]; } },100);

const highlightedPixel = ref<{x:number,y:number}|null>(null);
let isDown=false; let octx:CanvasRenderingContext2D|null=null;
const spriteComp = ref<InstanceType<typeof BbySprite>|null>(null);
const overlay = ref<HTMLCanvasElement|null>(null);
const stack = ref<HTMLDivElement|null>(null);
let ro:ResizeObserver|null=null; const dpr = window.devicePixelRatio||1;
let paintedPixelsInStroke = new Set<string>();
const localPaintData = ref<ImageData | null>(null);
const currentPaintData = computed(() => props.isTestCanvas ? localPaintData.value : paintOverlayData.value);

let tmpCanvas: HTMLCanvasElement | null = null;
let tmpCtx: CanvasRenderingContext2D | null = null;
function ensureTmpCanvas(force=false) {
  if (!tmpCanvas || force || tmpCanvas.width !== SPRITE_W || tmpCanvas.height !== SPRITE_H) {
    tmpCanvas = document.createElement('canvas');
    tmpCanvas.width = SPRITE_W;
    tmpCanvas.height = SPRITE_H;
    tmpCtx = tmpCanvas.getContext('2d');
  }
}

function exportCanvas(): HTMLCanvasElement | null {
  ensureTmpCanvas();
  if (!tmpCanvas || !tmpCtx || !currentPaintData.value) return null;
  tmpCtx.clearRect(0, 0, SPRITE_W, SPRITE_H);
  tmpCtx.putImageData(currentPaintData.value, 0, 0);
  const scale = overlay.value ? Math.round(overlay.value.width / SPRITE_W) : 8;
  const outCanvas = document.createElement('canvas');
  outCanvas.width = SPRITE_W * scale;
  outCanvas.height = SPRITE_H * scale;
  const outCtx = outCanvas.getContext('2d');
  if (!outCtx) return null;
  outCtx.imageSmoothingEnabled = false;
  outCtx.drawImage(tmpCanvas, 0, 0, outCanvas.width, outCanvas.height);
  return outCanvas;
}

function exportCompositeCanvas(): HTMLCanvasElement | null {
  if (props.isTestCanvas) {
    console.warn("Cannot export composite from a test canvas. Returning paint layer only.");
    return exportCanvas();
  }
  const babyCanvas = spriteComp.value?.bbyCanvas;
  if (!babyCanvas || !currentPaintData.value) {
    console.error("Missing elements for composite export:", { babyCanvas, currentPaintData });
    return null;
  }
  ensureTmpCanvas();
  if (!tmpCanvas || !tmpCtx) return null;
  tmpCtx.clearRect(0, 0, SPRITE_W, SPRITE_H);
  tmpCtx.drawImage(babyCanvas, 0, 0, SPRITE_W, SPRITE_H);
  const paintLayerCanvas = document.createElement('canvas');
  paintLayerCanvas.width = SPRITE_W;
  paintLayerCanvas.height = SPRITE_H;
  const paintLayerCtx = paintLayerCanvas.getContext('2d');
  if (paintLayerCtx) {
    paintLayerCtx.putImageData(currentPaintData.value, 0, 0);
    tmpCtx.drawImage(paintLayerCanvas, 0, 0);
  }
  const scale = overlay.value ? Math.round(overlay.value.width / SPRITE_W) : 8;
  const outCanvas = document.createElement('canvas');
  outCanvas.width = SPRITE_W * scale;
  outCanvas.height = SPRITE_H * scale;
  const outCtx = outCanvas.getContext('2d');
  if (!outCtx) return null;
  outCtx.imageSmoothingEnabled = false;
  outCtx.drawImage(tmpCanvas, 0, 0, outCanvas.width, outCanvas.height);
  return outCanvas;
}

function clampByte(x:number){ return Math.max(0, Math.min(255, Math.round(x))); }
function idx(x:number,y:number){ return (y*SPRITE_W+x)*4; }
function hexToRGB(hx:string): RgbColor { const h=hx.replace('#',''); return {r:parseInt(h.slice(0,2),16), g:parseInt(h.slice(2,4),16), b:parseInt(h.slice(4,6),16)}; }
function rgbToHex(r:number,g:number,b:number){ return "#"+[r,g,b].map(x=>{const hex=clampByte(x).toString(16); return hex.length===1?'0'+hex:hex;}).join(''); }
let cachedBase:Uint8ClampedArray|null=null;
function getBabyCanvas(){ if(props.isTestCanvas) return null; const el = spriteComp.value?.$el as HTMLElement|undefined; return el&&el.tagName==='CANVAS' ? (el as HTMLCanvasElement) : null; }
function cacheBabyAtStrokeStart(){
  if(props.isTestCanvas) { cachedBase = null; return; }
  const baby=getBabyCanvas(); if(!baby){cachedBase=null;return;}
  const ctx=baby.getContext('2d',{willReadFrequently:true}); if(!ctx){cachedBase=null;return;}
  const img=ctx.getImageData(0,0,baby.width,baby.height).data;
  const buf=new Uint8ClampedArray(SPRITE_W*SPRITE_H*4);
  for(let y=0;y<SPRITE_H;y++)for(let x=0;x<SPRITE_W;x++){ const sx=Math.floor(x*(baby.width/SPRITE_W)), sy=Math.floor(y*(baby.height/SPRITE_H)); const si=(sy*baby.width+sx)*4, di=idx(x,y); buf[di]=img[si]; buf[di+1]=img[si+1]; buf[di+2]=img[si+2]; buf[di+3]=img[si+3]; }
  cachedBase=buf;
}
function readPaintDataRGB(x:number,y:number){ if(!currentPaintData.value)return null; const d=currentPaintData.value.data,i=idx(x,y),a=d[i+3]; return a>0?{r:d[i],g:d[i+1],b:d[i+2],a}:null; }
function readBabyBaseRGB(x:number,y:number){ if(!cachedBase || props.isTestCanvas)return null; const i=idx(x,y); return { r:cachedBase[i], g:cachedBase[i+1], b:cachedBase[i+2], a:cachedBase[i+3] }; }
function readCurrentRGB(x:number,y:number): RgbaColor { const overlay = readPaintDataRGB(x,y); if(overlay) return overlay; const base = readBabyBaseRGB(x,y); if(base) return base; return {r:0,g:0,b:0,a:0}; }
function clearOverlay(){
  const data = currentPaintData.value; if(!data) return;
  data.data.fill(0);
  if (props.isTestCanvas) { redrawOverlay(); }
  else { tickPaint(); const out=[] as {x:number,y:number,r:number,g:number,b:number,a:number}[]; for(let y=0;y<SPRITE_H;y++) for(let x=0;x<SPRITE_W;x++) out.push({x,y,r:0,g:0,b:0,a:0}); sendPixelUpdate(out); }
}
function setPixel(x:number,y:number,r:number,g:number,b:number,a:number){
  const data = currentPaintData.value; if(!data) return;
  if(x<0||y<0||x>=SPRITE_W||y>=SPRITE_H) return;
  const i=idx(x,y), d=data.data; d[i]=r; d[i+1]=g; d[i+2]=b; d[i+3]=a;
  if (props.isTestCanvas) { redrawOverlay(); }
  else { tickPaint(); pixelUpdateBatch.push({x,y,r:clampByte(r),g:clampByte(g),b:clampByte(b),a:clampByte(a)}); throttledSendBatch(); }
}
function setupOverlay(){
  const containerEl = props.isTestCanvas ? stack.value : getBabyCanvas(); if(!containerEl||!overlay.value)return;
  const cssW=containerEl.clientWidth, cssH=containerEl.clientHeight;
  overlay.value.style.width=cssW+'px'; overlay.value.style.height=cssH+'px';
  overlay.value.width=Math.round(cssW*dpr); overlay.value.height=Math.round(cssH*dpr);
  octx=overlay.value.getContext('2d',{alpha:true}); if(!octx) throw new Error('overlay 2D ctx failed');
  octx.imageSmoothingEnabled=false; redrawOverlay();
}
function redrawOverlay() {
  if (!octx || !overlay.value) return;
  const containerEl = props.isTestCanvas ? stack.value : getBabyCanvas(); if (!containerEl) return;
  const cssW = containerEl.clientWidth, cssH = containerEl.clientHeight;
  const s = Math.min(cssW / SPRITE_W, cssH / SPRITE_H) || 1;
  const offset_x = (cssW - SPRITE_W * s) / 2;
  const offset_y = (cssH - SPRITE_H * s) / 2;
  octx.setTransform(dpr, 0, 0, dpr, 0, 0); octx.clearRect(0, 0, overlay.value.width, overlay.value.height); octx.setTransform(s * dpr, 0, 0, s * dpr, offset_x * dpr, offset_y * dpr);
  if (props.isTestCanvas && currentPaintData.value) {
    ensureTmpCanvas();
    if (tmpCtx && tmpCanvas) { tmpCtx.putImageData(currentPaintData.value, 0, 0); octx.drawImage(tmpCanvas, 0, 0, SPRITE_W, SPRITE_H); }
  }
  if (props.isScopeCursorActive && highlightedPixel.value) {
    const SCOPE_SIZE = 5; const PIXEL_SIZE = 4;
    const {x: hx, y: hy} = highlightedPixel.value;
    const scope_offset_x = (hx / SPRITE_W < 0.5) ? 10 : - (SCOPE_SIZE * PIXEL_SIZE) - 10;
    const scope_offset_y = (hy / SPRITE_H < 0.5) ? 10 : - (SCOPE_SIZE * PIXEL_SIZE) - 10;
    octx.save(); octx.translate(hx, hy);
    for (let dy = 0; dy < SCOPE_SIZE; dy++) { for (let dx = 0; dx < SCOPE_SIZE; dx++) { const sx = hx - Math.floor(SCOPE_SIZE/2) + dx; const sy = hy - Math.floor(SCOPE_SIZE/2) + dy; const color = readCurrentRGB(sx, sy); octx.fillStyle = `rgba(${color.r},${color.g},${color.b},${color.a/255})`; octx.fillRect(scope_offset_x + dx * PIXEL_SIZE, scope_offset_y + dy * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE); } }
    octx.strokeStyle = 'rgba(255,255,255,0.7)'; octx.lineWidth = 0.5; octx.strokeRect(scope_offset_x - 1, scope_offset_y - 1, SCOPE_SIZE * PIXEL_SIZE + 2, SCOPE_SIZE * PIXEL_SIZE + 2); octx.strokeStyle = 'rgba(0,0,0,0.7)'; octx.strokeRect(scope_offset_x + Math.floor(SCOPE_SIZE/2) * PIXEL_SIZE, scope_offset_y + Math.floor(SCOPE_SIZE/2) * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE);
    octx.restore();
  } else if (highlightedPixel.value) {
    const {x,y}=highlightedPixel.value; let offset_x = 0, offset_y = 0, stretch_x = SPRITE_W, stretch_y = SPRITE_H;
    if (!props.isTestCanvas) {
      stretch_x=SPRITE_W+(bbyState.stretch_left?1:0)+(bbyState.stretch_right?1:0)-(bbyState.squish_left?1:0)-(bbyState.squish_right?1:0); stretch_y=SPRITE_H+(bbyState.stretch_up?1:0)+(bbyState.stretch_down?1:0)-(bbyState.squish_up?1:0)-(bbyState.squish_down?1:0); const jumpset=bbyState.jumping?-4:0; offset_x=(SPRITE_W-stretch_x)/2-(bbyState.stretch_left?1:0); offset_y=(SPRITE_H-stretch_y)/2-(bbyState.stretch_up?1:0)+jumpset;
    }
    const hx=x, hy=y, hw=1;
    if (props.mode !== 'eyedropper') { octx.fillStyle = props.mode === 'erase' ? 'rgba(255,255,255,.4)' : props.hexColor+'80'; octx.fillRect(offset_x + hx*(stretch_x/SPRITE_W), offset_y + hy*(stretch_y/SPRITE_H), hw*(stretch_x/SPRITE_W), hw*(stretch_y/SPRITE_H)); }
  }
}
const handleResize = () => { setupOverlay(); redrawOverlay(); };
function cssToPixel(clientX:number, clientY:number){
  const el = overlay.value; if(!el) return null; const rect = el.getBoundingClientRect(); const lx = clientX - rect.left, ly = clientY - rect.top; let px, py;
  if (props.isTestCanvas) {
    const scale = Math.min(rect.width / SPRITE_W, rect.height / SPRITE_H); const offset_x = (rect.width - SPRITE_W * scale) / 2; const offset_y = (rect.height - SPRITE_H * scale) / 2; const canvas_x = (lx - offset_x) / scale; const canvas_y = (ly - offset_y) / scale; px = Math.floor(canvas_x); py = Math.floor(canvas_y);
  } else {
    const stretch_x=SPRITE_W+(bbyState.stretch_left?1:0)+(bbyState.stretch_right?1:0)-(bbyState.squish_left?1:0)-(bbyState.squish_right?1:0); const stretch_y=SPRITE_H+(bbyState.stretch_up?1:0)+(bbyState.stretch_down?1:0)-(bbyState.squish_up?1:0)-(bbyState.squish_down?1:0); const jumpset=bbyState.jumping?-4:0; const offset_x=(SPRITE_W-stretch_x)/2-(bbyState.stretch_left?1:0); const offset_y=(SPRITE_H-stretch_y)/2-(bbyState.stretch_up?1:0)+jumpset; const scale_x=rect.width/SPRITE_W, scale_y=rect.height/SPRITE_H; const canvas_x=lx/scale_x, canvas_y=ly/scale_y; px=Math.floor((canvas_x-offset_x)*(SPRITE_W/stretch_x)); py=Math.floor((canvas_y-offset_y)*(SPRITE_H/stretch_y));
  }
  if(px<0||py<0||px>=SPRITE_W||py>=SPRITE_H) return null;
  return {x:px,y:py};
}
function onDown(e:PointerEvent){
  overlay.value?.setPointerCapture(e.pointerId); isDown=true; paintedPixelsInStroke.clear(); cacheBabyAtStrokeStart(); const brushColor = hexToRGB(props.hexColor); strokeState = { brushColor }; paint(e);
}
function onPointerMove(e:PointerEvent){
  const p = cssToPixel(e.clientX, e.clientY); highlightedPixel.value = p;
  if (props.mode === 'eyedropper') emit('color-hovered', p ? readCurrentRGB(p.x, p.y) : null);
  if(isDown) paint(e); redrawOverlay();
}
function onUp(e:PointerEvent){
  try{overlay.value?.releasePointerCapture(e.pointerId);}catch{} isDown=false; paintedPixelsInStroke.clear(); strokeState = null;
}
function onPointerLeave(){
  highlightedPixel.value=null; emit('color-hovered', null); redrawOverlay();
}
function blendRgbColors(base: RgbColor, blend: RgbColor, amount: number): RgbColor {
  const inv = 1 - amount; return { r: clampByte(blend.r * amount + base.r * inv), g: clampByte(blend.g * amount + base.g * inv), b: clampByte(blend.b * amount + base.b * inv), };
}
function paint(e:PointerEvent){
  const p=cssToPixel(e.clientX,e.clientY); if(!p || !strokeState) return;
  const pixelKey = `${p.x},${p.y}`; if (isDown && paintedPixelsInStroke.has(pixelKey) && (props.mode === 'paint' || props.mode === 'behind')) return;
  paintedPixelsInStroke.add(pixelKey);
  const { x, y } = p;
  switch (props.mode) {
    case 'eyedropper': { const c = readCurrentRGB(x,y); if(c) emit('color-picked', rgbToHex(c.r,c.g,c.b)); return; }
    case 'paint': {
      const next = stepColourOnce(strokeState.brushColor, { activeEqs: props.activeEQs, userColour: props.userSetColor, bbyColour: props.bbyColor, tempo: props.tempo, userColorInfluence: props.userColorInfluence, bbyInfluence: props.bbyInfluence, redInfluence: props.redInfluence, greenInfluence: props.greenInfluence, blueInfluence: props.blueInfluence, rainbowInfluence: props.rainbowInfluence, baseStep: 0.05, rainbowHueStep: 20, });
      setPixel(x, y, next.r, next.g, next.b, 255); strokeState.brushColor = next; const finalHex = rgbToHex(next.r, next.g, next.b);
      if (props.hexColor !== finalHex) emit('color-picked', finalHex); if (!props.isTestCanvas) throttledReactionUpdate(next.r, next.g, next.b);
      break;
    }
    case 'behind': {
      const existing = readCurrentRGB(x, y); if (existing.a !== 0) return;
      const next = stepColourOnce(strokeState.brushColor, { activeEqs: props.activeEQs, userColour: props.userSetColor, bbyColour: props.bbyColor, tempo: props.tempo, userColorInfluence: props.userColorInfluence, bbyInfluence: props.bbyInfluence, redInfluence: props.redInfluence, greenInfluence: props.greenInfluence, blueInfluence: props.blueInfluence, rainbowInfluence: props.rainbowInfluence, baseStep: 0.05, rainbowHueStep: 20, });
      setPixel(x, y, next.r, next.g, next.b, 255); strokeState.brushColor = next; const finalHex = rgbToHex(next.r, next.g, next.b);
      if (props.hexColor !== finalHex) emit('color-picked', finalHex); if (!props.isTestCanvas) throttledReactionUpdate(next.r, next.g, next.b);
      break;
    }
    case 'blend': {
      const baseColor = readCurrentRGB(x, y); if (baseColor.a === 0) return;
      const brushColor = hexToRGB(props.hexColor); const blendAmount = (props.blendOpacity / 100) * (props.tempo / 100);
      const { r, g, b } = blendRgbColors({ r: baseColor.r, g: baseColor.g, b: baseColor.b }, brushColor, blendAmount);
      setPixel(x, y, r, g, b, baseColor.a); if (!props.isTestCanvas) throttledReactionUpdate(r, g, b);
      break;
    }
    case 'erase': {
      const existing = readCurrentRGB(x, y); if (existing.a === 0) return;
      const opacity = props.blendOpacity / 100 * (props.tempo / 100);
      const finalAlpha = existing.a * (1 - opacity);
      setPixel(x, y, existing.r, existing.g, existing.b, finalAlpha);
      break;
    }
  }
}
function updateResolution(res:number){ SPRITE_W = SPRITE_H = res; if(props.isTestCanvas){ localPaintData.value = new ImageData(SPRITE_W, SPRITE_H); } ensureTmpCanvas(true); setupOverlay(); redrawOverlay(); }
onMounted(async () => {
  await nextTick();
  if (props.isTestCanvas) { updateResolution(props.resolution ?? 32); } else { setupOverlay(); }
  const elToObserve = props.isTestCanvas ? stack.value?.parentElement : getBabyCanvas();
  if (elToObserve) { ro = new ResizeObserver(() => { setupOverlay(); redrawOverlay(); }); ro.observe(elToObserve); }
  window.addEventListener('resize', handleResize);
});
onBeforeUnmount(() => {
  const elToObserve = props.isTestCanvas ? stack.value?.parentElement : getBabyCanvas();
  if (ro && elToObserve) { ro.unobserve(elToObserve); }
  window.removeEventListener('resize', handleResize);
});
if(props.isTestCanvas){ watch(() => props.resolution, (r) => { if(typeof r === 'number') updateResolution(r); }); }
</script>

<style scoped>
.lab-wrap,.stack{width:100%;height:100%}
.stack{display:grid;align-items:center;justify-content:center;image-rendering:pixelated}
.stack>:deep(canvas),.overlay{grid-area:1/1}
.overlay{touch-action:none;cursor:crosshair}
.overlay:has(canvas[data-scope-active=true]) { cursor: none; }
</style>