const test = require('node:test');
const assert = require('node:assert/strict');

const {
  normalizeRecommendationInput,
} = require('../dist/recommendations/recommendation-normalizer.js');

test('normalizer returns a valid AI payload with defaults', () => {
  const payload = normalizeRecommendationInput({
    skill_level: 'beginner',
    playing_style: 'balanced',
    budget_min: 30,
    budget_max: 50,
    preferred_tension: 24,
    game_type: 'singles',
    frequency_per_week: 2,
    pref_attack: 3,
    pref_comfort: 4,
    pref_control: 4,
    pref_durability: 4,
    pref_elasticity: 3,
    pref_sound: 3,
    pref_string_movement: 4,
    pref_tension_retention: 4,
    pref_value_for_money: 5,
  });

  assert.equal(payload.top_n, 5);
  assert.equal(payload.budget_max, 50);
  assert.equal(payload.pref_comfort, 4);
});

test('normalizer rejects inverted budget ranges', () => {
  assert.throws(
    () =>
      normalizeRecommendationInput({
        skill_level: 'beginner',
        playing_style: 'balanced',
        budget_min: 60,
        budget_max: 50,
        preferred_tension: 24,
        game_type: 'singles',
        frequency_per_week: 2,
        pref_attack: 3,
        pref_comfort: 4,
        pref_control: 4,
        pref_durability: 4,
        pref_elasticity: 3,
        pref_sound: 3,
        pref_string_movement: 4,
        pref_tension_retention: 4,
        pref_value_for_money: 5,
      }),
    /budget_min must be less than or equal to budget_max/,
  );
});
