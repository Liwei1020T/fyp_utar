import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
  communityEvidenceLabel,
  communityFeatureEntries,
  formatCommunityScore,
} from '../lib/communityFeedback.ts';

test('community evidence labels preserve the documented thresholds', () => {
  assert.equal(communityEvidenceLabel(0), 'No evidence');
  assert.equal(communityEvidenceLabel(2), 'Limited');
  assert.equal(communityEvidenceLabel(3), 'Developing');
  assert.equal(communityEvidenceLabel(10), 'Established');
});

test('community display converts normalized scores and keeps feature order', () => {
  assert.equal(formatCommunityScore(0), '1.0/5');
  assert.equal(formatCommunityScore(0.75), '4.0/5');
  assert.equal(formatCommunityScore(2), '5.0/5');
  const entries = communityFeatureEntries({
    durability: {
      score: 1,
      distinct_users: 1,
      booking_count: 1,
      confidence: 0.1,
      weight: 0.03,
      evidence_scope: 'global_string',
      source_version: 'd',
    },
    comfort: {
      score: 1,
      distinct_users: 1,
      booking_count: 1,
      confidence: 0.1,
      weight: 0.03,
      evidence_scope: 'global_string',
      source_version: 'c',
    },
  });
  assert.deepEqual(entries.map(([key]) => key), ['comfort', 'durability']);
});

test('player and admin screens expose recoverable community-summary states', async () => {
  const [api, playerDetail, adminFeedback] = await Promise.all(
    [
      'services/backendApi.ts',
      'app/player/strings/[id].tsx',
      'app/admin/feedback.tsx',
    ].map((file) => readFile(new URL(`../${file}`, import.meta.url), 'utf8')),
  );

  assert.match(api, /'\/strings\/community-summary'/);
  assert.match(api, /'\/admin\/feedback\/community-summary'/);
  assert.match(playerDetail, /title="Local player feedback"/);
  assert.match(playerDetail, /Loading local feedback evidence/);
  assert.match(playerDetail, /No eligible local ratings yet/);
  assert.match(adminFeedback, /title="Community calibration"/);
  assert.match(adminFeedback, /Global strings/);
  assert.match(adminFeedback, /No eligible community ratings exist/);
});
