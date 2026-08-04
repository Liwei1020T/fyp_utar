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
