import type { VendorAnalyticsSummary } from '../types/domain';

export const MOCK_VENDOR_ANALYTICS: VendorAnalyticsSummary[] = [
  {
    vendorId: 'admin-001',
    weeklyBookings: 42,
    pendingPaymentCount: 4,
    awaitingDropoffCount: 6,
    inProgressCount: 7,
    readyForCollectionCount: 5,
    completedToday: 8,
    lowStockCount: 2,
    unreadChats: 3,
    todayRevenue: 486,
    busySlots: ['Fri 7 PM', 'Sat 11 AM', 'Sun 2 PM'],
    popularStringIds: ['string-001', 'string-003', 'string-004'],
    workloadMix: [
      { label: 'Pending payment', value: 4 },
      { label: 'Awaiting drop-off', value: 6 },
      { label: 'In progress', value: 7 },
      { label: 'Ready for collection', value: 5 },
      { label: 'Completed today', value: 8 },
    ],
  },
];
