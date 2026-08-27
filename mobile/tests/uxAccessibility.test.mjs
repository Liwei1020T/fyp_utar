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

test('booking setup can register and return with a selected racket', async () => {
  const [booking, racket] = await Promise.all(
    [
      'app/player/bookings/new.tsx',
      'app/player/rackets/new.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.match(booking, /label="Racket passport"/);
  assert.match(booking, /returnTo=booking/);
  assert.match(booking, /Register this racket/);
  assert.match(booking, /setValue\('racketBrand', ''/);
  assert.match(racket, /params\.returnTo === 'booking'/);
  assert.match(racket, /\/player\/bookings\/new\?racketId=/);
});

test('booking setup uses sequential steps', async () => {
  const booking = await readFile(
    new URL('app/player/bookings/new.tsx', mobileRoot),
    'utf8',
  );

  assert.match(booking, /type BookingStep = 1 \| 2 \| 3/);
  assert.match(booking, /accessibilityRole="progressbar"/);
  assert.match(booking, /Continue to setup/);
  assert.match(booking, /Continue to drop-off/);
  assert.match(booking, /Review booking/);
  assert.match(booking, /currentStep === 1/);
  assert.match(booking, /currentStep === 2/);
  assert.match(booking, /currentStep === 3/);
});

test('racket specs use selects without preferred-use UI', async () => {
  const [newRacket, detailRacket] = await Promise.all(
    [
      'app/player/rackets/new.tsx',
      'app/player/rackets/[id].tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  for (const source of [newRacket, detailRacket]) {
    assert.match(source, /racketWeightClassOptions/);
    assert.match(source, /racketBalancePointOptions/);
    assert.match(source, /racketGripSizeOptions/);
    assert.match(source, /<AppSelect/);
    assert.doesNotMatch(source, /Preferred use/);
    assert.doesNotMatch(source, /preferredUse/);
  }
});

test('admin inventory keeps a product visual when string media is absent', async () => {
  const card = await readFile(
    new URL('components/admin/inventory/AdminInventoryCard.tsx', mobileRoot),
    'utf8',
  );

  assert.match(card, /StringProductImage/);
  assert.doesNotMatch(card, /No photo/);
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
      'app/admin/settings.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  for (const source of sources) {
    assert.match(source, /<Switch/);
  }
});

test('player settings stay focused on security after low-value account controls are removed', async () => {
  const settings = await readFile(
    new URL('app/player/settings.tsx', mobileRoot),
    'utf8',
  );

  assert.match(settings, /Update password/);
  assert.doesNotMatch(
    settings,
    /Data choices|privacy|notification preferences|delete account request/i,
  );
});

test('fixed footers do not reserve the tab bar twice', async () => {
  const appScreen = await readFile(
    new URL('components/shared/AppScreen.tsx', mobileRoot),
    'utf8',
  );

  assert.doesNotMatch(
    appScreen,
    /marginBottom:\s*Math\.max\(insets\.bottom,\s*tabBarHeight\)\s*\+\s*4/,
  );
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
  const [answerCard, chatbot, adminAssistant] = await Promise.all(
    [
      'components/agent/AgentAnswerCard.tsx',
      'app/player/chatbot.tsx',
      'app/admin/assistant.tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.match(answerCard, /const showEvidenceStatus = false/);
  assert.match(answerCard, /showEvidenceStatus \?/);
  assert.match(chatbot, /label="Contact human support"/);
  assert.match(chatbot, /router\.push\('\/player\/chat'\)/);
  assert.match(adminAssistant, /label="Generate daily briefing"/);
  assert.match(adminAssistant, /DAILY_BRIEFING_PROMPT/);
});

test('admin recommendation details hide internal provenance noise', async () => {
  const detail = await readFile(
    new URL('app/admin/recommendations/[runId].tsx', mobileRoot),
    'utf8',
  );

  assert.doesNotMatch(
    detail,
    /Rationale summary|community_snapshot_version|cf_shadow|sha256|Algorithm Family/,
  );
  assert.doesNotMatch(
    detail,
    /Submitted recommendation request|Resolved profile snapshot|requestItems|profileItems/,
  );
  assert.match(detail, /eyebrow="Ranked output"/);
  assert.match(detail, /Score breakdown/);
});

test('trending strings preserve drag-to-scroll behavior', async () => {
  const trending = await readFile(
    new URL('components/player/TrendingStrings.tsx', mobileRoot),
    'utf8',
  );

  assert.match(trending, /horizontal/);
  assert.match(trending, /onPointerDown=\{handlePointerDown\}/);
  assert.match(trending, /onPointerMove=\{handlePointerMove\}/);
  assert.match(trending, /scrollTo\(\{\s*x:/);
});

test('booking detail returns to the booking list', async () => {
  const detail = await readFile(
    new URL('app/player/bookings/[id].tsx', mobileRoot),
    'utf8',
  );

  assert.match(detail, /backAccessibilityLabel="Back to bookings"/);
  assert.match(detail, /onBackPress=\{\(\) => router\.replace\('\/player\/bookings'\)\}/);
  assert.doesNotMatch(detail, /onBackPress=\{\(\) => router\.back\(\)\}/);
});

test('booking list exposes a direct check-in shortcut', async () => {
  const [bookings, bookingCard, detail] = await Promise.all(
    [
      'app/player/(tabs)/bookings.tsx',
      'components/booking/BookingCard.tsx',
      'app/player/bookings/[id].tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.match(bookings, /onNextStepPress=/);
  assert.match(bookings, /\/player\/check-in\?bookingId=\$\{item\.id\}/);
  assert.match(bookingCard, /Show check-in for booking/);
  assert.match(detail, /label="Show check-in"/);
  assert.match(detail, /\/player\/check-in\?bookingId=\$\{booking\.id\}/);
});

test('booking confirmation opens payment choices without reopening setup', async () => {
  const [summary, payment, detail] = await Promise.all(
    [
      'app/player/bookings/summary.tsx',
      'app/player/payments/[bookingId].tsx',
      'app/player/bookings/[id].tsx',
    ].map((file) => readFile(new URL(file, mobileRoot), 'utf8')),
  );

  assert.match(summary, /label="Confirm booking & pay"/);
  assert.match(summary, /const paymentPath = `\/player\/payments\/\$\{booking\.id\}`/);
  assert.match(summary, /photoUploadFailed \? `\$\{paymentPath\}\?photoUpload=failed` : paymentPath/);
  assert.match(payment, /method: 'qr_transfer'/);
  assert.match(payment, /method: 'cash'/);
  assert.match(payment, /method: 'wallet_balance'/);
  assert.match(payment, /router\.replace\(`\/player\/bookings\/\$\{booking\.id\}`\)/);
  assert.match(detail, /booking\.paymentStatus !== 'paid'/);
});

test('string detail keeps mobile information hierarchy compact', async () => {
  const detail = await readFile(
    new URL('app/player/strings/[id].tsx', mobileRoot),
    'utf8',
  );

  assert.match(detail, /aspect-\[3\/2\]/);
  assert.match(detail, /<AppRadarChart data=\{selectedString\.ratings\} size=\{260\} \/>/);
  assert.match(detail, /className="mb-8 mt-6 flex-row gap-2\.5"/);
  assert.doesNotMatch(detail, /aspect-\[4\/3\]|className="mb-12 mt-10 flex-row gap-3"/);
});

test('string detail uses the grounded Agent for its introduction', async () => {
  const detail = await readFile(
    new URL('app/player/strings/[id].tsx', mobileRoot),
    'utf8',
  );

  assert.match(detail, /AgentAnswerCard/);
  assert.match(detail, /context: \{ surface: 'chatbot', catalog_id: selectedStringId \}/);
  assert.match(detail, /eyebrow="StringSense AI"/);
  assert.doesNotMatch(detail, /The match logic|Saved scorer reason|Deep Reasoning/);
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
  assert.match(home, /min-h-\[76px\] flex-1 items-center/);
  assert.doesNotMatch(home, /flex-row flex-wrap gap-3/);
  assert.match(home, /Find your next string/);
  assert.doesNotMatch(home, /playerBookings\.length\} logged/);
  assert.doesNotMatch(home, /eyebrow="ESSENTIALS"/);
  assert.doesNotMatch(profile, /More player tools|ALL FEATURES/);
  assert.match(profile, /title="Your setup"/);
  assert.match(profile, /title="Your space"/);
  assert.doesNotMatch(profile, /Account settings|Profile note/);
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
  assert.match(analytics, /7-day comparison|30 days|previous_period_bookings/);
  assert.match(adminDashboard, /pending_payment_count|low_stock_count|unread_chats/);
  assert.match(adminDashboard, /\/admin\/payments|\/admin\/inventory|\/admin\/chat/);
  assert.match(businessHours, /title="Temporary closures"/);
  assert.match(businessHours, /label="Add closed date"/);
  assert.match(businessHours, /Only today or future dates can be added/);
  assert.match(businessHours, /label="Month"/);
  assert.doesNotMatch(businessHours, /Comma-separated YYYY-MM-DD dates/);
  assert.doesNotMatch(settings, /Default service price|Service fee \(RM\)/);
  assert.doesNotMatch(settings, /Default title|Default body/);
  assert.doesNotMatch(bookingSummary, /Service fee|defaultServicePrice/);
  assert.doesNotMatch(payment, /Service fee|service_fee/);
  assert.doesNotMatch(tools, /\/player\/settings/);
  assert.doesNotMatch(tools, /\/player\/profile\/edit/);
  assert.doesNotMatch(recommendation, /Saved Priority Weights/);
  assert.match(results, /StringProductImage/);
  assert.match(results, /Why this fits/);
  assert.doesNotMatch(results, /Score model/);
  assert.match(adminDashboard, /title="Needs attention"/);
  assert.match(adminDashboard, /label="Search tools"/);
});
