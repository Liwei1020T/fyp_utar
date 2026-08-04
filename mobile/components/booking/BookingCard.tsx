import * as React from 'react';
import { Pressable, View } from 'react-native';
import {
  CalendarDays,
  ChevronRight,
  ArrowRightCircle,
  CheckCircle2,
  PackageCheck,
  TimerReset,
  CircleDashed,
} from 'lucide-react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import { appChromeColors, getBookingStatusVariant } from '../ui/theme';
import {
  formatBookingOrderCode,
  formatBookingStatus,
  formatCurrency,
  formatDateLabel,
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
      return `Next: Drop off before ${time || 'scheduled time'}`;
    case 'in_progress':
      return 'Next: Waiting for stringing completion';
    case 'ready_for_collection':
      return 'Next: Ready for collection';
    case 'completed':
      return `Completed on ${date || 'scheduled date'}`;
    case 'cancelled':
      return 'This booking was cancelled';
    case 'rejected':
      return 'This booking was declined by the shop';
    case 'pending_payment':
      return 'Next: Complete payment to finish';
    default:
      return 'Next: Follow admin instructions';
  }
};

const getBookingPriceLabel = (booking: Booking): string => {
  if (booking.totalAmount > 0) {
    return formatCurrency(booking.totalAmount);
  }

  switch (booking.status) {
    case 'awaiting_dropoff':
      return 'Quoted at shop';
    case 'in_progress':
      return 'Vendor quote';
    default:
      return 'Price pending';
  }
};

const getStatusStripTone = (status: BookingStatus) => {
  switch (status) {
    case 'awaiting_dropoff':
      return {
        container: 'bg-warning-50 border-warning-100',
        text: 'text-warning-700',
        iconColor: '#B67D21',
        Icon: TimerReset,
      };
    case 'ready_for_collection':
      return {
        container: 'bg-success-50 border-success-100',
        text: 'text-success-700',
        iconColor: '#2F7A58',
        Icon: PackageCheck,
      };
    case 'completed':
      return {
        container: 'bg-complete-50 border-complete-100',
        text: 'text-complete-700',
        iconColor: '#6D8477',
        Icon: CheckCircle2,
      };
    case 'pending':
    case 'pending_payment':
      return {
        container: 'bg-primary-50 border-primary-100',
        text: 'text-primary-800',
        iconColor: appChromeColors.primary,
        Icon: CircleDashed,
      };
    case 'cancelled':
    case 'rejected':
      return {
        container: 'bg-danger-50 border-danger-100',
        text: 'text-danger-700',
        iconColor: '#B42318',
        Icon: CircleDashed,
      };
    case 'confirmed':
    case 'in_progress':
    default:
      return {
        container: 'bg-primary-50 border-primary-100',
        text: 'text-primary-800',
        iconColor: appChromeColors.primary,
        Icon: ArrowRightCircle,
      };
  }
};

export function BookingCard({ booking, stringLabel, adminLabel, onPress }: BookingCardProps) {
  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);
  const stripTone = getStatusStripTone(booking.status);
  const StatusIcon = stripTone.Icon;
  const stringSpec = `${stringLabel} • ${booking.requestedTension} lbs`;
  const racketName = `${booking.racketBrand} ${booking.racketModel}`;
  const bookingDateLabel = formatDateLabel(booking.dropOffDate);
  const priceLabel = getBookingPriceLabel(booking);
  const content = (
    <AppCard variant="elevated" padding="sm">
      <View className="gap-2.5">
        <View className="flex-row items-start justify-between gap-3">
          <HeroText className="flex-1 pr-2 text-[10px] font-semibold uppercase tracking-normal text-neutral-400">
            #{orderCode}
          </HeroText>
          <AppChip
            label={formatBookingStatus(booking.status)}
            variant={getBookingStatusVariant(booking.status)}
            size="sm"
            className="shrink-0"
          />
        </View>

        <View className="gap-1.5">
          <View className="min-w-0">
            <HeroText className="text-[17px] font-bold tracking-normal text-neutral-950">
              {racketName}
            </HeroText>
            <HeroText className="mt-0.5 text-[12px] font-medium text-neutral-600">
              {stringSpec}
            </HeroText>
            {adminLabel ? (
              <HeroText className="mt-1 text-[11px] font-medium text-neutral-500">
                {adminLabel}
              </HeroText>
            ) : null}
          </View>
          <View className="flex-row items-center gap-1.5">
            <HeroText className="text-[12px] font-semibold text-neutral-700">
              {priceLabel}
            </HeroText>
            <HeroText className="text-[11px] font-semibold text-neutral-300">
              •
            </HeroText>
            <CalendarDays size={11} color="#94A3B8" />
            <HeroText className="text-[11px] font-semibold text-neutral-500">
              {bookingDateLabel}
            </HeroText>
          </View>
        </View>

        <View
          className={`mt-0.5 flex-row items-center gap-2 rounded-lg border px-3 py-2 ${stripTone.container}`}
        >
          <StatusIcon size={14} color={stripTone.iconColor} />
          <HeroText className={`flex-1 text-[11px] font-semibold ${stripTone.text}`}>
            {getNextStep(booking.status, booking.dropOffDate, booking.dropOffTime)}
          </HeroText>
          {onPress ? <ChevronRight size={14} color={stripTone.iconColor} /> : null}
        </View>
      </View>
    </AppCard>
  );

  if (!onPress) {
    return content;
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`Booking ${orderCode}, ${racketName}, ${formatBookingStatus(booking.status)}`}
      accessibilityHint="Open booking details"
      onPress={onPress}
    >
      <View className="mb-3">
        {content}
      </View>
    </Pressable>
  );
}
