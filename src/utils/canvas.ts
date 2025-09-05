export interface CanvasCoords { x: number; y: number }

export function eventToCanvasCoords(canvas: HTMLCanvasElement, e: { clientX: number; clientY: number }): CanvasCoords {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY,
  };
}

/**
 * Convert a mouse event to integer cell coordinates on a canvas.
 * Useful when dealing with grid-based canvases where each pixel maps to a cell.
 */
export function eventToCellCoords(canvas: HTMLCanvasElement, e: { clientX: number; clientY: number }): CanvasCoords {
  const { x, y } = eventToCanvasCoords(canvas, e);
  return { x: Math.floor(x), y: Math.floor(y) };
}
