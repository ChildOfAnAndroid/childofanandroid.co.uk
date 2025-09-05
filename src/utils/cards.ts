export interface CardLike { label: string }

export function resolveCardLabel<T extends CardLike>(cards: T[], label: string): string {
  const match = cards.find(c => c.label.toLowerCase() === label.toLowerCase());
  return match ? match.label : label;
}
