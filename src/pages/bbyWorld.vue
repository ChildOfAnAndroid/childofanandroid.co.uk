<!-- CHARIS CAT // bbyWorld - 2025 -->
<template>
  <div class="page-container bbyworld-page">
    <h1 class="page-title">bbyWorld</h1>

    <div class="world-controls">
      <label for="card-select">select a bbyfact:</label>
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
      <span>WAR: {{ stats.warDeaths }}</span>
      <span>BBY: {{ stats.babyMerges }}</span>
      <span>SQUISH: {{ stats.squishDeaths }}</span>
      <span>AVG LIFE: {{ avgLifespan }}</span>
    </div>

    <canvas
      ref="gameCanvas"
      :width="canvasW"
      :height="canvasH"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { bbyUse } from '@/composables/bbyUse.ts';

const { fetchBbyBookGallery } = bbyUse();

type GridCell = {
  r: number;
  g: number;
  b: number;
  x: number;
  y: number;
  energy: number;
  alive: boolean;
  birthTick: number;
};


const canvasScale = 20;
const gridSize = 32;
const canvasW = gridSize * canvasScale;
const canvasH = gridSize * canvasScale;
const gameCanvas = ref<HTMLCanvasElement | null>(null);

const cards = ref<{ label: string; url: string }[]>([]);
const selectedCardLabel = ref<string | null>(null);
const grid = ref<GridCell[][]>([]);

const stats = ref({
  warDeaths: 0,
  babyMerges: 0,
  squishDeaths: 0,
  totalLifespan: 0,
  deadCount: 0,
});


let tickCount = 0;
let animationFrameId: number | null = null; // To control the animation loop

onMounted(async () => {
  console.log("Component mounted. Fetching gallery data...");
  try {
    const gallery = await fetchBbyBookGallery();
    cards.value = gallery.map(card => ({ label: card.factName, url: card.url }));
    console.log(`Successfully fetched ${cards.value.length} cards.`);

    if (cards.value.length > 0) {
      selectedCardLabel.value = cards.value[0].label;
      loadSelectedImage();
    } else {
      console.warn("No cards found after fetching. The grid will be empty.");
    }
  } catch (error) {
    console.error("Failed to fetch bbyBook gallery:", error);
  }
});

function loadSelectedImage() {
  const selected = cards.value.find(c => c.label === selectedCardLabel.value);
  if (!selected) {
    console.error("Could not find the selected card:", selectedCardLabel.value);
    return;
  }

  console.log(`Attempting to load image: ${selected.url}`);

  const img = new Image();
  img.crossOrigin = "Anonymous"; // Set to "Anonymous" to request CORS headers

  // --- DEBUGGING HANDLERS ---
  img.onload = () => {
    console.log("Image successfully loaded. Processing pixels...");
    const tempCanvas = document.createElement("canvas");
    const ctx = tempCanvas.getContext("2d", { willReadFrequently: true })!; // Optimization for getImageData
    tempCanvas.width = gridSize;
    tempCanvas.height = gridSize;
    ctx.drawImage(img, 0, 0, gridSize, gridSize);

    try {
      const pixels = ctx.getImageData(0, 0, gridSize, gridSize).data;
      const newGrid: GridCell[][] = [];

      for (let y = 0; y < gridSize; y++) {
        const row: GridCell[] = [];
        for (let x = 0; x < gridSize; x++) {
          const i = (y * gridSize + x) * 4;
            row.push({
            r: pixels[i],
            g: pixels[i + 1],
            b: pixels[i + 2],
            x,
            y,
            energy: 100,
            alive: true,
            birthTick: tickCount
            });
        }
        newGrid.push(row);
      }

      grid.value = newGrid;
      console.log("Grid populated. Starting tick loop.");

      // Stop any previous animation loop before starting a new one
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      tickLoop();

    } catch (e) {
      console.error("CORS Error: Could not get image data. The server hosting the image must send 'Access-Control-Allow-Origin: *' headers.", e);
    }
  };

  img.onerror = (e) => {
    console.error("Failed to load the image. Check the URL and network connection.", e);
  };
  // --- END DEBUGGING HANDLERS ---
  
  img.src = selected.url;
}

function drawGrid(ctx: CanvasRenderingContext2D) {
  ctx.clearRect(0, 0, canvasW, canvasH);
  for (let row of grid.value) {
    for (let cell of row) {
      if (!cell.alive) continue;
      ctx.fillStyle = `rgb(${cell.r}, ${cell.g}, ${cell.b})`;
      ctx.fillRect(cell.x * canvasScale, cell.y * canvasScale, canvasScale, canvasScale);
    }
  }
}

