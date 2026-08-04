import React from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ArrowRight, CalendarClock, Clock3 } from 'lucide-react-native';
import { View } from 'react-native';
import { AppButton } from '../../../../components/ui/AppButton';
import { AppCard } from '../../../../components/ui/AppCard';
import { AppChip } from '../../../../components/ui/AppChip';
import { HeroText } from '../../../../components/ui/heroui';
import { AppScreen } from '../../../../components/shared/AppScreen';
import { AppSection } from '../../../../components/shared/AppSection';
import { TrackingTimeline } from '../../../../components/tracking/TrackingTimeline';
import { formatBookingOrderCode, formatBookingStatus } from '../../../../lib/formatters';
import { useBookings } from '../../../../store/appStore';
import type { Booking, BookingStatus } from '../../../../types/domain';

const NEXT_STEP_LABELS: Partial<Record<BookingStatus, string>> = {
  confirmed: 'Awaiting drop-off',
  awaiting_dropoff: 'Stringing started',
  in_progress: 'Ready for collection',
  ready_for_collection: 'Completed',
  completed: 'Service closed',
  cancelled: 'Booking closed',
  rejected: 'Review rejection reason',
};

function formatTrackingDateTime(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString('en-MY', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatDropOffDateTime(booking: Booking) {
  const date = new Date(`${booking.dropOffDate}T${booking.dropOffTime}:00`);

  if (Number.isNaN(date.getTime())) {
    return `${booking.dropOffDate} ${booking.dropOffTime}`;
  }

  return date.toLocaleString('en-MY', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function getCurrentStatusLabel(status: BookingStatus) {
  switch (status) {
    case 'in_progress':
      return 'Stringing started';
    default:
      return formatBookingStatus(status);
  }
}

export default function BookingTrackingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const bookings = useBookings();
  const booking = bookings.find((item) => item.id === params.id);

  if (!booking) {
    return (
      <AppScreen title="Tracking unavailable">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            This booking is no longer available.
          </HeroText>
          <AppButton
            label="Back to bookings"
            className="mt-6"
            onPress={() => router.replace('/player/bookings')}
          />
        </AppCard>
      </AppScreen>
    );
  }

  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);
  const currentStatus = getCurrentStatusLabel(booking.status);
  const nextStep = NEXT_STEP_LABELS[booking.status] ?? 'Awaiting update';
  const latestEventAt = booking.timeline[booking.timeline.length - 1]?.at ?? booking.createdAt;

  return (
    <AppScreen
      headerVariant="secondary"
      compactHeader
      title="Service tracking"
      subtitle="Live progress from booking to collection."
      showBackButton
      onBackPress={() => router.back()}
      contentContainerClassName="pt-3"
    >
      <View className="gap-4">
        <AppCard variant="elevated" padding="md" className="rounded-[24px]">
          <View className="gap-3">
            <View className="gap-3">
              <View className="flex-row items-start justify-between gap-3">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                  Booking {orderCode}
                </HeroText>
                <AppChip label={currentStatus} variant="primary" className="self-start" />
              </View>
              <HeroText className="text-[24px] font-bold tracking-tight text-neutral-950">
                Your restring journey
              </HeroText>
            </View>

            <View className="flex-row flex-wrap gap-2">
              <View className="rounded-[18px] bg-secondary-50 px-3 py-3" style={{ width: '48%' }}>
                <View className="flex-row items-center gap-2">
                  <Clock3 size={15} color="#2F64B6" />
                  <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-neutral-400" numberOfLines={2}>
                    Current status
                  </HeroText>
                </View>
                <HeroText className="mt-2 text-[14px] font-bold tracking-tight text-neutral-950" numberOfLines={2}>
                  {currentStatus}
                </HeroText>
              </View>

              <View className="rounded-[18px] bg-secondary-50 px-3 py-3" style={{ width: '48%' }}>
                <View className="flex-row items-center gap-2">
                  <ArrowRight size={15} color="#2F64B6" />
                  <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-neutral-400" numberOfLines={2}>
                    Next step
                  </HeroText>
                </View>
                <HeroText className="mt-2 text-[14px] font-bold tracking-tight text-neutral-950" numberOfLines={2}>
                  {nextStep}
                </HeroText>
              </View>

              <View className="rounded-[18px] bg-secondary-50 px-3 py-3" style={{ width: '48%' }}>
                <View className="flex-row items-center gap-2">
                  <CalendarClock size={15} color="#2F64B6" />
                  <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-neutral-400" numberOfLines={2}>
                    Drop-off time
                  </HeroText>
                </View>
                <HeroText className="mt-2 text-[14px] font-bold tracking-tight text-neutral-950" numberOfLines={3}>
                  {formatDropOffDateTime(booking)}
                </HeroText>
              </View>

              <View className="rounded-[18px] bg-secondary-50 px-3 py-3" style={{ width: '48%' }}>
                <View className="flex-row items-center gap-2">
                  <CalendarClock size={15} color="#2F64B6" />
                  <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-neutral-400" numberOfLines={2}>
                    Expected ready
                  </HeroText>
                </View>
                <HeroText className="mt-2 text-[14px] font-bold tracking-tight text-neutral-950" numberOfLines={3}>
                  {booking.expectedCompletionAt
                    ? formatTrackingDateTime(booking.expectedCompletionAt)
                    : '-'}
                </HeroText>
              </View>
            </View>

            <HeroText className="text-[12px] leading-5 text-neutral-500">
              Last update recorded on {formatTrackingDateTime(latestEventAt)}.
            </HeroText>
          </View>
        </AppCard>

        <AppSection
          eyebrow="Timeline"
          title="Service journey"
          subtitle="Every milestone is shown in order so you can see what is done, what is live, and what comes next."
        >
          <TrackingTimeline timeline={booking.timeline} currentStatus={booking.status} />
        </AppSection>
      </View>
    </AppScreen>
  );
}
