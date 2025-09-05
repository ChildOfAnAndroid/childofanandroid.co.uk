import { computed, type Ref } from 'vue';
import { createTickFormatter, type TickLabels } from '@/utils/time';

/**
 * Shared time utilities for bbyWorld pages.
 * Provides a `formatTicks` helper along with common
 * derived displays such as elapsed time and average lifespan.
 */
export function useWorldTime(
  tickCount: Ref<number>,
  stats: Ref<{ totalLifespan: number; deadCount: number }>,
  options: { ticksPerDay?: number; daysPerYear?: number; labels?: TickLabels } = {}
) {
  const { ticksPerDay = 100, daysPerYear = 365, labels } = options;
  const formatTicks = createTickFormatter(ticksPerDay, daysPerYear, labels);
  const elapsedTimeDisplay = computed(() => formatTicks(tickCount.value));
  const avgLifespan = computed(() =>
    stats.value.deadCount > 0
      ? formatTicks(stats.value.totalLifespan / stats.value.deadCount)
      : '---'
  );
  return { formatTicks, elapsedTimeDisplay, avgLifespan };
}
export type UseWorldTime = ReturnType<typeof useWorldTime>;
