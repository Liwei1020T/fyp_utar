const test = require('node:test');
const assert = require('node:assert/strict');

const {
  normalizePhoneNumber,
} = require('../dist/common/utils/phone-number.js');

test('normalizePhoneNumber strips formatting noise', () => {
  assert.equal(normalizePhoneNumber(' 012-345 6789 '), '0123456789');
});

test('normalizePhoneNumber rejects invalid numbers', () => {
  assert.throws(() => normalizePhoneNumber('12345'), /Phone number must contain/);
});
