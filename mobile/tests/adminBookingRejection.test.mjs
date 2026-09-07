import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const mobileRoot = new URL('../', import.meta.url);

test('admin booking page exposes terminal status reasons', async () => {
  const source = await readFile(
    new URL('app/admin/bookings/[id].tsx', mobileRoot),
    'utf8',
  );

  assert.match(source, /'cancelled',\n  'rejected',\n\] as const/);
  assert.match(source, /awaiting_dropoff: \['in_progress', 'cancelled', 'rejected'\]/);
  assert.match(source, /in_progress: \['ready_for_collection', 'cancelled'\]/);
  assert.match(source, /Cancellation reason/);
  assert.match(source, /if \(isClosing && !statusNote\.trim\(\)\)/);
  assert.match(
    source,
    /note: isClosing \? statusNote\.trim\(\) \|\| undefined : undefined/,
  );
});
