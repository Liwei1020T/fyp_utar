import { pbkdf2Sync, randomBytes, timingSafeEqual } from 'node:crypto';

const DEFAULT_ITERATIONS = 240_000;

export function hashPassword(value: string): string {
  const salt = randomBytes(16);
  const digest = pbkdf2Sync(value, salt, DEFAULT_ITERATIONS, 32, 'sha256');
  return `pbkdf2_sha256$${DEFAULT_ITERATIONS}$${salt.toString('hex')}$${digest.toString(
    'hex',
  )}`;
}

export function verifyPassword(plainPassword: string, passwordHash: string): boolean {
  const parts = passwordHash.split('$');
  if (parts.length !== 4) {
    return false;
  }

  const [algorithm, iterationsText, saltHex, digestHex] = parts;
  if (algorithm !== 'pbkdf2_sha256') {
    return false;
  }

  const derivedDigest = pbkdf2Sync(
    plainPassword,
    Buffer.from(saltHex, 'hex'),
    Number(iterationsText),
    32,
    'sha256',
  );
  const storedDigest = Buffer.from(digestHex, 'hex');

  if (storedDigest.length !== derivedDigest.length) {
    return false;
  }

  return timingSafeEqual(storedDigest, derivedDigest);
}
