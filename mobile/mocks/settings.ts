import type { AdminSettings, NotificationPreferences } from '../types/domain';

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

export const MOCK_ADMIN_SETTINGS: AdminSettings[] = [
  {
    adminId: 'admin-001',
    storeName: 'Apex String Lab',
    storeContact: '+60 12-999 4421',
    supportText: 'Ask us about tension pairing, string feel, or drop-off timing and we will reply from the admin operations desk.',
    paymentNotes: 'Payment handling stays outside the FYP1 demo flow.',
    bookingNotes: 'Drop-off slots are previewed from business hours and capacity settings.',
    storePolicyText: 'Reschedule or cancellation is allowed before the admin starts work on the racket. Collection reminders remain mock-only in FYP1.',
    address: 'Level 2, Jalil Sports Hub, Bukit Jalil, Kuala Lumpur',
  },
];

export const MOCK_VENDOR_SETTINGS = MOCK_ADMIN_SETTINGS;
