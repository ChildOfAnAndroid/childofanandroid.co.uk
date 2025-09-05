export type MetricFns<T> = Record<string, (item: T) => number>;

export function computeGroupStats<T, M extends MetricFns<T>>(
  items: T[],
  groupKey: (item: T) => string,
  metrics: M
): Array<{ colour: string; count: number; percentage: number } & { [K in keyof M]: number }> {
  const totals: Record<string, { count: number } & { [K in keyof M]: number }> = {};
  const initialMetricTotals = Object.fromEntries(
    Object.keys(metrics).map(k => [k, 0])
  ) as { [K in keyof M]: number };

  for (const item of items) {
    const key = groupKey(item);
    const group = (totals[key] || (totals[key] = { count: 0, ...initialMetricTotals })) as any;
    group.count++;
    for (const name in metrics) {
      group[name] += metrics[name](item);
    }
  }

  const totalCount = items.length;
  return Object.entries(totals).map(([colour, data]) => {
    const averages: Partial<Record<keyof M, number>> = {};
    const d: any = data;
    for (const name in metrics) {
      averages[name] = data.count ? d[name] / data.count : 0;
    }
    return { colour, count: data.count, percentage: totalCount ? (data.count / totalCount) * 100 : 0, ...averages } as { colour: string; count: number; percentage: number } & { [K in keyof M]: number };
  });
}

