<!-- CHARIS CAT // bbyWorld - 2025 -->
<template>
  <div class="page-container bbyworld-page">
    <h1 class="page-title">bbyWorld</h1>

    <div class="world-controls">
      <label for="card-select">select a bby to place:</label>
      <select
        id="card-select"
        v-model="selectedCardLabel"
        @change="loadSelectedImage"
      >
        <option v-for="card in cards" :value="card.label" :key="card.label">
          {{ card.label }}
        </option>
      </select>
    </div>

    <div class="world-stats">
      <span>CELLS: {{ livingCells.length }}</span>
      <span>WAR: {{ stats.warDeaths }}</span>
      <span>BBY: {{ stats.babyMerges }}</span>
      <span>SQUISH: {{ stats.squishDeaths }}</span>
      <span>AVG LIFE: {{ avgLifespan }}</span>
    </div>

    <canvas
      ref="gameCanvas"
      :width="canvasW"
      :height="canvasH"
      @click="placeImage"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, onUnmounted } from "vue";
import { bbyUse } from '@/composables/bbyUse.ts';

const { fetchBbyBookGallery } = bbyUse();

type GridCell = {
  r: number; g: number; b: number;
  x: number; y: number;
  energy: number; alive: boolean; birthTick: number;
};

// --- CORE CONFIGURATION ---
const gridSize = 256;
const canvasScale = 4;
const canvasW = gridSize * canvasScale;
const canvasH = gridSize * canvasScale;
const MAX_STAMP_DIMENSION = 96; // Max width or height of 96px

const gameCanvas = ref<HTMLCanvasElement | null>(null);
const cards = ref<{ label: string; url: string; stamp_url?: string; }[]>([]);
const selectedCardLabel = ref<string | null>(null);

// --- DATA STRUCTURES ---
const livingCells = ref<GridCell[]>([]);
const spatialMap = new Map<string, GridCell>();
let loadedImageData: ImageData | null = null;

const stats = ref({
  warDeaths: 0, babyMerges: 0, squishDeaths: 0,
  totalLifespan: 0, deadCount: 0,
});

// --- GAME LOOP VARIABLES ---
let animationFrameId: number | null = null;
let lastTime = 0;
const ticksPerSecond = 30;
const tickInterval = 1000 / ticksPerSecond;
let timeSinceLastTick = 0;
let tickCount = 0;

onMounted(async () => {
  console.log("Component mounted.");
  try {
    const gallery = await fetchBbyBookGallery();
    // MODIFIED: Also store the stamp_url if it exists
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
  animationFrameId = requestAnimationFrame(mainLoop);
});

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
});

function mainLoop(timestamp: number) {
  const ctx = gameCanvas.value?.getContext("2d");
  if (!ctx) return;

  const deltaTime = timestamp - lastTime;
  lastTime = timestamp;
  timeSinceLastTick += deltaTime;

  while (timeSinceLastTick >= tickInterval) {
    update();
    timeSinceLastTick -= tickInterval;
  }
  drawGrid(ctx);
  animationFrameId = requestAnimationFrame(mainLoop);
}

function update() {
  tickCount++;
  const updatesPerTick = Math.ceil(livingCells.value.length / 100);
  for (let i = 0; i < updatesPerTick; i++) {
    const cell = pickRandomLivingCell();
    if (cell) {
      const dirs = [[1,0], [-1,0], [0,1], [0,-1]];
      const [dx, dy] = dirs[Math.floor(Math.random() * dirs.length)];
      tryMove(cell, dx, dy);
    }
  }
}

/**
 * Loads the selected image and processes it into pixel data,
 * respecting its original size up to a maximum limit.
 */
function loadSelectedImage() {
  const selected = cards.value.find(c => c.label === selectedCardLabel.value);
  if (!selected) return;
  const img = new Image();
  img.crossOrigin = "Anonymous";
  img.onload = () => {
    // This logic is now a fallback for older images without stamps.
    // The stamp itself is already correctly sized by the server.
    let stampWidth = img.width;
    let stampHeight = img.height;

    // If the image is too large, scale it down while maintaining aspect ratio.
    if (!selected.stamp_url && (stampWidth > MAX_STAMP_DIMENSION || stampHeight > MAX_STAMP_DIMENSION)) {
      const ratio = Math.min(MAX_STAMP_DIMENSION / stampWidth, MAX_STAMP_DIMENSION / stampHeight);
      stampWidth = Math.floor(stampWidth * ratio);
      stampHeight = Math.floor(stampHeight * ratio);
      console.warn(`Image was too large, scaled down to ${stampWidth}x${stampHeight}`);
    }

    const tempCanvas = document.createElement("canvas");
    const ctx = tempCanvas.getContext("2d", { willReadFrequently: true })!;
    tempCanvas.width = stampWidth;
    tempCanvas.height = stampHeight;
    // Draw the image (potentially scaled) onto the temp canvas
    ctx.drawImage(img, 0, 0, stampWidth, stampHeight);

    loadedImageData = ctx.getImageData(0, 0, stampWidth, stampHeight);
    console.log(`Image "${selected.label}" ready to place at ${stampWidth}x${stampHeight}.`);
  };

  // MODIFIED: Prioritize stamp_url, fallback to original url
  const imageUrl = selected.stamp_url || selected.url;
  console.log(`Loading image for bbyWorld: ${imageUrl}`);
  img.src = imageUrl;
}

/**
 * Places the loaded image, centering it on the cursor.
 */
