import type { NotificationPreferences, VendorSettings } from '../types/domain';

export const MOCK_NOTIFICATION_PREFERENCES: NotificationPreferences[] = [
  {
    userId: 'player-001',
    booking: true,
    payment: true,
    service: true,
    chat: true,
    recommendation: false,
  },
  {
    userId: 'player-002',
    booking: true,
    payment: true,
    service: true,
    chat: true,
    recommendation: true,
  },
  {
    userId: 'player-003',
    booking: true,
    payment: true,
    service: false,
    chat: true,
    recommendation: true,
  },
];

export const MOCK_VENDOR_SETTINGS: VendorSettings[] = [
  {
    vendorId: 'vendor-001',
    storeName: 'Apex String Lab',
    storeContact: '+60 12-999 4421',
    supportText: 'Ask us about tension pairing, string feel, or drop-off timing and we will reply in the vendor chat queue.',
    paymentNotes: 'Full payment is required to confirm every booking in this FYP 1 prototype.',
    bookingNotes: 'Drop-off slots are previewed from business hours and capacity settings.',
    storePolicyText: 'Reschedule and cancellation are allowed only before payment is completed. Collection reminders remain mock-only in FYP 1.',
    address: 'Level 2, Jalil Sports Hub, Bukit Jalil, Kuala Lumpur',
  },
];
