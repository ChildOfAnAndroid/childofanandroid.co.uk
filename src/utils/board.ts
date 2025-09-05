import type { Ref } from 'vue';

export function applyBoardSize(
  pan: Ref<{ x: number; y: number }>,
  zoomFactor: Ref<number>,
  gameCanvas: Ref<HTMLCanvasElement | null>,
  size: number,
  allocateWorldArrays: (size: number) => void,
  clearWorld: () => void,
  computeBaseScale: () => void,
) {
  pan.value = { x: 0, y: 0 };
  zoomFactor.value = 1;
  const canvas = gameCanvas.value;
  if (canvas) {
    canvas.width = size;
    canvas.height = size;
  }
  allocateWorldArrays(size);
  clearWorld();
  computeBaseScale();
}
