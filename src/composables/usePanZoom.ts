import { ref, computed, type Ref } from 'vue';

interface PanZoomOptions {
  maxZoom?: number;
  minZoom?: number;
}

export function usePanZoom(stageEl: Ref<HTMLDivElement | null>, boardSize: Ref<number>, options: PanZoomOptions = {}) {
  const pan = ref({ x: 0, y: 0 });
  const baseScale = ref(1);
  const zoomFactor = ref(1);

  const maxZoom = options.maxZoom ?? 16;
  const minZoom = options.minZoom ?? 0.25;

  const totalScale = computed(() => Math.max(1, Math.round(baseScale.value * zoomFactor.value)));
  const canvasStyle = computed(() => ({
    transform: `translate(${Math.round(pan.value.x)}px, ${Math.round(pan.value.y)}px) scale(${totalScale.value})`,
    transformOrigin: 'top left',
    willChange: 'transform'
  }));

  function zoomIn() {
    zoomFactor.value = Math.min(maxZoom, zoomFactor.value * 1.25);
  }
  function zoomOut() {
    zoomFactor.value = Math.max(minZoom, zoomFactor.value / 1.25);
  }
  function onWheelZoom(e: WheelEvent) {
    e.deltaY < 0 ? zoomIn() : zoomOut();
  }
  function resetView() {
    pan.value = { x: 0, y: 0 };
    zoomFactor.value = 1;
    computeBaseScale();
  }

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
  }

  function endPan() {
    isPanning = false;
  }

  function computeBaseScale() {
    const s = stageEl.value;
    if (!s) return;
    const w = s.clientWidth,
      h = s.clientHeight,
      sz = boardSize.value;
    if (w <= 0 || h <= 0 || sz <= 0) return;
    baseScale.value = Math.max(1, Math.floor(Math.min(w / sz, h / sz)));
  }

  return {
    pan,
    baseScale,
    zoomFactor,
    totalScale,
    canvasStyle,
    zoomIn,
    zoomOut,
    resetView,
    onWheelZoom,
    startPan,
    onMouseMove,
    endPan,
    computeBaseScale
  };
}

export type UsePanZoom = ReturnType<typeof usePanZoom>;
