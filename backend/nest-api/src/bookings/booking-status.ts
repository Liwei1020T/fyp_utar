import { ConflictException } from '@nestjs/common';
import { BookingStatus } from '@prisma/client';

export const BOOKING_STATUS_TRANSITIONS: Record<BookingStatus, BookingStatus[]> = {
  pending: ['confirmed', 'rejected', 'cancelled'],
  confirmed: ['in_progress', 'cancelled'],
  in_progress: ['ready_for_pickup', 'cancelled'],
  ready_for_pickup: ['picked_up', 'cancelled'],
  picked_up: [],
  cancelled: [],
  rejected: [],
};

export function assertBookingStatusTransition(
  currentStatus: BookingStatus,
  nextStatus: BookingStatus,
): void {
  if (!BOOKING_STATUS_TRANSITIONS[currentStatus].includes(nextStatus)) {
    throw new ConflictException('Invalid booking status transition');
  }
}
