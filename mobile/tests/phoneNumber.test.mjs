import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const mobileRoot = new URL('../', import.meta.url);

test('auth phone input caps local digits and warns before stripping a leading zero', async () => {
  const [field, login, register] = await Promise.all(
    [
      'components/auth/PhoneNumberField.tsx',
      'app/auth/login.tsx',
      'app/auth/register.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.match(field, /LOCAL_PHONE_DIGIT_LIMIT = 10/);
  assert.match(field, /maxLength=\{LOCAL_PHONE_DIGIT_LIMIT\}/);
  assert.match(
    field,
    /normalizePhoneNumber\(nextValue\)\.slice\(0, LOCAL_PHONE_DIGIT_LIMIT\)/,
  );

  for (const source of [login, register]) {
    assert.match(source, /\.max\(\s*LOCAL_PHONE_DIGIT_LIMIT/);
    assert.match(source, /normalizePhoneNumber\(data\.phoneNumber\)/);
    assert.match(source, /normalizedPhoneNumber\.startsWith\('0'\)/);
    assert.match(source, /showAlert\(/);
  }
});
