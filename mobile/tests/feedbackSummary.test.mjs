import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
  feedbackEvidenceLabel,
  feedbackFeatureEntries,
  formatFeedbackScore,
} from '../lib/feedbackSummary.ts';

test('feedback evidence labels preserve the documented thresholds', () => {
  assert.equal(feedbackEvidenceLabel(0), 'No evidence');
  assert.equal(feedbackEvidenceLabel(2), 'Limited');
  assert.equal(feedbackEvidenceLabel(3), 'Developing');
  assert.equal(feedbackEvidenceLabel(10), 'Established');
});

test('feedback display converts normalized scores and keeps feature order', () => {
  assert.equal(formatFeedbackScore(0), '1.0/5');
  assert.equal(formatFeedbackScore(0.75), '4.0/5');
  assert.equal(formatFeedbackScore(2), '5.0/5');
  const entries = feedbackFeatureEntries({
    control: {
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
  assert.deepEqual(entries.map(([key]) => key), ['comfort', 'control']);
});

test('player and admin screens expose recoverable feedback-summary states', async () => {
  const [api, playerDetail, adminFeedback] = await Promise.all(
    [
      'services/backendApi.ts',
      'app/player/strings/[id].tsx',
      'app/admin/feedback.tsx',
    ].map((file) => readFile(new URL(`../${file}`, import.meta.url), 'utf8')),
  );

  assert.match(api, /'\/strings\/feedback-summary'/);
  assert.match(api, /'\/admin\/feedback\/summary'/);
  assert.match(playerDetail, /title="Local player feedback"/);
  assert.match(playerDetail, /Loading local feedback evidence/);
  assert.match(playerDetail, /No eligible local ratings yet/);
  assert.match(adminFeedback, /eyebrow="Feedback inbox"/);
  assert.match(adminFeedback, />\s*Calibration evidence/);
  assert.match(adminFeedback, /label="View calibration evidence"/);
  assert.match(adminFeedback, /visible=\{showCalibration\}/);
  assert.match(adminFeedback, /label=\{showFilters/);
  assert.match(adminFeedback, /Hide filters/);
  assert.match(adminFeedback, /Global strings/);
  assert.match(adminFeedback, /No eligible feedback ratings exist/);
  assert.doesNotMatch(adminFeedback, /Review structured service feedback/);
  assert.doesNotMatch(adminFeedback, /Read-only evidence used by V11/);
  assert.doesNotMatch(adminFeedback, /Policy .*snapshot|showing one string/);
});
