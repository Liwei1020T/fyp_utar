import type { BookingSlot } from '../types/domain';

const SLOT_DATA: Array<{
  id: string;
  date: string;
  time: string;
  capacity: number;
  availableSpots: number;
  label: string;
  dayLabel: string;
}> = [
  { id: 'slot-001', date: '2026-04-05', time: '10:00', capacity: 3, availableSpots: 2, label: '10:00 AM', dayLabel: 'Sunday' },
  { id: 'slot-002', date: '2026-04-05', time: '11:00', capacity: 3, availableSpots: 2, label: '11:00 AM', dayLabel: 'Sunday' },
  { id: 'slot-003', date: '2026-04-05', time: '14:00', capacity: 3, availableSpots: 1, label: '2:00 PM', dayLabel: 'Sunday' },
  { id: 'slot-004', date: '2026-04-05', time: '15:30', capacity: 3, availableSpots: 0, label: '3:30 PM', dayLabel: 'Sunday' },
  { id: 'slot-005', date: '2026-04-05', time: '17:00', capacity: 3, availableSpots: 3, label: '5:00 PM', dayLabel: 'Sunday' },
  { id: 'slot-006', date: '2026-04-06', time: '11:00', capacity: 3, availableSpots: 3, label: '11:00 AM', dayLabel: 'Monday' },
  { id: 'slot-007', date: '2026-04-06', time: '12:00', capacity: 3, availableSpots: 2, label: '12:00 PM', dayLabel: 'Monday' },
  { id: 'slot-008', date: '2026-04-06', time: '16:00', capacity: 3, availableSpots: 1, label: '4:00 PM', dayLabel: 'Monday' },
  { id: 'slot-009', date: '2026-04-07', time: '11:30', capacity: 3, availableSpots: 2, label: '11:30 AM', dayLabel: 'Tuesday' },
  { id: 'slot-010', date: '2026-04-07', time: '17:30', capacity: 3, availableSpots: 2, label: '5:30 PM', dayLabel: 'Tuesday' },
];

export const MOCK_BOOKING_SLOTS: BookingSlot[] = SLOT_DATA.map((slot) => ({
  vendorId: 'vendor-001',
  ...slot,
}));
