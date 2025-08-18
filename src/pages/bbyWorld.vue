<!-- CHARIS CAT // bbyWorld — 2025 -->
<template>
  <div class="bbyworld-page">
    <h1>bbyWorld</h1>

    <div class="world-controls">
      <label>select a bbyfact:</label>
      <select v-model="selectedCardLabel" @change="loadSelectedImage">
        <option v-for="card in cards" :value="card.label" :key="card.label">
          {{ card.label }}
        </option>
      </select>
    </div>

    <canvas ref="gameCanvas" :width="canvasW" :height="canvasH" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
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
};

const canvasScale = 10;
const gridSize = 32;
const canvasW = gridSize * canvasScale;
const canvasH = gridSize * canvasScale;
const gameCanvas = ref<HTMLCanvasElement | null>(null);

const cards = ref<{ label: string; url: string }[]>([]);
const selectedCardLabel = ref<string | null>(null);
const grid = ref<GridCell[][]>([]);

onMounted(async () => {
  const gallery = await fetchBbyBookGallery();
  cards.value = gallery.map(card => ({ label: card.factName, url: card.url }));
});

function loadSelectedImage() {
  const selected = cards.value.find(c => c.label === selectedCardLabel.value);
  if (!selected) return;

  const img = new Image();
  img.crossOrigin = "anonymous";
  img.src = selected.url;

  img.onload = () => {
    const tempCanvas = document.createElement("canvas");
    const ctx = tempCanvas.getContext("2d")!;
    tempCanvas.width = gridSize;
    tempCanvas.height = gridSize;
    ctx.drawImage(img, 0, 0, gridSize, gridSize);

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
        });
      }
      newGrid.push(row);
    }

    grid.value = newGrid;
    tickLoop();
  };
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

function tickLoop() {
  const ctx = gameCanvas.value?.getContext("2d");
  if (!ctx) return;

  for (let i = 0; i < 20; i++) {
    const cell = pickRandomLivingCell();
    if (cell) tryMove(cell);
  }

  drawGrid(ctx);
  requestAnimationFrame(tickLoop);
}

function pickRandomLivingCell(): GridCell | null {
  const flat = grid.value.flat().filter(c => c.alive);
  if (flat.length === 0) return null;
  return flat[Math.floor(Math.random() * flat.length)];
}

function tryMove(cell: GridCell) {
  const dirs = [
    [0, 1], [1, 0], [0, -1], [-1, 0],
  ];
  const [dx, dy] = dirs[Math.floor(Math.random() * dirs.length)];

  const newX = (cell.x + dx + gridSize) % gridSize;
  const newY = (cell.y + dy + gridSize) % gridSize;
  const target = grid.value[newY][newX];

  if (!target.alive) {
    grid.value[cell.y][cell.x] = { ...cell, alive: false };
    grid.value[newY][newX] = { ...cell, x: newX, y: newY };
  } else {
    if (cell.energy > target.energy) {
      target.alive = false;
      cell.energy -= 10;
    } else {
      cell.alive = false;
    }
  }
}
</script>

<style scoped>
.bbyworld-page {
  padding: 2rem;
  background: #111;
  color: #fff;
  font-family: monospace;
}
.world-controls {
  margin-bottom: 1rem;
}
canvas {
  image-rendering: pixelated;
  border: 2px solid white;
  background: black;
}
</style>
