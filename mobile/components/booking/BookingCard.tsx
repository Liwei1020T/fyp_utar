import React from 'react';
import { Pressable, View } from 'react-native';
import { CalendarDays, ChevronRight, Clock3 } from 'lucide-react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import { getBookingStatusVariant } from '../ui/theme';
import { formatBookingStatus, formatCurrency } from '../../lib/formatters';
import type { Booking } from '../../types/domain';

interface BookingCardProps {
  booking: Booking;
  stringLabel: string;
  adminLabel?: string;
  onPress?: () => void;
}

export function BookingCard({ booking, stringLabel, adminLabel, onPress }: BookingCardProps) {
  const content = (
    <AppCard variant="elevated" padding="md">
      <View className="gap-4">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
              Booking #{booking.id}
            </HeroText>
            <HeroText className="mt-2 text-xl font-bold tracking-tight text-neutral-950">
              {booking.racketBrand} {booking.racketModel}
            </HeroText>
            <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
              {stringLabel} at {booking.requestedTension} lbs
            </HeroText>
            {adminLabel ? (
              <HeroText className="mt-1 text-sm text-neutral-500">
                {adminLabel}
              </HeroText>
            ) : null}
          </View>
          <View className="max-w-[40%] items-end gap-2">
            <AppChip label={formatBookingStatus(booking.status)} variant={getBookingStatusVariant(booking.status)} />
          </View>
        </View>

        <View className="gap-3 rounded-[20px] bg-app-muted px-4 py-3 md:flex-row md:items-center md:justify-between">
          <View className="flex-row items-center gap-2">
            <CalendarDays size={14} color="#64748B" />
            <HeroText className="text-sm font-medium text-neutral-700">
              {booking.dropOffDate}
            </HeroText>
          </View>
          <View className="flex-row items-center gap-2">
            <Clock3 size={14} color="#64748B" />
            <HeroText className="text-sm font-medium text-neutral-700">
              {booking.dropOffTime}
            </HeroText>
          </View>
        </View>

        <View className="flex-row items-center justify-between">
          <HeroText className="text-sm text-neutral-500">
            Service estimate
          </HeroText>
          <HeroText className="text-sm font-semibold text-neutral-900">
            Total {formatCurrency(booking.totalAmount)}
          </HeroText>
        </View>
      </View>
    </AppCard>
  );

  if (!onPress) {
    return content;
  }

  return (
    <Pressable onPress={onPress}>
      <View>
        {content}
        <View className="absolute right-6 top-6 h-10 w-10 items-center justify-center rounded-full bg-primary-50">
          <ChevronRight size={18} color="#2F64B6" />
        </View>
      </View>
    </Pressable>
  );
}
