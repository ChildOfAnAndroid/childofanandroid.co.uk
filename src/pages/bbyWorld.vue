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
// These attributes set the canvas's INTERNAL resolution.
const canvasW = gridSize * canvasScale; // 1024
const canvasH = gridSize * canvasScale; // 1024

const gameCanvas = ref<HTMLCanvasElement | null>(null);
const cards = ref<{ label: string; url: string }[]>([]);
const selectedCardLabel = ref<string | null>(null);

// --- DATA STRUCTURES ---
const livingCells = ref<GridCell[]>([]);
const spatialMap = new Map<string, GridCell>();
let loadedImageData: ImageData | null = null;

const stats = ref({
  warDeaths: 0, babyMerges: 0, squishDeaths: 0,
  totalLifespan: 0, deadCount: 0,
});

// --- ROBUST GAME LOOP VARIABLES ---
let animationFrameId: number | null = null;
let lastTime = 0;
const ticksPerSecond = 30; // Run logic 30 times/sec
const tickInterval = 1000 / ticksPerSecond;
let timeSinceLastTick = 0;
let tickCount = 0;

onMounted(async () => {
  console.log("Component mounted.");
  try {
    const gallery = await fetchBbyBookGallery();
    cards.value = gallery.map(card => ({ label: card.factName, url: card.url }));
    if (cards.value.length > 0) {
      selectedCardLabel.value = cards.value[0].label;
      loadSelectedImage();
    }
  } catch (error) {
    console.error("Failed to fetch bbyBook gallery:", error);
  }

  // Start the main loop
  animationFrameId = requestAnimationFrame(mainLoop);
});

// Clean up the animation frame when the component is removed from the page
onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
});

/**
 * The main animation loop, driven by requestAnimationFrame.
 * It manages time to call the logic (update) and rendering (drawGrid) separately.
 */
function mainLoop(timestamp: number) {
  const ctx = gameCanvas.value?.getContext("2d");
  if (!ctx) return;

  const deltaTime = timestamp - lastTime;
  lastTime = timestamp;
  timeSinceLastTick += deltaTime;

  // Run the logic at a fixed rate to ensure consistent simulation speed
  while (timeSinceLastTick >= tickInterval) {
    update();
    timeSinceLastTick -= tickInterval;
  }

  drawGrid(ctx); // Draw the result once per frame
  animationFrameId = requestAnimationFrame(mainLoop);
}

/**
 * Contains only the game logic for a single tick.
 */
function update() {
  tickCount++;
  // Scale the number of movements based on population size to keep the world lively
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

function loadSelectedImage() {
  const selected = cards.value.find(c => c.label === selectedCardLabel.value);
  if (!selected) return;
  const img = new Image();
  img.crossOrigin = "Anonymous";
  img.onload = () => {
    const stampSize = 32;
    const tempCanvas = document.createElement("canvas");
    const ctx = tempCanvas.getContext("2d", { willReadFrequently: true })!;
    tempCanvas.width = stampSize;
    tempCanvas.height = stampSize;
    ctx.drawImage(img, 0, 0, stampSize, stampSize);
    loadedImageData = ctx.getImageData(0, 0, stampSize, stampSize);
    console.log(`Image "${selected.label}" ready to place.`);
  };
  img.src = selected.url;
}

function placeImage(event: MouseEvent) {
  if (!loadedImageData) return;
  const canvas = gameCanvas.value;
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  // These calculations correctly scale the mouse position to the canvas's internal resolution,
  // even if the CSS has resized its display dimensions.
  const clickX = (event.clientX - rect.left) * (canvas.width / rect.width);
  const clickY = (event.clientY - rect.top) * (canvas.height / rect.height);
  
  const gridX = Math.floor(clickX / canvasScale);
  const gridY = Math.floor(clickY / canvasScale);

  const pixels = loadedImageData.data;
  const stampWidth = loadedImageData.width;

  for (let y = 0; y < stampWidth; y++) {
    for (let x = 0; x < stampWidth; x++) {
      const i = (y * stampWidth + x) * 4;
      const alpha = pixels[i + 3];

      if (alpha > 0) {
        const newX = gridX + x;
        const newY = gridY + y;
        const mapKey = `${newX},${newY}`;
        if (newX < gridSize && newY < gridSize && !spatialMap.has(mapKey)) {
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
        return false; // A merge is not a successful "push"
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
  /* Ensure the container takes full width to properly size the canvas */
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

/* --- RESPONSIVE CANVAS FIX --- */
canvas {
  cursor: crosshair;
  border: var(--border);
  border-radius: var(--border-radius);
  background: var(--bby-colour-black);

  /* This tells the browser to keep pixels sharp when scaling, not blurry */
  image-rendering: pixelated;

  /*
    This is the key: The canvas's DISPLAY size is now responsive.
    It will scale down to fit the screen width, while its internal
    resolution (the :width and :height attributes) remains 1024x1024.
  */
  width: 100%;
  height: auto; /* Maintain aspect ratio automatically */
  max-width: 1024px; /* Prevents it from becoming huge on large monitors */
}
</style>