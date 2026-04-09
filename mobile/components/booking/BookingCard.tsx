import * as React from 'react';
import { Pressable, View } from 'react-native';
import { CalendarDays, ChevronRight, Clock3, ArrowRightCircle } from 'lucide-react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import { getBookingStatusVariant } from '../ui/theme';
import {
  formatBookingOrderCode,
  formatBookingStatus,
  formatCurrency,
} from '../../lib/formatters';
import type { Booking, BookingStatus } from '../../types/domain';

interface BookingCardProps {
  booking: Booking;
  stringLabel: string;
  adminLabel?: string;
  onPress?: () => void;
}

const getNextStep = (status: BookingStatus, date?: string, time?: string): string => {
  switch (status) {
    case 'pending':
      return 'Next: Awaiting vendor confirmation';
    case 'confirmed':
    case 'awaiting_dropoff':
      return `Next: Drop off your racket at ${time || 'scheduled time'}`;
    case 'in_progress':
      return 'Next: Waiting for stringing completion';
    case 'ready_for_collection':
      return 'Next: Ready for collection';
    case 'completed':
      return `Completed on ${date || ''}`;
    case 'cancelled':
      return 'This booking was cancelled';
    case 'pending_payment':
      return 'Next: Complete payment to finish';
    default:
      return 'Next: Follow admin instructions';
  }
};

export function BookingCard({ booking, stringLabel, adminLabel, onPress }: BookingCardProps) {
  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);
  const content = (
    <AppCard variant="elevated" padding="sm">
      <View className="gap-2">
        <View className="flex-row items-center justify-between">
          <HeroText className="text-[10px] font-bold uppercase tracking-[0.1em] text-neutral-400">
            #{orderCode}
          </HeroText>
          <AppChip
            label={formatBookingStatus(booking.status)}
            variant={getBookingStatusVariant(booking.status)}
            size="sm"
          />
        </View>

        <View className="flex-row justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
              {booking.racketBrand} {booking.racketModel}
            </HeroText>
            <HeroText className="text-xs text-neutral-500">
              {stringLabel} • {booking.requestedTension} lbs
            </HeroText>
            {adminLabel ? (
              <HeroText className="text-xs font-medium text-primary-600">
                {adminLabel}
              </HeroText>
            ) : null}
          </View>
          <View className="items-end">
            <HeroText className="text-sm font-bold text-neutral-900">
              {formatCurrency(booking.totalAmount)}
            </HeroText>
            <View className="mt-1 flex-row items-center gap-1">
              <CalendarDays size={10} color="#94A3B8" />
              <HeroText className="text-[10px] font-medium text-neutral-500">
                {booking.dropOffDate}
              </HeroText>
            </View>
          </View>
        </View>

        <View className="mt-1 flex-row items-center gap-2 rounded-xl bg-primary-50 px-3 py-2">
          <ArrowRightCircle size={14} color="#2F64B6" />
          <HeroText className="flex-1 text-[11px] font-semibold text-primary-800">
            {getNextStep(booking.status, booking.dropOffDate, booking.dropOffTime)}
          </HeroText>
          {onPress && <ChevronRight size={14} color="#2F64B6" />}
        </View>
      </View>
    </AppCard>
  );

  if (!onPress) {
    return content;
  }

  return (
    <Pressable onPress={onPress}>
      <View className="mb-3">
        {content}
      </View>
    </Pressable>
  );
}
