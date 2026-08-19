import assert from 'node:assert/strict';
import test from 'node:test';

import { shouldExpireBackendSession } from '../services/backendSessionPolicy.ts';

test('a late 401 cannot expire a newer session', () => {
  assert.equal(shouldExpireBackendSession('new-token', 'old-token'), false);
  assert.equal(shouldExpireBackendSession('current-token', 'current-token'), true);
});
