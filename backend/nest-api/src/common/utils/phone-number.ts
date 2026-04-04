export function normalizePhoneNumber(value: string): string {
  const raw = value.trim().replace(/[\s()-]+/g, '');
  const normalized = raw.startsWith('+')
    ? `+${raw.slice(1).replace(/[^0-9]/g, '')}`
    : raw.replace(/[^0-9]/g, '');

  if (!/^(?:\+?[0-9]{9,15})$/.test(normalized)) {
    throw new Error('Phone number must contain 9 to 15 digits');
  }

  return normalized;
}

export function isPhoneNumber(value: string): boolean {
  try {
    normalizePhoneNumber(value);
    return true;
  } catch {
    return false;
  }
}