function burstEnergy(x: number, y: number, energy: number, color: {r:number,g:number,b:number}) {
  const dirs = [
    [1,0], [-1,0], [0,1], [0,-1],
    [1,1], [-1,1], [1,-1], [-1,-1]
  ];
  for (let [dx,dy] of dirs) {
    const nx = (x + dx + gridSize) % gridSize;
    const ny = (y + dy + gridSize) % gridSize;
    const neighbour = grid.value[ny][nx];
    if (neighbour && neighbour.alive) { // Added a check if neighbour exists
      const chaos = 0.2 + Math.random() * 0.5;
      neighbour.energy = Math.min(neighbour.energy + energy * chaos, 200);
      // tint them slightly toward the dead cell's colour
      neighbour.r = Math.round((neighbour.r*3 + color.r) / 4);
      neighbour.g = Math.round((neighbour.g*3 + color.g) / 4);
      neighbour.b = Math.round((neighbour.b*3 + color.b) / 4);
    }
  }
}

function tickLoop() {
  const ctx = gameCanvas.value?.getContext("2d");
  if (!ctx) {
    console.error("Canvas context not found, stopping loop.");
    return;
  }

  tickCount++;

  const cell = pickRandomLivingCell();
  if (cell) {
    const dirs = [
      [1,0], [-1,0], [0,1], [0,-1]
    ];
    const [dx, dy] = dirs[Math.floor(Math.random() * dirs.length)];
    tryMove(cell, dx, dy);
  }

  drawGrid(ctx);
  animationFrameId = requestAnimationFrame(tickLoop);
}


function pickRandomLivingCell(): GridCell | null {
  const flat = grid.value.flat().filter(c => c.alive);
  if (flat.length === 0) return null;
  return flat[Math.floor(Math.random() * flat.length)];
}

function tryMove(cell: GridCell, dx: number, dy: number): boolean {
  const newX = (cell.x + dx + gridSize) % gridSize;
  const newY = (cell.y + dy + gridSize) % gridSize;
  const target = grid.value[newY][newX];

  if (!target) return false; // Safety check

  // Empty space → move straight in
  if (!target.alive) {
    grid.value[newY][newX] = { ...cell, x: newX, y: newY };
    grid.value[cell.y][cell.x] = { ...grid.value[cell.y][cell.x], alive: false };
    return true;
  }

  if (target.alive) {
    const pushed = tryMove(target, dx, dy);
    if (pushed) {
      grid.value[cell.y][cell.x] = { ...grid.value[cell.y][cell.x], alive: false };
      grid.value[newY][newX] = { ...cell, x: newX, y: newY };
      return true;
    } else {
      if (Math.random() < 0.5) {
        // WAR
        if (cell.energy > target.energy) {
          recordDeath(target, "war");
          grid.value[newY][newX] = {
            ...cell,
            x: newX,
            y: newY,
            energy: cell.energy - 10,
          };
          grid.value[cell.y][cell.x] = { ...grid.value[cell.y][cell.x], alive: false };
          return true;
        } else {
          recordDeath(cell, "war");
          // No need to set alive: false here, recordDeath already called
          return false;
        }
      } else {
        // BABY merge
        const strength = cell.energy + target.energy;
        const r = Math.round((cell.r * cell.energy + target.r * target.energy) / strength);
        const g = Math.round((cell.g * cell.energy + target.g * target.energy) / strength);
        const b = Math.round((cell.b * cell.energy + target.b * target.energy) / strength);

        grid.value[newY][newX] = {
          r, g, b,
          x: newX,
          y: newY,
          energy: Math.min(strength, 200),
          alive: true,
          birthTick: tickCount,
        };

        stats.value.babyMerges++;
        grid.value[cell.y][cell.x] = { ...grid.value[cell.y][cell.x], alive: false };
        return true;
      }
    }
  }

  return false;
}


function recordDeath(cell: GridCell, reason: "war"|"squish") {
  if (!cell.alive) return; // Prevent double-counting deaths

  cell.alive = false; // Mark as dead
  const lifespan = tickCount - cell.birthTick;
  stats.value.totalLifespan += lifespan;
  stats.value.deadCount++;

  if (reason === "war") stats.value.warDeaths++;
  if (reason === "squish") stats.value.squishDeaths++;

  burstEnergy(cell.x, cell.y, cell.energy, {r: cell.r, g: cell.g, b: cell.b});
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
}

.page-title {
  margin: 0;
}

.world-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing);
}

canvas {
  image-rendering: pixelated;
  border: var(--border);
  border-radius: var(--border-radius);
  background: var(--bby-colour-black);
}
</style>
