let rngSeed = Date.now();

export function seedRand(seed: number) {
  rngSeed = seed;
}

export function rand(): number {
  rngSeed = (rngSeed * 16807 + 1) % 2147483647;
  return (rngSeed - 1) / 2147483646;
}
