const test = require('node:test');
const assert = require('node:assert/strict');

const {
  BOOKING_STATUS_TRANSITIONS,
  assertBookingStatusTransition,
} = require('../dist/bookings/booking-status.js');

test('booking transitions match the final workflow', () => {
  assert.deepEqual(BOOKING_STATUS_TRANSITIONS.pending, [
    'confirmed',
    'rejected',
    'cancelled',
  ]);
  assert.deepEqual(BOOKING_STATUS_TRANSITIONS.ready_for_pickup, [
    'picked_up',
    'cancelled',
  ]);
});

test('illegal booking transition throws', () => {
  assert.throws(
    () => assertBookingStatusTransition('pending', 'picked_up'),
    /Invalid booking status transition/,
  );
});
