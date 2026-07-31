import React, { useEffect, useState } from 'react';
import { Alert, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { CalendarClock, Circle, CircleCheck } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useConversations,
  usePayments,
  useStrings,
} from '../../../store/appStore';
import {
  formatBookingOrderCode,
  formatBookingStatus,
  formatDateTime,
} from '../../../lib/formatters';
import { getBookingStatusVariant } from '../../../components/ui/theme';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  mapBackendBookingToBooking,
  mapBackendConversationToConversation,
} from '../../../services/backendMappers';
import type { Booking, BookingStatus } from '../../../types/domain';

const TRACKING_STAGES: {
  key: 'confirmed' | 'dropoff' | 'in_progress' | 'ready_for_collection' | 'completed';
  label: string;
}[] = [
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
    case 'rejected':
    default:
      return 'confirmed';
  }
}

function getStageState(stageKey: (typeof TRACKING_STAGES)[number]['key'], booking: Booking) {
  const currentIndex = TRACKING_STAGES.findIndex((stage) => stage.key === getCurrentStageKey(booking.status));
  const stageIndex = TRACKING_STAGES.findIndex((stage) => stage.key === stageKey);

  if (booking.status === 'cancelled' || booking.status === 'rejected') {
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
    return `${booking.dropOffDate} at ${booking.dropOffTime}`;
  }

  return date.toLocaleString('en-MY', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).replace(',', ' at');
}

function getHeroStatusLabel(status: BookingStatus) {
  switch (status) {
    case 'in_progress':
      return 'In Progress';
    case 'ready_for_collection':
      return 'Ready for Collection';
    default:
      return formatBookingStatus(status);
  }
}

function getNextStepLabel(status: BookingStatus) {
  switch (status) {
    case 'pending':
    case 'pending_payment':
      return 'Waiting for booking confirmation';
    case 'confirmed':
    case 'awaiting_dropoff':
      return 'Waiting for drop-off check-in';
    case 'in_progress':
      return 'Waiting for stringing completion';
    case 'ready_for_collection':
      return 'Waiting for collection';
    case 'completed':
      return 'Service completed';
    case 'cancelled':
      return 'Booking cancelled';
    case 'rejected':
      return 'Booking declined by shop';
    default:
      return 'Booking closed';
  }
}

function getHeroStatusChipClasses(status: BookingStatus) {
  switch (status) {
    case 'completed':
      return {
        className: 'self-start border-[#94A3B8]/45 bg-[#E2E8F0]/18',
        textClassName: 'text-white font-semibold text-xs',
      };
    case 'ready_for_collection':
      return {
        className: 'self-start border-emerald-200/35 bg-emerald-300/18',
        textClassName: 'text-white font-semibold text-xs',
      };
    case 'in_progress':
    case 'confirmed':
      return {
        className: 'self-start border-primary-200/35 bg-primary-300/18',
        textClassName: 'text-white font-semibold text-xs',
      };
    case 'awaiting_dropoff':
    case 'pending':
    case 'pending_payment':
      return {
        className: 'self-start border-amber-200/35 bg-amber-300/18',
        textClassName: 'text-white font-semibold text-xs',
      };
    case 'cancelled':
    case 'rejected':
      return {
        className: 'self-start border-red-200/35 bg-red-300/18',
        textClassName: 'text-white font-semibold text-xs',
      };
    default:
      return {
        className: 'self-start border-white/20 bg-white/15',
        textClassName: 'text-white font-semibold text-xs',
      };
  }
}

function getQuoteStatus(booking: Booking) {
  if (booking.totalAmount > 0 || booking.amountPaid > 0) {
    return 'Quote confirmed';
  }

  return 'Vendor quote pending';
}

function getLatestUpdate(booking: Booking): {
  label: string;
  at: string;
  message: string;
} {
  const latestAdminUpdate = [...booking.updates]
    .filter((item) => item.authorRole === 'admin')
    .sort((left, right) => new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime())[0];

  if (latestAdminUpdate) {
    return {
      label: 'Admin update',
      at: latestAdminUpdate.createdAt,
      message: latestAdminUpdate.comment ?? 'The shop posted a service update for this booking.',
    };
  }

  const latestTimelineEntry = booking.timeline[booking.timeline.length - 1];

  return {
    label: 'Latest update',
    at: latestTimelineEntry?.at ?? booking.createdAt,
    message: latestTimelineEntry?.note ?? 'The shop will post the next service update here.',
  };
}

