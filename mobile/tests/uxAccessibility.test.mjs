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

test('images are described or hidden from assistive technology', async () => {
  const files = (
    await Promise.all(
      ['app', 'components'].map((directory) =>
        readdir(new URL(`${directory}/`, mobileRoot), { recursive: true }),
      ),
    )
  ).flatMap((files, index) =>
    files
      .filter((file) => file.endsWith('.tsx'))
      .map((file) => `${index === 0 ? 'app' : 'components'}/${file}`),
  );
  const missingSemantics = [];

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
        node.tagName.getText(sourceFile) === 'Image'
      ) {
        const attributes = node.attributes.properties
          .filter(ts.isJsxAttribute)
          .map((attribute) => attribute.name.getText(sourceFile));
        if (
          !attributes.includes('accessibilityLabel') &&
          !attributes.includes('accessible')
        ) {
          const { line } = sourceFile.getLineAndCharacterOfPosition(
            node.getStart(sourceFile),
          );
          missingSemantics.push(`${file}:${line + 1}`);
        }
      }
      ts.forEachChild(node, visit);
    };
    visit(sourceFile);
  }

  assert.deepEqual(missingSemantics, []);
});

test('shared controls and catalog preserve recoverable UX states', async () => {
  const [button, input, select, datePicker, screen, header, logo, catalog] = await Promise.all(
    [
      'components/ui/AppButton.tsx',
      'components/ui/AppInput.tsx',
      'components/ui/AppSelect.tsx',
      'components/ui/AppDatePicker.tsx',
      'components/shared/AppScreen.tsx',
      'components/shared/AppPageHeader.tsx',
      'components/ui/AppBrandLogo.tsx',
      'app/player/(tabs)/strings.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.match(button, /busy: isLoading/);
  assert.match(input, /accessibilityLiveRegion=\{error \? 'polite' : 'none'\}/);
  assert.match(select, /position: 'absolute'/);
  assert.match(select, /zIndex: 1000/);
  assert.match(datePicker, /type: 'date'/);
  assert.match(datePicker, /DateTimePicker/);
  assert.match(datePicker, /accessibilityRole="button"/);
  assert.match(screen, /subtitle=\{subtitle\}/);
  assert.match(header, /accessibilityRole="header"/);
  assert.match(header, /\{subtitle \? \(/);
  assert.match(logo, /style=\{\{ width: '100%', height: '100%' \}\}/);
  assert.match(catalog, /label="Clear filters"/);
  assert.doesNotMatch(catalog, />\s*View All\s*</);
});

test('feedback submission uses a clear confirmation dialog', async () => {
  const [feedback, alerts] = await Promise.all(
    ['app/player/feedback/[bookingId].tsx', 'lib/alerts.ts'].map((file) =>
      readFile(new URL(file, mobileRoot), 'utf8'),
    ),
  );

  assert.match(feedback, /showAlert\(alertTitle, alertMessage\)/);
  assert.match(alerts, /globalThis\.alert\(/);
  assert.match(alerts, /Alert\.alert\(/);
  assert.match(feedback, /Feedback submitted/);
  assert.doesNotMatch(feedback, /future evidence/i);
  assert.doesNotMatch(feedback, /durability|feedback-eligibility/i);
});

test('binary preference controls use native switches', async () => {
  const sources = await Promise.all(
    [
      'app/player/notifications/preferences.tsx',
      'app/player/settings.tsx',
      'app/admin/settings.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  for (const source of sources) {
    assert.match(source, /<Switch/);
  }
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

test('reduced Agent cards hide evidence status labels', async () => {
  const [answerCard, chatbot] = await Promise.all(
    [
      'components/agent/AgentAnswerCard.tsx',
      'app/player/chatbot.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.match(answerCard, /const showEvidenceStatus = false/);
  assert.match(answerCard, /showEvidenceStatus \?/);
  assert.match(chatbot, /label="Contact human support"/);
  assert.match(chatbot, /router\.push\('\/player\/chat'\)/);
});

test('core mobile journeys use progressive disclosure and discoverable tools', async () => {
  const [profileEdit, home, profile, tools, recommendation, results, adminDashboard, inventory, inventoryCard, analytics, businessHours, settings, bookingSummary, payment] =
    await Promise.all(
      [
        'app/player/profile/edit.tsx',
        'app/player/(tabs)/home.tsx',
        'app/player/(tabs)/profile.tsx',
        'app/player/tools.tsx',
        'app/player/(tabs)/recommend.tsx',
        'app/player/(tabs)/results.tsx',
        'app/admin/(tabs)/dashboard.tsx',
        'app/admin/(tabs)/inventory.tsx',
        'components/admin/inventory/AdminInventoryCard.tsx',
        'app/admin/(tabs)/analytics.tsx',
        'app/admin/business-hours.tsx',
        'app/admin/settings.tsx',
        'app/player/bookings/summary.tsx',
        'app/player/payments/[bookingId].tsx',
      ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
    );

  assert.match(profileEdit, /Step \{step\} of 3/);
  assert.match(profileEdit, /showAdvanced/);
  assert.match(profileEdit, /skillLevel === 'Beginner' && tension > 25/);
  assert.match(profileEdit, /For beginners, 22–25 lbs is recommended/);
  assert.match(profileEdit, /Adjust to 25 lbs/);
  assert.match(home, /activeBooking/);
  assert.match(home, /Open all player features/);
  assert.match(home, /router\.push\('\/player\/tools'\)/);
  assert.match(home, /isFeatured/);
  assert.match(home, /min-h-\[84px\] flex-1 items-center/);
  assert.doesNotMatch(home, /flex-row flex-wrap gap-3/);
  assert.match(home, /Find your next string/);
  assert.doesNotMatch(home, /playerBookings\.length\} logged/);
  assert.doesNotMatch(home, /eyebrow="ESSENTIALS"/);
  assert.doesNotMatch(profile, /More player tools|ALL FEATURES/);
  assert.match(profile, /label="Account settings"/);
  assert.match(tools, /title="All tools"/);
  assert.match(tools, /title: 'Play'/);
  assert.match(tools, /title: 'Service'/);
  assert.match(tools, /title: 'Account'/);
  assert.match(inventory, /accessibilityLabel="Show inventory filters"/);
  assert.match(inventory, /className="mb-3 flex-row items-end gap-2"/);
  assert.match(inventory, /headerVariant="primary"/);
  assert.match(inventory, /adminUpdateInventoryString/);
  assert.match(inventoryCard, /label=\{isSavingStock \? 'Saving stock' : 'Save stock'\}/);
  assert.doesNotMatch(inventoryCard, /label: 'Notes'|label="Notes"/);
  assert.doesNotMatch(
    analytics,
    /Requested tension distribution|Popular strings|When the desk gets crowded|adminPopularStrings/,
  );
  assert.match(businessHours, /title="Temporary closures"/);
  assert.match(businessHours, /label="Add closed date"/);
  assert.match(businessHours, /label="Month"/);
  assert.doesNotMatch(businessHours, /Comma-separated YYYY-MM-DD dates/);
  assert.doesNotMatch(settings, /Default service price|Service fee \(RM\)/);
  assert.doesNotMatch(settings, /Default title|Default body/);
  assert.doesNotMatch(bookingSummary, /Service fee|defaultServicePrice/);
  assert.doesNotMatch(payment, /Service fee|service_fee/);
  assert.doesNotMatch(tools, /\/player\/profile\/edit/);
  assert.doesNotMatch(recommendation, /Saved Priority Weights/);
  assert.match(results, /StringProductImage/);
  assert.match(results, /Why this fits/);
  assert.doesNotMatch(results, /Score model/);
  assert.match(adminDashboard, /title="Needs attention"/);
  assert.match(adminDashboard, /label="Search tools"/);
});
