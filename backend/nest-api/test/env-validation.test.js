const test = require('node:test');
const assert = require('node:assert/strict');

const { validateEnvironment } = require('../dist/config/env.validation.js');

test('seeded admin requires explicit credentials when enabled', () => {
  assert.throws(
    () =>
      validateEnvironment({
        DATABASE_URL: 'postgresql://example',
        JWT_SECRET_KEY: 'secret',
        AI_INTERNAL_API_KEY: 'internal-key',
        SEED_ADMIN_ENABLED: 'true',
      }),
    /SEED_ADMIN_USERNAME must be set/,
  );
});

test('disabled seed users do not require extra credential fields', () => {
  assert.doesNotThrow(() =>
    validateEnvironment({
      DATABASE_URL: 'postgresql://example',
      JWT_SECRET_KEY: 'secret',
      AI_INTERNAL_API_KEY: 'internal-key',
      SEED_ADMIN_ENABLED: 'false',
      SEED_VENDOR_ENABLED: 'false',
    }),
  );
});