function normalizeStoreText(value: unknown) {
  return typeof value === 'string' ? value.trim() : '';
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row items-start justify-between gap-4 py-3">
      <HeroText className="text-[13px] text-neutral-500">
        {label}
      </HeroText>
      <HeroText className="max-w-[58%] text-right text-[13px] font-semibold leading-5 text-neutral-950">
        {value}
      </HeroText>
    </View>
  );
}

export default function PlayerBookingDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string; photoUpload?: string }>();
  const bookings = useBookings();
  const conversations = useConversations();
  const payments = usePayments();
  const strings = useStrings();
  const token = useBackendAccessToken();
  const storeSettings = useAppStore((state) => state.storeSettings);
  const upsertLiveBooking = useAppStore((state) => state.upsertLiveBooking);
  const upsertLiveConversation = useAppStore(
    (state) => state.upsertLiveConversation,
  );
  const [isRequestingSupport, setIsRequestingSupport] = useState(false);
  const [supportError, setSupportError] = useState<string | null>(null);
  const [hasFeedback, setHasFeedback] = useState<boolean | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const booking = bookings.find((item) => item.id === params.id);
  const showPhotoUploadWarning = params.photoUpload === 'failed';
  const activePayment = payments.find(
    (item) =>
      item.bookingId === booking?.id &&
      (item.status === 'pending' || item.status === 'paid'),
  );
  const supportConversation = conversations.find(
    (item) => item.bookingId === booking?.id,
  );

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
        upsertLiveBooking(mapBackendBookingToBooking(freshBooking));
      } catch (error) {
        console.warn('Failed to refresh live player booking detail', error);
      }
    };

    void hydrateBooking();

    return () => {
      cancelled = true;
    };
  }, [params.id, token, upsertLiveBooking]);

  useEffect(() => {
    if (!token || booking?.status !== 'completed') {
      setHasFeedback(null);
      return;
    }

    let cancelled = false;
    void backendApi
      .fetchBookingFeedback(token, booking.id)
      .then((feedback) => {
        if (!cancelled) {
          setHasFeedback(feedback !== null);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setHasFeedback(
            error instanceof BackendApiError && error.statusCode === 404
              ? false
              : null,
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, [booking?.id, booking?.status, token]);

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

  const canCancel = booking.status === 'awaiting_dropoff';
  const cancelBooking = () => {
    if (!token || !canCancel) {
      return;
    }
    Alert.alert(
      'Cancel booking?',
      'Cancellation is available only before the racket is checked in.',
      [
        { text: 'Keep booking', style: 'cancel' },
        {
          text: 'Cancel booking',
          style: 'destructive',
          onPress: () => {
            setIsCancelling(true);
            setCancelError(null);
            void backendApi
              .cancelBooking(
                token,
                booking.id,
                'Cancelled by player before drop-off.',
              )
              .then((response) => {
                upsertLiveBooking(mapBackendBookingToBooking(response));
              })
              .catch((error: unknown) => {
                setCancelError(
                  error instanceof BackendApiError
                    ? error.message
                    : 'Failed to cancel this booking.',
                );
              })
              .finally(() => setIsCancelling(false));
          },
        },
      ],
    );
  };

  const stringItem = strings.find((item) => item.id === booking.stringId);
  const stringLabel = stringItem
    ? `${stringItem.brand} ${stringItem.model}`
    : 'Custom string selection';
  const storeName = normalizeStoreText(storeSettings?.storeName);
  const storeAddress = normalizeStoreText(storeSettings?.address);
  const vendorLabel =
    storeName ||
    'Assigned shop';
  const shopAddress =
    storeAddress ||
    'Address not provided';
  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);
  const latestUpdate = getLatestUpdate(booking);
  const heroStatusChip = getHeroStatusChipClasses(booking.status);
  const canCheckIn =
    booking.status === 'confirmed' || booking.status === 'awaiting_dropoff';
  const canOpenFeedback = booking.status === 'completed';

  const openSupportConversation = async () => {
    if (supportConversation) {
      router.push(`/player/chat/${supportConversation.id}`);
      return;
    }
    if (!token) {
      setSupportError('Your player session expired. Sign in again to open support.');
      return;
    }

    setIsRequestingSupport(true);
    setSupportError(null);
    try {
      const response = await backendApi.requestBookingSupport(token, booking.id);
      const conversation = mapBackendConversationToConversation(response, booking);
      upsertLiveConversation(conversation);
      router.push(`/player/chat/${conversation.id}`);
    } catch (error) {
      setSupportError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to open booking support.',
      );
    } finally {
      setIsRequestingSupport(false);
    }
  };

  return (
    <AppScreen
      headerVariant="secondary"
      compactHeader
      title={`Booking ${orderCode}`}
      subtitle="Track booking info and live progress."
      showBackButton
      onBackPress={() => router.back()}
      contentContainerClassName="pt-3"
    >
      {showPhotoUploadWarning ? (
        <AppCard variant="subtle" className="mb-4 border border-amber-200" padding="md">
          <HeroText className="text-sm font-medium text-amber-700">
            Booking was created, but photo upload failed. You can add a photo again from booking updates.
          </HeroText>
        </AppCard>
      ) : null}
      <View className="gap-4">
        <AppCard variant="dark" className="rounded-[28px]" padding="md">
          <View className="gap-3">
            <View className="gap-3">
              <View className="flex-row items-start justify-between gap-3">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary-100">
                  Status overview
                </HeroText>
                <AppChip
                  label={formatBookingStatus(booking.status)}
                  variant={getBookingStatusVariant(booking.status)}
                  className={heroStatusChip.className}
                  textClassName={heroStatusChip.textClassName}
                />
              </View>
              <HeroText
                className="text-[26px] font-bold tracking-tight text-white"
                style={{ fontSize: 30, lineHeight: 36, fontWeight: '800' }}
              >
                {getHeroStatusLabel(booking.status)}
              </HeroText>
            </View>

            <View className="rounded-[20px] bg-white/10 px-4 py-3">
              <HeroText className="text-sm text-primary-100">
                Drop-off on {formatDropOffDateTime(booking)}
              </HeroText>
              <HeroText className="mt-2 text-sm font-medium leading-6 text-white">
                Next: {getNextStepLabel(booking.status)}
              </HeroText>
            </View>
          </View>
        </AppCard>

        <AppCard variant="elevated" padding="md" className="rounded-[24px]">
          <View className="gap-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
              Booking details
            </HeroText>
            <View className="mt-2">
              <DetailRow label="Vendor" value={vendorLabel} />
              <View className="h-px bg-[#EEF3F8]" />
              <View className="py-3">
                <HeroText className="text-[13px] text-neutral-500">
                  Shop address
                </HeroText>
                <HeroText className="mt-1 text-[13px] leading-5 text-neutral-900">
                  {shopAddress}
                </HeroText>
              </View>
              <View className="h-px bg-[#EEF3F8]" />
              <DetailRow label="Racket" value={`${booking.racketBrand} ${booking.racketModel}`} />
              <DetailRow
                label="Service method"
                value={
                  booking.serviceMethod === 'pickup_request'
                    ? 'Pickup requested'
                    : 'Counter drop-off'
                }
              />
              <View className="h-px bg-[#EEF3F8]" />
              <DetailRow
                label="String"
                value={stringLabel}
              />
              <View className="h-px bg-[#EEF3F8]" />
              <DetailRow label="Tension" value={`${booking.requestedTension} lbs`} />
              <View className="h-px bg-[#EEF3F8]" />
              <DetailRow label="Order ID" value={orderCode} />
              <View className="h-px bg-[#EEF3F8]" />
              <DetailRow label="Quote status" value={getQuoteStatus(booking)} />
              <View className="h-px bg-[#EEF3F8]" />
              <DetailRow
                label="Expected ready"
                value={
                  booking.expectedCompletionAt
                    ? formatDateTime(booking.expectedCompletionAt)
                    : '-'
                }
              />
            </View>
          </View>
        </AppCard>

        <AppCard variant="elevated" padding="md" className="rounded-[24px]">
          <View className="gap-3">
            <View className="flex-row items-start justify-between gap-3">
              <View className="min-w-0 flex-1">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                  Progress
                </HeroText>
                <HeroText className="mt-1 text-[15px] font-bold tracking-tight text-neutral-950">
                  Progress preview
                </HeroText>
              </View>
              <AppButton
                label="View full"
                variant="ghost"
                size="sm"
                onPress={() => router.push(`/player/bookings/${booking.id}/tracking`)}
              />
            </View>

            <View className="gap-2">
              {TRACKING_STAGES.map((stage) => {
                const state = getStageState(stage.key, booking);
                const isCurrent = state === 'current';
                const isComplete = state === 'complete';

                return (
                  <View
                    key={stage.key}
                    className={`flex-row items-center gap-3 rounded-[18px] px-3 py-2 ${
                      isCurrent ? 'bg-primary-50/80' : ''
                    }`}
                  >
                    <View className="h-6 w-6 items-center justify-center">
                      {isComplete ? (
                        <CircleCheck size={18} color="#2F64B6" />
                      ) : isCurrent ? (
                        <Circle size={16} color="#2F64B6" fill="#2F64B6" />
                      ) : (
                        <Circle size={16} color="#C9D5E4" />
                      )}
                    </View>
                    <HeroText
                      className={`text-[14px] leading-6 ${
                        isCurrent
                          ? 'font-semibold text-primary-700'
                          : isComplete
                            ? 'font-medium text-neutral-700'
                            : 'text-neutral-400'
                      }`}
                    >
                      {stage.label}
                    </HeroText>
                  </View>
                );
              })}
            </View>
          </View>
        </AppCard>

        <AppCard variant="subtle" padding="md" className="rounded-[24px]">
          <View className="flex-row items-start gap-3">
            <CalendarClock size={18} color="#2F64B6" />
            <View className="min-w-0 flex-1">
              <HeroText className="text-[14px] font-semibold tracking-tight text-neutral-950">
                Show your order ID at the counter during drop-off.
              </HeroText>
              <HeroText className="mt-1 text-[13px] leading-5 text-neutral-600">
                The vendor uses the order ID to verify the booking and proceed with drop-off confirmation.
              </HeroText>
            </View>
          </View>
        </AppCard>

        <AppCard variant="elevated" padding="md" className="rounded-[24px]">
          <View className="gap-3">
            <View className="flex-row items-start justify-between gap-3">
              <AppChip label={latestUpdate.label} variant="primary" />
              <HeroText className="text-[12px] text-neutral-500">
                {formatTrackingDateTime(latestUpdate.at)}
              </HeroText>
            </View>
            <HeroText className="text-[14px] leading-6 text-neutral-700">
              {latestUpdate.message}
            </HeroText>
          </View>
        </AppCard>

        <View className="pt-1">
          {booking.totalAmount > 0 && activePayment?.status !== 'paid' ? (
            <AppButton
              label={
                activePayment?.status === 'pending'
                  ? 'Payment awaiting verification'
                  : 'Pay booking'
              }
              variant="outline"
              size="lg"
              className="mb-3"
              isDisabled={activePayment?.status === 'pending'}
              onPress={() => router.push(`/player/payments/${booking.id}`)}
            />
          ) : null}
          {canCheckIn ? (
            <AppButton
              label="Show check-in reference"
              variant="outline"
              size="lg"
              className="mb-3"
              onPress={() =>
                router.push(`/player/check-in?bookingId=${booking.id}`)
              }
            />
          ) : null}
          <AppButton
            label="Message shop"
            variant="outline"
            size="lg"
            className="mb-3"
            isLoading={isRequestingSupport}
            onPress={() => void openSupportConversation()}
          />
          {supportError ? (
            <HeroText className="mb-3 text-sm font-medium text-red-600">
              {supportError}
            </HeroText>
          ) : null}
          {canOpenFeedback ? (
            <AppButton
              label={hasFeedback ? 'View service feedback' : 'Leave service feedback'}
              variant="outline"
              size="lg"
              className="mb-3"
              onPress={() => router.push(`/player/feedback/${booking.id}`)}
            />
          ) : null}
          {canCancel ? (
            <AppButton
              label="Cancel booking"
              variant="outline"
              size="lg"
              className="mb-3"
              isLoading={isCancelling}
              onPress={cancelBooking}
            />
          ) : null}
          {cancelError ? (
            <HeroText className="mb-3 text-sm font-medium text-red-600">
              {cancelError}
            </HeroText>
          ) : null}
          <AppButton
            label="View tracking"
            variant="primary"
            size="lg"
            onPress={() => router.push(`/player/bookings/${booking.id}/tracking`)}
          />
          <HeroText className="mt-3 text-center text-[11px] leading-5 text-neutral-400">
            Booking flow covers drop-off, progress updates, and collection tracking.
          </HeroText>
        </View>
      </View>
    </AppScreen>
  );
}
