type NumericLike = number | { toString(): string } | null | undefined;

export function toNullableNumber(value: NumericLike): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  return Number(value);
}

export function toIsoString(value: Date): string {
  return value.toISOString();
}

export function toNullableIsoString(value: Date | null | undefined): string | null {
  return value ? value.toISOString() : null;
}
