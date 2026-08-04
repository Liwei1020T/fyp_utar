import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import test from 'node:test';

import ts from 'typescript';

const mobileRoot = new URL('../', import.meta.url);

test('raw Pressable controls declare an accessibility role', async () => {
  const files = (
    await Promise.all(
      ['app', 'components'].map((directory) =>
        readdir(new URL(`${directory}/`, mobileRoot), { recursive: true }),
      ),
    )
  )
    .flatMap((files, index) =>
      files
        .filter((file) => file.endsWith('.tsx'))
        .map((file) => `${index === 0 ? 'app' : 'components'}/${file}`),
    );

  const missingRoles = [];

  for (const file of files) {
    const source = await readFile(new URL(file, mobileRoot), 'utf8');
    const sourceFile = ts.createSourceFile(
      file,
      source,
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TSX,
    );

    const visit = (node) => {
      if (
        (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) &&
        node.tagName.getText(sourceFile) === 'Pressable'
      ) {
        const hasRole = node.attributes.properties.some(
          (attribute) =>
            ts.isJsxAttribute(attribute) &&
            attribute.name.getText(sourceFile) === 'accessibilityRole',
        );

        if (!hasRole) {
          const { line } = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
          missingRoles.push(`${file}:${line + 1}`);
        }
      }

      ts.forEachChild(node, visit);
    };

    visit(sourceFile);
  }

  assert.deepEqual(missingRoles, []);
});

test('shared controls and catalog preserve recoverable UX states', async () => {
  const [button, input, header, catalog] = await Promise.all(
    [
      'components/ui/AppButton.tsx',
      'components/ui/AppInput.tsx',
      'components/shared/AppPageHeader.tsx',
      'app/player/(tabs)/strings.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.match(button, /busy: isLoading/);
  assert.match(input, /accessibilityLiveRegion=\{error \? 'polite' : 'none'\}/);
  assert.match(header, /accessibilityRole="header"/);
  assert.match(catalog, /label="Clear filters"/);
  assert.doesNotMatch(catalog, />\s*View All\s*</);
});

test('authentication uses one account entry and routes from the backend role', async () => {
  const [login, welcome, index] = await Promise.all(
    ['app/auth/login.tsx', 'app/auth/welcome.tsx', 'app/index.tsx'].map((file) =>
      readFile(new URL(file, mobileRoot), 'utf8'),
    ),
  );

  assert.doesNotMatch(login, /selectedRole|roleOptions/);
  assert.match(login, /if \(auth\.role === 'admin'\)/);
  assert.match(login, /if \(auth\.role !== 'customer'\)/);
  assert.match(welcome, /<Redirect href="\/auth\/login"/);
  assert.match(index, /: '\/auth\/login'/);
});

test('headers keep only task-critical copy', async () => {
  const [pageHeader, authShell, login] = await Promise.all(
    [
      'components/shared/AppPageHeader.tsx',
      'components/auth/AuthShell.tsx',
      'app/auth/login.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.doesNotMatch(pageHeader, /toneLabels|subtitleStyles|FOCUSED FLOW/);
  assert.match(pageHeader, /header-string-weave\.png/);
  assert.doesNotMatch(authShell, /Badminton stringing|Find your ideal string setup/);
  assert.doesNotMatch(login, /helperText=/);
});

test('core mobile journeys use progressive disclosure and discoverable tools', async () => {
  const [profileEdit, home, recommendation, results, adminDashboard] =
    await Promise.all(
      [
        'app/player/profile/edit.tsx',
        'app/player/(tabs)/home.tsx',
        'app/player/(tabs)/recommend.tsx',
        'app/player/(tabs)/results.tsx',
        'app/admin/(tabs)/dashboard.tsx',
      ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
    );

  assert.match(profileEdit, /Step \{step\} of 3/);
  assert.match(profileEdit, /showAdvanced/);
  assert.match(home, /activeBooking/);
  assert.match(home, /Open all player features/);
  assert.match(home, /isFeatured/);
  assert.match(home, /min-h-\[84px\] flex-1 items-center/);
  assert.doesNotMatch(home, /flex-row flex-wrap gap-3/);
  assert.match(home, /Find your next string/);
  assert.doesNotMatch(home, /playerBookings\.length\} logged/);
  assert.doesNotMatch(home, /eyebrow="ESSENTIALS"/);
  assert.doesNotMatch(recommendation, /Saved Priority Weights/);
  assert.match(results, /StringProductImage/);
  assert.match(results, /Why this fits/);
  assert.doesNotMatch(results, /Score model/);
  assert.match(adminDashboard, /title="Needs attention"/);
  assert.match(adminDashboard, /label="Search tools"/);
});
