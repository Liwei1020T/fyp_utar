import React from 'react';
import { View } from 'react-native';
import { CheckCheck, Circle } from 'lucide-react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import { formatBookingStatus, formatDateTime } from '../../lib/formatters';
import { getBookingStatusVariant } from '../ui/theme';
import type { BookingStatus, BookingStatusEntry } from '../../types/domain';

interface TrackingTimelineProps {
  timeline: BookingStatusEntry[];
  currentStatus: BookingStatus;
}

export function TrackingTimeline({ timeline, currentStatus }: TrackingTimelineProps) {
  return (
    <View className="gap-3">
      {timeline.map((entry, index) => {
        const isCurrent = entry.status === currentStatus;
        const isLast = index === timeline.length - 1;

        return (
          <AppCard key={`${entry.status}-${entry.at}`} variant={isCurrent ? 'highlighted' : 'elevated'} padding="md">
            <View className="flex-row gap-4">
              <View className="items-center">
                <View className={`h-10 w-10 items-center justify-center rounded-full ${isCurrent ? 'bg-primary-600' : 'bg-neutral-100'}`}>
                  {isCurrent ? (
                    <CheckCheck size={18} color="white" />
                  ) : (
                    <Circle size={16} color="#64748B" fill="#64748B" />
                  )}
                </View>
                {!isLast ? <View className="mt-2 h-8 w-[2px] bg-neutral-200" /> : null}
              </View>
              <View className="flex-1">
                <View className="gap-2 md:flex-row md:items-center md:justify-between">
                  <HeroText className="text-base font-bold tracking-tight text-neutral-950">
                    {entry.title}
                  </HeroText>
                  <AppChip
                    label={formatBookingStatus(entry.status)}
                    variant={getBookingStatusVariant(entry.status)}
                    className="self-start"
                  />
                </View>
                <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
                  {entry.note}
                </HeroText>
                <HeroText className="mt-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
                  {formatDateTime(entry.at)}
                </HeroText>
              </View>
            </View>
          </AppCard>
        );
      })}
    </View>
  );
}
