import React, { useMemo, useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, CalendarClock, CircleCheck, ScanLine } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
  useStrings,
} from '../../store/appStore';
import { backendApi, BackendApiError } from '../../services/backendApi';
import { mapBackendBookingToBooking } from '../../services/backendMappers';
import { getStringById, getUserById } from '../../services/mockAppService';
import { formatBookingOrderCode, formatBookingStatus } from '../../lib/formatters';
import { getBookingStatusVariant } from '../../components/ui/theme';
import type { Booking } from '../../types/domain';

function formatDropOffDateTime(booking: Booking) {
  const date = new Date(`${booking.dropOffDate}T${booking.dropOffTime}:00`);

  if (Number.isNaN(date.getTime())) {
    return `${booking.dropOffDate} at ${booking.dropOffTime}`;
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

function getDropOffConfirmationStatus(booking: Booking) {
  if (booking.status === 'awaiting_dropoff' || booking.status === 'confirmed') {
    return 'Ready to confirm';
  }

  if (booking.status === 'in_progress') {
    return 'Already dropped off';
  }

  return formatBookingStatus(booking.status);
}

export default function AdminCheckInScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const strings = useStrings();
  const updateBookingStatus = useAppStore((state) => state.updateBookingStatus);
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);

  const awaitingDropOffBooking = useMemo(
    () => bookings.find((item) => item.adminId === user?.id && item.status === 'awaiting_dropoff'),
    [bookings, user?.id],
  );

  const defaultOrderId = awaitingDropOffBooking
    ? awaitingDropOffBooking.orderCode ?? formatBookingOrderCode(awaitingDropOffBooking.id)
    : '';

  const [orderId, setOrderId] = useState(defaultOrderId);
  const [match, setMatch] = useState<Booking | null>(awaitingDropOffBooking ?? null);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [confirmationNote, setConfirmationNote] = useState('');
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  if (!user || user.role !== 'admin') {
    return null;
  }

  const resolveLocalMatch = (value: string) => {
    const normalized = value.trim().toUpperCase();

    return bookings.find((item) => {
      const itemOrderId = (item.orderCode ?? formatBookingOrderCode(item.id)).toUpperCase();
      return item.adminId === user.id && (itemOrderId.includes(normalized) || item.id.toUpperCase().includes(normalized));
    }) ?? null;
  };

  const runLookup = async (input = orderId) => {
    const normalized = input.trim();
    setLookupError(null);
    setConfirmError(null);

    if (!normalized) {
      setMatch(null);
      setLookupError('Enter an order ID to find the booking.');
      return;
    }

    if (!token) {
      const localMatch = resolveLocalMatch(normalized);
      setMatch(localMatch);
      if (!localMatch) {
        setLookupError('No booking matched that order ID.');
      }
      return;
    }

    setIsLookingUp(true);
    try {
      const response = await backendApi.adminLookupCheckIn(token, normalized);
      const priceByStringId = new Map(strings.map((item) => [item.id, item.price]));
      const mapped = mapBackendBookingToBooking(response.booking, priceByStringId, user.id);
      const currentBookings = useAppStore.getState().liveBookings;
      setLiveBookings(
        currentBookings.some((item) => item.id === mapped.id)
          ? currentBookings.map((item) => (item.id === mapped.id ? mapped : item))
          : [mapped, ...currentBookings],
      );
      setMatch(mapped);
    } catch (error) {
      setMatch(null);
      setLookupError(
        error instanceof BackendApiError
          ? error.message
          : 'No booking matched that order ID.',
      );
    } finally {
      setIsLookingUp(false);
    }
  };

  const confirmDropOff = async () => {
    if (!match) {
      setConfirmError('Look up a booking before confirming drop-off.');
      return;
    }

    setConfirmError(null);

    if (match.status === 'in_progress') {
      router.push(`/admin/bookings/${match.id}`);
      return;
    }

    if (!token) {
      updateBookingStatus(match.id, 'in_progress');
      router.push(`/admin/bookings/${match.id}`);
      return;
    }

    setIsConfirming(true);
    try {
      const updated = await backendApi.adminCheckIn(token, {
        booking_id: match.id,
        reference: match.orderCode ?? formatBookingOrderCode(match.id),
        note: confirmationNote.trim() || null,
      });
      const priceByStringId = new Map(strings.map((item) => [item.id, item.price]));
      const mapped = mapBackendBookingToBooking(updated, priceByStringId, user.id);
      const currentBookings = useAppStore.getState().liveBookings;
      setLiveBookings(
        currentBookings.some((item) => item.id === mapped.id)
          ? currentBookings.map((item) => (item.id === mapped.id ? mapped : item))
          : [mapped, ...currentBookings],
      );
      router.push(`/admin/bookings/${mapped.id}`);
    } catch (error) {
      setConfirmError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to confirm drop-off.',
      );
    } finally {
      setIsConfirming(false);
    }
  };

  const matchedOrderId = match ? match.orderCode ?? formatBookingOrderCode(match.id) : null;
  const matchedPlayer = match ? getUserById(match.playerId) : null;
  const matchedString = match ? getStringById(match.stringId) : null;

  return (
    <AppScreen
      tone="admin"
      headerVariant="flow"
      compactHeader
      title="Confirm drop-off"
      subtitle="Use the order ID to verify the booking and continue the service."
      showBackButton
      onBackPress={() => router.back()}
      contentContainerClassName="pt-3"
    >
      <View className="gap-4">
        <AppCard variant="dark" padding="md" className="rounded-[28px]">
          <View className="gap-3">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-100">
              Vendor drop-off
            </HeroText>
            <HeroText className="text-[24px] font-bold tracking-tight text-white">
              Confirm racket handover from the player.
            </HeroText>
            <View className="rounded-[20px] bg-white/10 px-4 py-3">
              <HeroText className="text-sm leading-6 text-primary-100">
                The counter only needs the order ID to verify the booking and move it into service.
              </HeroText>
            </View>
          </View>
        </AppCard>

        <AppCard variant="elevated" padding="md" className="rounded-[24px]">
          <View className="gap-3">
            <View className="flex-row items-start justify-between gap-3">
              <View className="min-w-0 flex-1">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                  Lookup
                </HeroText>
                <HeroText className="mt-1 text-[16px] font-bold tracking-tight text-neutral-950">
                  Find booking by Order ID
                </HeroText>
              </View>
              <AppChip label="Order ID only" variant="primary" />
            </View>

            <AppInput
              label="Order ID"
              value={orderId}
              onChangeText={setOrderId}
              placeholder="Enter ORD-xxxxx"
              autoCapitalize="characters"
            />

            <View className="flex-row gap-3">
              <AppButton
                label="Use next drop-off"
                variant="outline"
                className="flex-1"
                leadingIcon={<ScanLine size={16} color="#5E6B7D" />}
                onPress={() => {
                  if (!awaitingDropOffBooking) {
                    return;
                  }
                  const nextOrderId = awaitingDropOffBooking.orderCode ?? formatBookingOrderCode(awaitingDropOffBooking.id);
                  setOrderId(nextOrderId);
                  void runLookup(nextOrderId);
                }}
              />
              <AppButton
                label="Lookup"
                className="flex-1"
                trailingIcon={<ArrowRight size={16} color="#FFFFFF" />}
                onPress={() => void runLookup()}
                isLoading={isLookingUp}
              />
            </View>

            {lookupError ? (
              <HeroText className="text-sm font-semibold text-danger-600">
                {lookupError}
              </HeroText>
            ) : null}
          </View>
        </AppCard>

        {match ? (
          <>
            <AppCard variant="highlighted" padding="md" className="rounded-[24px]">
              <View className="gap-3">
                <View className="flex-row items-start justify-between gap-3">
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                      Matched booking
                    </HeroText>
                    <HeroText className="mt-1 text-[18px] font-bold tracking-tight text-neutral-950">
                      {matchedOrderId}
                    </HeroText>
                  </View>
                  <AppChip
                    label={getDropOffConfirmationStatus(match)}
                    variant={match.status === 'in_progress' ? 'success' : getBookingStatusVariant(match.status)}
                  />
                </View>

                <View className="gap-2">
                  <HeroText className="text-[14px] font-semibold text-neutral-950">
                    {matchedPlayer?.name ?? 'Player booking'}
                  </HeroText>
                  <HeroText className="text-[13px] leading-5 text-neutral-600">
                    {match.racketBrand} {match.racketModel}
                  </HeroText>
                  <HeroText className="text-[13px] leading-5 text-neutral-600">
                    {matchedString?.brand ?? 'Custom'} {matchedString?.model ?? 'String selection'} • {match.requestedTension} lbs
                  </HeroText>
                </View>

                <View className="rounded-[18px] bg-white/70 px-4 py-3">
                  <View className="flex-row items-center gap-2">
                    <CalendarClock size={16} color="#2F64B6" />
                    <HeroText className="text-[13px] font-medium text-neutral-700">
                      Scheduled drop-off: {formatDropOffDateTime(match)}
                    </HeroText>
                  </View>
                </View>
              </View>
            </AppCard>

            <AppCard variant="elevated" padding="md" className="rounded-[24px]">
              <View className="gap-3">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                  Confirmation note
                </HeroText>
                <AppInput
                  label="Optional admin note"
                  value={confirmationNote}
                  onChangeText={setConfirmationNote}
                  multiline
                  inputClassName="min-h-24"
                  placeholder="Frame condition, handed-over accessories, or check-in observations..."
                />
                {confirmError ? (
                  <HeroText className="text-sm font-semibold text-danger-600">
                    {confirmError}
                  </HeroText>
                ) : null}
                <AppButton
                  label={match.status === 'in_progress' ? 'Open booking' : 'Confirm drop-off'}
                  size="lg"
                  leadingIcon={<CircleCheck size={18} color="#FFFFFF" />}
                  onPress={() => void confirmDropOff()}
                  isLoading={isConfirming}
                />
              </View>
            </AppCard>
          </>
        ) : null}
      </View>
    </AppScreen>
  );
}
