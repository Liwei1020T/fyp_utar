import type { BusinessHours } from '../types/domain';

export const MOCK_BUSINESS_HOURS: BusinessHours[] = [
  {
    vendorId: 'admin-001',
    days: [
      { day: 'Monday', isOpen: true, openTime: '11:00', closeTime: '20:00', breakStart: '15:00', breakEnd: '16:00', slotDurationMinutes: 30, maxBookingsPerSlot: 3 },
      { day: 'Tuesday', isOpen: true, openTime: '11:00', closeTime: '20:00', breakStart: '15:00', breakEnd: '16:00', slotDurationMinutes: 30, maxBookingsPerSlot: 3 },
      { day: 'Wednesday', isOpen: true, openTime: '11:00', closeTime: '20:00', breakStart: '15:00', breakEnd: '16:00', slotDurationMinutes: 30, maxBookingsPerSlot: 3 },
      { day: 'Thursday', isOpen: true, openTime: '11:00', closeTime: '21:00', breakStart: '15:00', breakEnd: '16:00', slotDurationMinutes: 30, maxBookingsPerSlot: 3 },
      { day: 'Friday', isOpen: true, openTime: '11:00', closeTime: '21:00', breakStart: '15:00', breakEnd: '16:00', slotDurationMinutes: 30, maxBookingsPerSlot: 4 },
      { day: 'Saturday', isOpen: true, openTime: '10:00', closeTime: '21:00', breakStart: '14:00', breakEnd: '15:00', slotDurationMinutes: 30, maxBookingsPerSlot: 4 },
      { day: 'Sunday', isOpen: true, openTime: '10:00', closeTime: '18:00', breakStart: '13:30', breakEnd: '14:30', slotDurationMinutes: 30, maxBookingsPerSlot: 3 },
    ],
    specialClosedDates: ['2026-04-14'],
  },
];
