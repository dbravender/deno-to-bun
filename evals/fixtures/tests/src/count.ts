export function parseCount(value: string): number {
  if (!/^\d+$/.test(value) || Number(value) < 1) {
    throw new RangeError("positive integer required");
  }
  return Number(value);
}