function placeImage(event: MouseEvent) {
  if (!loadedImageData) return;
  const canvas = gameCanvas.value;
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  const clickX = (event.clientX - rect.left) * (canvas.width / rect.width);
  const clickY = (event.clientY - rect.top) * (canvas.height / rect.height);
  
  const mouseGridX = Math.floor(clickX / canvasScale);
  const mouseGridY = Math.floor(clickY / canvasScale);
  
  const stampWidth = loadedImageData.width;
  const stampHeight = loadedImageData.height;

  // Calculate top-left corner to center the image on the cursor
  const startGridX = mouseGridX - Math.floor(stampWidth / 2);
  const startGridY = mouseGridY - Math.floor(stampHeight / 2);
  
  const pixels = loadedImageData.data;

  for (let y = 0; y < stampHeight; y++) {
    for (let x = 0; x < stampWidth; x++) {
      const i = (y * stampWidth + x) * 4;
      const alpha = pixels[i + 3];

      if (alpha > 0) {
        const newX = startGridX + x;
        const newY = startGridY + y;
        const mapKey = `${newX},${newY}`;

        if (newX >= 0 && newX < gridSize && newY >= 0 && newY < gridSize && !spatialMap.has(mapKey)) {
          const newCell: GridCell = {
            r: pixels[i], g: pixels[i+1], b: pixels[i+2],
            x: newX, y: newY, energy: 100, alive: true, birthTick: tickCount,
          };
          livingCells.value.push(newCell);
          spatialMap.set(mapKey, newCell);
        }
      }
    }
  }
}

function drawGrid(ctx: CanvasRenderingContext2D) {
  ctx.clearRect(0, 0, canvasW, canvasH);
  for (const cell of livingCells.value) {
    ctx.fillStyle = `rgb(${cell.r}, ${cell.g}, ${cell.b})`;
    ctx.fillRect(cell.x * canvasScale, cell.y * canvasScale, canvasScale, canvasScale);
  }
}

function pickRandomLivingCell(): GridCell | null {
  if (livingCells.value.length === 0) return null;
  const randomIndex = Math.floor(Math.random() * livingCells.value.length);
  return livingCells.value[randomIndex];
}

function tryMove(cell: GridCell, dx: number, dy: number): boolean {
  const newX = (cell.x + dx + gridSize) % gridSize;
  const newY = (cell.y + dy + gridSize) % gridSize;
  const target = spatialMap.get(`${newX},${newY}`);

  const performMove = (movingCell: GridCell, toX: number, toY: number) => {
    spatialMap.delete(`${movingCell.x},${movingCell.y}`);
    movingCell.x = toX;
    movingCell.y = toY;
    spatialMap.set(`${toX},${toY}`, movingCell);
  };

  if (!target) {
    performMove(cell, newX, newY);
    return true;
  }
  if (target.alive) {
    const pushed = tryMove(target, dx, dy);
    if (pushed) {
      performMove(cell, newX, newY);
      return true;
    } else {
      if (Math.random() < 0.5) { // WAR
        if (cell.energy > target.energy) {
          recordDeath(target, "war");
          cell.energy -= 10;
          performMove(cell, newX, newY);
          return true;
        } else {
          recordDeath(cell, "war");
          return false;
        }
      } else { // BABY merge
        const strength = cell.energy + target.energy;
        const baby: GridCell = {
          r: Math.round((cell.r * cell.energy + target.r * target.energy) / strength),
          g: Math.round((cell.g * cell.energy + target.g * target.energy) / strength),
          b: Math.round((cell.b * cell.energy + target.b * target.energy) / strength),
          x: newX, y: newY,
          energy: Math.min(strength, 200),
          alive: true, birthTick: tickCount,
        };
        recordDeath(cell, "squish");
        recordDeath(target, "squish");
        livingCells.value.push(baby);
        spatialMap.set(`${newX},${newY}`, baby);
        stats.value.babyMerges++;
        return false;
      }
    }
  }
  return false;
}

function recordDeath(cell: GridCell, reason: "war" | "squish") {
  if (!cell.alive) return;
  cell.alive = false;
  
  stats.value.totalLifespan += tickCount - cell.birthTick;
  stats.value.deadCount++;
  if (reason === "war") stats.value.warDeaths++;
  if (reason === "squish") stats.value.squishDeaths++;

  spatialMap.delete(`${cell.x},${cell.y}`);
  const index = livingCells.value.findIndex(c => c === cell);
  if (index > -1) livingCells.value.splice(index, 1);

  burstEnergy(cell.x, cell.y, cell.energy, { r: cell.r, g: cell.g, b: cell.b });
}

function burstEnergy(x: number, y: number, energy: number, color: {r:number,g:number,b:number}) {
  const dirs = [[1,0], [-1,0], [0,1], [0,-1], [1,1], [-1,1], [1,-1], [-1,-1]];
  for (let [dx,dy] of dirs) {
    const nx = (x + dx + gridSize) % gridSize;
    const ny = (y + dy + gridSize) % gridSize;
    const neighbour = spatialMap.get(`${nx},${ny}`);
    if (neighbour?.alive) {
      neighbour.energy = Math.min(neighbour.energy + (energy * (0.2 + Math.random() * 0.5)), 200);
      neighbour.r = Math.round((neighbour.r*3 + color.r) / 4);
      neighbour.g = Math.round((neighbour.g*3 + color.g) / 4);
      neighbour.b = Math.round((neighbour.b*3 + color.b) / 4);
    }
  }
}

const avgLifespan = computed(() => {
  return stats.value.deadCount > 0
    ? (stats.value.totalLifespan / stats.value.deadCount).toFixed(1)
    : "–";
});
</script>

<style scoped>
.bbyworld-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing);
  width: 100%;
}

.page-title {
  margin: 0;
}

.world-controls, .world-stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: var(--spacing);
}

canvas {
  cursor: crosshair;
  border: var(--border);
  border-radius: var(--border-radius);
  background: var(--bby-colour-black);
  image-rendering: pixelated;
  width: 100%;
  height: auto;
  max-width: 1024px;
}
</style>