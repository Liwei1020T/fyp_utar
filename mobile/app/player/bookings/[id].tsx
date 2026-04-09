import React, { useEffect } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { CalendarClock, Circle, CircleCheck, TimerReset } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppDetailList } from '../../../components/shared/AppDetailList';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { BookingUpdates } from '../../../components/booking/BookingUpdates';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useStrings,
} from '../../../store/appStore';
import { getAdminById, getStringById } from '../../../services/mockAppService';
import {
  formatBookingOrderCode,
  formatBookingStatus,
  formatCurrency,
} from '../../../lib/formatters';
import { getBookingStatusVariant } from '../../../components/ui/theme';
import { backendApi } from '../../../services/backendApi';
import { mapBackendBookingToBooking } from '../../../services/backendMappers';
import type { Booking, BookingStatus } from '../../../types/domain';

const TRACKING_STAGES: Array<{
  key: 'confirmed' | 'dropoff' | 'in_progress' | 'ready_for_collection' | 'completed';
  label: string;
}> = [
  { key: 'confirmed', label: 'Booking confirmed' },
  { key: 'dropoff', label: 'Drop-off scheduled' },
  { key: 'in_progress', label: 'In progress' },
  { key: 'ready_for_collection', label: 'Ready for collection' },
  { key: 'completed', label: 'Completed' },
];

function getCurrentStageKey(status: BookingStatus) {
  switch (status) {
    case 'pending':
    case 'pending_payment':
    case 'confirmed':
      return 'confirmed';
    case 'awaiting_dropoff':
      return 'dropoff';
    case 'in_progress':
      return 'in_progress';
    case 'ready_for_collection':
      return 'ready_for_collection';
    case 'completed':
      return 'completed';
    case 'cancelled':
    default:
      return 'confirmed';
  }
}

function getStageState(stageKey: (typeof TRACKING_STAGES)[number]['key'], booking: Booking) {
  const currentIndex = TRACKING_STAGES.findIndex((stage) => stage.key === getCurrentStageKey(booking.status));
  const stageIndex = TRACKING_STAGES.findIndex((stage) => stage.key === stageKey);

  if (booking.status === 'cancelled') {
    return 'upcoming' as const;
  }

  if (stageIndex < currentIndex) {
    return 'complete' as const;
  }

  if (stageIndex === currentIndex) {
    return 'current' as const;
  }

  return 'upcoming' as const;
}

function getNextStepSummary(status: BookingStatus) {
  switch (status) {
    case 'pending':
    case 'pending_payment':
      return 'Complete booking confirmation to lock in your drop-off slot.';
    case 'confirmed':
    case 'awaiting_dropoff':
      return 'Bring your racket and show the booking reference at the counter.';
    case 'in_progress':
      return 'Waiting for stringing completion from the shop.';
    case 'ready_for_collection':
      return 'Your racket is ready. Head to the shop for collection.';
    case 'completed':
      return 'Service completed. You can review the final updates anytime.';
    case 'cancelled':
    default:
      return 'This booking is no longer progressing.';
  }
}

function getPricingLabel(amount: number, fallback: string) {
  return amount > 0 ? formatCurrency(amount) : fallback;
}

function getDropOffNote(booking: Booking) {
  return `Use reference ${booking.checkInReference} at counter check-in.`;
}

function getQueueNote(booking: Booking) {
  if (booking.queuePosition > 0) {
    return `Current queue: #${booking.queuePosition}. Updates appear here as the shop progresses your order.`;
  }

  return 'Queue and service updates appear here as the shop progresses your order.';
}

