type EnvironmentShape = Record<string, string | undefined>;

function isEnabled(value: string | undefined): boolean {
  return value === 'true';
}

function requireConfigValue(config: EnvironmentShape, key: string): void {
  if (!config[key]?.trim()) {
    throw new Error(`${key} must be set for nest-api`);
  }
}

export function validateEnvironment(config: EnvironmentShape): EnvironmentShape {
  requireConfigValue(config, 'DATABASE_URL');
  requireConfigValue(config, 'JWT_SECRET_KEY');
  requireConfigValue(config, 'AI_INTERNAL_API_KEY');

  if (isEnabled(config.SEED_ADMIN_ENABLED)) {
    requireConfigValue(config, 'SEED_ADMIN_USERNAME');
    requireConfigValue(config, 'SEED_ADMIN_PHONE_NUMBER');
    requireConfigValue(config, 'SEED_ADMIN_PASSWORD');
  }

  if (isEnabled(config.SEED_VENDOR_ENABLED)) {
    requireConfigValue(config, 'SEED_VENDOR_USERNAME');
    requireConfigValue(config, 'SEED_VENDOR_PHONE_NUMBER');
    requireConfigValue(config, 'SEED_VENDOR_PASSWORD');
  }

  return config;
}
