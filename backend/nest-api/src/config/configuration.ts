import path from 'node:path';

export function resolveBackendRoot(baseDir = __dirname): string {
  return path.resolve(baseDir, '..', '..', '..');
}

export function resolveBackendPath(
  relativeOrAbsolutePath: string,
  baseDir = __dirname,
): string {
  return path.isAbsolute(relativeOrAbsolutePath)
    ? relativeOrAbsolutePath
    : path.resolve(resolveBackendRoot(baseDir), relativeOrAbsolutePath);
}

export default () => ({
  app: {
    name: process.env.APP_NAME ?? 'StringSense Nest API',
    port: Number(process.env.PORT ?? 3001),
  },
  database: {
    url: process.env.DATABASE_URL,
  },
  auth: {
    jwtSecret: process.env.JWT_SECRET_KEY ?? 'stringsense-local-dev-secret-key-2026',
    jwtIssuer: process.env.JWT_ISSUER ?? 'stringsense-nest-api',
    jwtExpiresMinutes: Number(process.env.ACCESS_TOKEN_EXPIRE_MINUTES ?? 60),
    seedAdminEnabled: (process.env.SEED_ADMIN_ENABLED ?? 'false') === 'true',
    seedAdminUsername: process.env.SEED_ADMIN_USERNAME,
    seedAdminPhoneNumber: process.env.SEED_ADMIN_PHONE_NUMBER,
    seedAdminPassword: process.env.SEED_ADMIN_PASSWORD,
    seedVendorEnabled: (process.env.SEED_VENDOR_ENABLED ?? 'false') === 'true',
    seedVendorUsername: process.env.SEED_VENDOR_USERNAME,
    seedVendorPhoneNumber: process.env.SEED_VENDOR_PHONE_NUMBER,
    seedVendorPassword: process.env.SEED_VENDOR_PASSWORD,
  },
  aiService: {
    baseUrl: process.env.AI_SERVICE_BASE_URL ?? 'http://127.0.0.1:8000',
    internalApiKey: process.env.AI_INTERNAL_API_KEY,
    timeoutMs: Number(process.env.AI_SERVICE_TIMEOUT_MS ?? 8000),
  },
  catalog: {
    approvedSourcePath: resolveBackendPath(
      process.env.APPROVED_STRINGS_SOURCE_PATH ??
        'data/raw/badminton_strings_recommender.jsonl',
    ),
  },
});
