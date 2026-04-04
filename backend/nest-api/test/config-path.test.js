const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  resolveBackendRoot,
  resolveBackendPath,
} = require('../dist/config/configuration.js');

test('resolveBackendRoot points at backend from src and dist config directories', () => {
  assert.equal(
    resolveBackendRoot('/tmp/work/backend/nest-api/src/config'),
    '/tmp/work/backend',
  );
  assert.equal(
    resolveBackendRoot('/tmp/work/backend/nest-api/dist/config'),
    '/tmp/work/backend',
  );
});

test('resolveBackendPath treats relative catalog paths as backend-root-relative', () => {
  assert.equal(
    resolveBackendPath('data/raw/catalog.jsonl', '/tmp/work/backend/nest-api/src/config'),
    '/tmp/work/backend/data/raw/catalog.jsonl',
  );
  assert.equal(
    resolveBackendPath(
      './data/raw/catalog.jsonl',
      '/tmp/work/backend/nest-api/dist/config',
    ),
    '/tmp/work/backend/data/raw/catalog.jsonl',
  );
  assert.equal(
    resolveBackendPath('/already/absolute/catalog.jsonl'),
    path.normalize('/already/absolute/catalog.jsonl'),
  );
});
