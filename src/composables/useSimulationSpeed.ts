import { ref, computed } from 'vue';

/**
 * Shared simulation speed controls used across bbyWorld pages.
 * Provides reactive ticks-per-second state with helpers to
 * speed up, slow down and pause the simulation.
 */
export function useSimulationSpeed(initial = 30) {
  const ticksPerSecond = ref(initial);
  const isPaused = ref(false);
  const tickInterval = computed(() => 1000 / ticksPerSecond.value);

  function speedUp() {
    ticksPerSecond.value = Math.min(240, ticksPerSecond.value + 10);
  }

  function slowDown() {
    ticksPerSecond.value = Math.max(1, ticksPerSecond.value - 10);
  }

  function togglePause() {
    isPaused.value = !isPaused.value;
  }

  return {
    ticksPerSecond,
    isPaused,
    tickInterval,
    speedUp,
    slowDown,
    togglePause,
  };
}
