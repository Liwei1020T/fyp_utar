import assert from 'node:assert/strict';
import test from 'node:test';

import { agentResponseToHistoryContent } from '../lib/agentHistory.ts';

test('Agent history keeps the visible summary, answer, and evidence', () => {
  const content = agentResponseToHistoryContent({
    summary: 'Ten of twelve bookings shown',
    answer: 'Booking 1: awaiting drop-off',
    evidence: ['The search returned 10 of 12 bookings.'],
  });

  assert.match(content, /Ten of twelve bookings shown/);
  assert.match(content, /Booking 1: awaiting drop-off/);
  assert.match(content, /The search returned 10 of 12 bookings/);
  assert.ok(content.length <= 2000);
});
