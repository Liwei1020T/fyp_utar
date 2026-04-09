import React, { useEffect } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { CalendarClock, ChevronLeft, TimerReset } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
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
      subtitle="Booking info, drop-off details, admin updates, and service status in one player view."
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
          </View>
        </View>
      </AppCard>

      <AppSection eyebrow="Overview" title="Quick facts">
        <View className="flex-row gap-3">
          <AppCard variant="elevated" className="flex-1" padding="md">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
              Booking
            </HeroText>
            <AppChip
              label={formatBookingStatus(booking.status)}
              variant={getBookingStatusVariant(booking.status)}
              className="mt-3 self-start"
            />
          </AppCard>
        </View>
      </AppSection>

      <AppSection eyebrow="Booking info" title="String and racket setup">
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
            {
              label: 'Admin desk',
              value: admin?.businessName ?? 'Assigned shop',
            },
          ]}
        />
      </AppSection>

      <AppSection eyebrow="Drop-off" title="Arrival and check-in">
        <View className="gap-3">
          <AppCard variant="subtle" padding="md">
            <View className="flex-row items-center gap-3">
              <CalendarClock size={18} color="#2F64B6" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                Booking reference: {booking.checkInReference}. Show this reference at the counter during drop-off.
              </HeroText>
            </View>
          </AppCard>
          <AppCard variant="subtle" padding="md">
            <View className="flex-row items-center gap-3">
              <TimerReset size={18} color="#22766D" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                {booking.queuePosition > 0
                  ? `Queue position is currently #${booking.queuePosition}. Service updates appear on the tracking timeline as the admin desk updates your order.`
                  : 'Service updates appear on the tracking timeline as the admin desk updates your order.'}
              </HeroText>
            </View>
          </AppCard>
        </View>
      </AppSection>

      <AppSection eyebrow="Pricing" title="Estimated service cost">
        <AppDetailList
          items={[
            { label: 'String fee', value: formatCurrency(booking.stringFee) },
            { label: 'Service fee', value: formatCurrency(booking.serviceFee) },
            { label: 'Estimated total', value: formatCurrency(booking.totalAmount) },
          ]}
        />
      </AppSection>

      <AppSection eyebrow="Rule" title="Booking policy">
        <AppCard variant="highlighted" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-700">
            {booking.paymentRuleNote}
          </HeroText>
        </AppCard>
      </AppSection>

      {booking.notes ? (
        <AppSection eyebrow="Notes" title="Service instructions">
          <AppCard variant="highlighted" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-700">{booking.notes}</HeroText>
          </AppCard>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Booking updates" title="Photos and comments">
        <BookingUpdates updates={booking.updates} />
      </AppSection>

      <View className="mb-12 mt-8 gap-3">
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