export default function PlayerBookingDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const bookings = useBookings();
  const strings = useStrings();
  const token = useBackendAccessToken();
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);
  const booking = bookings.find((item) => item.id === params.id);

  useEffect(() => {
    if (!token || !params.id) {
      return;
    }

    const bookingId = params.id;
    let cancelled = false;

    const hydrateBooking = async () => {
      try {
        const freshBooking = await backendApi.fetchBooking(token, bookingId);
        if (cancelled) {
          return;
        }
        const priceByStringId = new Map(strings.map((item) => [item.id, item.price]));
        const mapped = mapBackendBookingToBooking(freshBooking, priceByStringId);
        const currentBookings = useAppStore.getState().liveBookings;
        setLiveBookings(
          currentBookings.some((item) => item.id === mapped.id)
            ? currentBookings.map((item) => (item.id === mapped.id ? mapped : item))
            : [mapped, ...currentBookings],
        );
      } catch (error) {
        console.warn('Failed to refresh live player booking detail', error);
      }
    };

    void hydrateBooking();

    return () => {
      cancelled = true;
    };
  }, [params.id, setLiveBookings, strings, token]);

  if (!booking) {
    return (
      <AppScreen title="Booking not found">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            We couldn&apos;t find this booking.
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

  const stringItem = getStringById(booking.stringId);
  const admin = getAdminById(booking.adminId);
  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);

  return (
    <AppScreen
      headerVariant="secondary"
      title={`Booking ${orderCode}`}
      subtitle="Booking info and live service progress"
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
              Service status
            </HeroText>
            <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-white">
              {formatBookingStatus(booking.status)}
            </HeroText>
            <HeroText className="mt-2 text-sm text-primary-100">
              Drop-off on {booking.dropOffDate} at {booking.dropOffTime}
            </HeroText>
            <View className="mt-4 rounded-[20px] bg-white/10 px-4 py-3">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-100">
                Next
              </HeroText>
              <HeroText className="mt-1 text-sm font-medium leading-6 text-white">
                {getNextStepSummary(booking.status)}
              </HeroText>
            </View>
          </View>
        </View>
      </AppCard>

      <AppSection eyebrow="Overview" title="Booking summary" variant="compact">
        <AppDetailList
          items={[
            {
              label: 'Status',
              value: (
                <AppChip
                  label={formatBookingStatus(booking.status)}
                  variant={getBookingStatusVariant(booking.status)}
                  className="self-start md:self-end"
                />
              ),
            },
            { label: 'Vendor', value: admin?.businessName ?? 'Assigned shop' },
            { label: 'Requested tension', value: `${booking.requestedTension} lbs` },
            { label: 'Reference', value: booking.checkInReference || 'Assigned at check-in' },
          ]}
          className="overflow-hidden"
        />
      </AppSection>

      <AppSection eyebrow="Setup" title="String and racket setup" variant="compact">
        <AppDetailList
          items={[
            {
              label: 'String',
              value: `${stringItem?.brand ?? ''} ${stringItem?.model ?? ''}`.trim(),
            },
            {
              label: 'Racket',
              value: `${booking.racketBrand} ${booking.racketModel}`,
            },
            {
              label: 'Requested tension',
              value: `${booking.requestedTension} lbs`,
            },
          ]}
        />
      </AppSection>

      <AppSection eyebrow="Progress" title="Tracking preview" variant="compact">
        <AppCard variant="elevated" padding="md">
          <View className="gap-3">
            {TRACKING_STAGES.map((stage) => {
              const state = getStageState(stage.key, booking);
              const isCurrent = state === 'current';
              const isComplete = state === 'complete';

              return (
                <View
                  key={stage.key}
                  className={`flex-row items-center gap-3 rounded-[18px] px-2 py-1.5 ${isCurrent ? 'bg-primary-50/80' : ''}`}
                >
                  <View className="h-7 w-7 items-center justify-center">
                    {isComplete ? (
                      <CircleCheck size={20} color="#2F64B6" />
                    ) : isCurrent ? (
                      <Circle size={18} color="#2F64B6" fill="#2F64B6" />
                    ) : (
                      <Circle size={18} color="#C4D0E0" />
                    )}
                  </View>
                  <HeroText
                    className={`text-sm leading-6 ${isCurrent ? 'font-semibold text-primary-700' : isComplete ? 'font-medium text-neutral-700' : 'text-neutral-400'}`}
                  >
                    {stage.label}
                  </HeroText>
                </View>
              );
            })}
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Drop-off" title="Check-in notes" variant="compact">
        <AppCard variant="subtle" padding="md">
          <View className="gap-3">
            <View className="flex-row items-start gap-3">
              <CalendarClock size={18} color="#2F64B6" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                {getDropOffNote(booking)}
              </HeroText>
            </View>
            <View className="h-px bg-white/70" />
            <View className="flex-row items-start gap-3">
              <TimerReset size={18} color="#22766D" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                {getQueueNote(booking)}
              </HeroText>
            </View>
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Pricing" title="Pricing" variant="compact">
        <AppDetailList
          items={[
            {
              label: 'String fee',
              value: getPricingLabel(booking.stringFee, 'Quoted at shop'),
            },
            {
              label: 'Service fee',
              value: getPricingLabel(booking.serviceFee, 'To be confirmed'),
            },
            {
              label: 'Estimated total',
              value: getPricingLabel(booking.totalAmount, 'Vendor quote'),
            },
          ]}
        />
      </AppSection>

      <AppSection eyebrow="Updates" title="Admin updates" variant="compact">
        <BookingUpdates updates={booking.updates} />
      </AppSection>

      <AppSection eyebrow="Note" title="FYP1 booking flow" variant="compact">
        <AppCard variant="subtle" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-700">
            FYP1 booking covers drop-off, status updates, and collection tracking.
          </HeroText>
        </AppCard>
      </AppSection>

      {booking.notes ? (
        <AppSection eyebrow="Notes" title="Service instructions" variant="compact">
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-700">{booking.notes}</HeroText>
          </AppCard>
        </AppSection>
      ) : null}

      <View className="mb-12 mt-7 gap-3">
        <AppButton
          label="View tracking"
          variant="primary"
          size="lg"
          onPress={() => router.push(`/player/bookings/${booking.id}/tracking`)}
        />
      </View>
    </AppScreen>
  );
}
