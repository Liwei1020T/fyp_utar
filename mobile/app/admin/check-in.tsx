import React, { useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  CalendarClock,
  Check,
  CircleCheck,
  Search,
} from 'lucide-react-native';
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
import { formatBookingOrderCode, formatBookingStatus } from '../../lib/formatters';
import { getBookingStatusVariant } from '../../components/ui/theme';
import type { Booking } from '../../types/domain';

type ChecklistKey = 'playerPresent' | 'racketReceived' | 'setupConfirmed';

const CHECKLIST_ITEMS: {
  key: ChecklistKey;
  label: string;
  helper: string;
}[] = [
  {
    key: 'playerPresent',
    label: 'Player present',
    helper: 'Confirm the player is at the counter.',
  },
  {
    key: 'racketReceived',
    label: 'Racket received',
    helper: 'Confirm the racket has been handed over.',
  },
  {
    key: 'setupConfirmed',
    label: 'Setup confirmed',
    helper: 'Confirm string and tension before service starts.',
  },
];

function formatDropOffDateTime(booking: Booking) {
  const date = new Date(`${booking.dropOffDate}T${booking.dropOffTime}:00`);

  if (Number.isNaN(date.getTime())) {
    return `${booking.dropOffDate} · ${booking.dropOffTime}`;
  }

  return date.toLocaleString('en-MY', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: false,
  });
}

function getTodayLocalDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getDropOffConfirmationStatus(booking: Booking) {
  if (booking.status === 'awaiting_dropoff' || booking.status === 'confirmed') {
    return 'Awaiting drop-off';
  }

  if (booking.status === 'in_progress') {
    return 'Already received';
  }

  return formatBookingStatus(booking.status);
}

export default function AdminCheckInScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const strings = useStrings();
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);

  const todaysAwaitingDropOffBookings = useMemo(() => {
    if (!user || user.role !== 'admin') {
      return [];
    }

    const today = getTodayLocalDate();

    return bookings
      .filter(
        (item) =>
          item.adminId === user.id &&
          item.status === 'awaiting_dropoff' &&
          item.dropOffDate === today,
      )
      .sort((left, right) =>
        `${left.dropOffDate} ${left.dropOffTime}`.localeCompare(
          `${right.dropOffDate} ${right.dropOffTime}`,
        ),
      );
  }, [bookings, user]);

  const defaultBooking = todaysAwaitingDropOffBookings[0] ?? null;
  const defaultOrderId = defaultBooking
    ? defaultBooking.orderCode ?? formatBookingOrderCode(defaultBooking.id)
    : '';

  const [orderId, setOrderId] = useState(defaultOrderId);
  const [match, setMatch] = useState<Booking | null>(defaultBooking);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [checklist, setChecklist] = useState<Record<ChecklistKey, boolean>>({
    playerPresent: false,
    racketReceived: false,
    setupConfirmed: false,
  });

  if (!user || user.role !== 'admin') {
    return null;
  }

  const resetChecklist = () => {
    setChecklist({
      playerPresent: false,
      racketReceived: false,
      setupConfirmed: false,
    });
    setNotes('');
  };

  const setSelectedBooking = (booking: Booking | null) => {
    setMatch(booking);
    setConfirmError(null);
    resetChecklist();

    if (booking) {
      setOrderId(booking.orderCode ?? formatBookingOrderCode(booking.id));
    }
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
      setMatch(null);
      setLookupError('Your admin session expired. Sign in again to look up bookings.');
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
      setSelectedBooking(mapped);
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

  const allChecklistChecked = Object.values(checklist).every(Boolean);

  const confirmDropOff = async () => {
    if (!match) {
      setConfirmError('Find a booking before confirming drop-off.');
      return;
    }

    if (!allChecklistChecked) {
      setConfirmError('Complete the counter checklist before confirming drop-off.');
      return;
    }

    setConfirmError(null);

    if (match.status === 'in_progress') {
      router.push(`/admin/bookings/${match.id}`);
      return;
    }

    if (!token) {
      setConfirmError('Your admin session expired. Sign in again to confirm drop-off.');
      return;
    }

    setIsConfirming(true);
    try {
      const updated = await backendApi.adminCheckIn(token, {
        booking_id: match.id,
        note: notes.trim() || null,
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
  const matchedString = match
    ? strings.find((item) => item.id === match.stringId)
    : null;
  const matchedPlayerName =
    match?.customerName
    ?? 'Player booking';
  const matchedPlayerContact =
    match?.customerPhone
    ?? '-';

  return (
    <AppScreen
      tone="admin"
      headerVariant="flow"
      compactHeader
      title="Check-in"
      subtitle="Confirm player drop-off by order ID"
      showBackButton
      onBackPress={() => router.back()}
      contentContainerClassName="pt-3"
    >
      <View className="gap-4">
        <AppCard variant="elevated" padding="md" className="rounded-[26px]">
          <View className="gap-3">
            <View className="flex-row items-start justify-between gap-3">
              <View className="min-w-0 flex-1">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                  Search
                </HeroText>
                <HeroText className="mt-1 text-[16px] font-bold tracking-tight text-neutral-950">
                  Find booking by order ID
                </HeroText>
              </View>
              <AppChip label="Order ID only" variant="primary" />
            </View>

            <AppInput
              label="Order ID"
              value={orderId}
              onChangeText={setOrderId}
              placeholder="Search order ID"
              autoCapitalize="characters"
              leftAdornment={<Search size={16} color="#64748B" />}
            />

            <View className="gap-3" style={{ gap: 12 }}>
              <AppButton
                label="Find booking"
                trailingIcon={<Search size={16} color="#FFFFFF" />}
                onPress={() => void runLookup()}
                isLoading={isLookingUp}
              />
            </View>

            <View className="flex-row flex-wrap gap-2">
              <AppChip
                label={
                  todaysAwaitingDropOffBookings.length > 0
                    ? `Awaiting today (${todaysAwaitingDropOffBookings.length})`
                    : 'Awaiting today'
                }
                variant={todaysAwaitingDropOffBookings.length > 0 ? 'warning' : 'neutral'}
                size="md"
                onPress={() => {
                  const nextBooking = todaysAwaitingDropOffBookings[0] ?? null;
                  if (!nextBooking) {
                    setLookupError('No awaiting drop-offs are scheduled for today.');
                    return;
                  }

                  setLookupError(null);
                  setSelectedBooking(nextBooking);
                }}
              />
              {defaultBooking ? (
                <AppChip
                  label={`Next: ${defaultBooking.orderCode ?? formatBookingOrderCode(defaultBooking.id)}`}
                  variant="secondary"
                  size="md"
                  onPress={() => {
                    setLookupError(null);
                    setSelectedBooking(defaultBooking);
                  }}
                />
              ) : null}
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
            <AppCard variant="highlighted" padding="md" className="rounded-[26px]">
              <View className="gap-4">
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
                    variant={
                      match.status === 'in_progress'
                        ? 'success'
                        : getBookingStatusVariant(match.status)
                    }
                  />
                </View>

                <View className="gap-3 rounded-[20px] bg-white/80 px-4 py-4">
                  <View className="flex-row items-start justify-between gap-4">
                    <HeroText className="text-sm font-medium text-neutral-500">Player</HeroText>
                    <HeroText className="flex-1 text-right text-sm font-semibold text-neutral-950">
                      {matchedPlayerName}
                    </HeroText>
                  </View>
                  <View className="flex-row items-start justify-between gap-4">
                    <HeroText className="text-sm font-medium text-neutral-500">Contact</HeroText>
                    <HeroText className="flex-1 text-right text-sm font-semibold text-neutral-950">
                      {matchedPlayerContact}
                    </HeroText>
                  </View>
                  <View className="flex-row items-start justify-between gap-4">
                    <HeroText className="text-sm font-medium text-neutral-500">Racket</HeroText>
                    <HeroText className="flex-1 text-right text-sm font-semibold text-neutral-950">
                      {match.racketBrand} {match.racketModel}
                    </HeroText>
                  </View>
                  <View className="flex-row items-start justify-between gap-4">
                    <HeroText className="text-sm font-medium text-neutral-500">String</HeroText>
                    <HeroText className="flex-1 text-right text-sm font-semibold text-neutral-950">
                      {matchedString?.brand ?? 'Custom'} {matchedString?.model ?? 'String selection'}
                    </HeroText>
                  </View>
                  <View className="flex-row items-start justify-between gap-4">
                    <HeroText className="text-sm font-medium text-neutral-500">Tension</HeroText>
                    <HeroText className="flex-1 text-right text-sm font-semibold text-neutral-950">
                      {match.requestedTension} lbs
                    </HeroText>
                  </View>
                  <View className="flex-row items-start justify-between gap-4">
                    <HeroText className="text-sm font-medium text-neutral-500">Slot</HeroText>
                    <HeroText className="flex-1 text-right text-sm font-semibold text-neutral-950">
                      {formatDropOffDateTime(match)}
                    </HeroText>
                  </View>
                  <View className="flex-row items-start justify-between gap-4">
                    <HeroText className="text-sm font-medium text-neutral-500">Status</HeroText>
                    <HeroText className="flex-1 text-right text-sm font-semibold text-neutral-950">
                      {formatBookingStatus(match.status)}
                    </HeroText>
                  </View>
                </View>
              </View>
            </AppCard>

            <AppCard variant="elevated" padding="md" className="rounded-[26px]">
              <View className="gap-3">
                <View className="flex-row items-center gap-2">
                  <CalendarClock size={16} color="#2F64B6" />
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                    Counter checklist
                  </HeroText>
                </View>

                <View className="gap-3">
                  {CHECKLIST_ITEMS.map((item) => {
                    const isChecked = checklist[item.key];

                    return (
                      <Pressable
                        key={item.key}
                        onPress={() =>
                          setChecklist((current) => ({
                            ...current,
                            [item.key]: !current[item.key],
                          }))
                        }
                      >
                        <AppCard variant="subtle" padding="md">
                          <View className="flex-row items-center gap-3">
                            <View
                              className={
                                isChecked
                                  ? 'h-7 w-7 items-center justify-center rounded-full bg-success-600'
                                  : 'h-7 w-7 items-center justify-center rounded-full border border-neutral-300 bg-white'
                              }
                            >
                              {isChecked ? <Check size={15} color="#FFFFFF" /> : null}
                            </View>
                            <View className="flex-1">
                              <HeroText className="text-[15px] font-semibold text-neutral-950">
                                {item.label}
                              </HeroText>
                              <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
                                {item.helper}
                              </HeroText>
                            </View>
                          </View>
                        </AppCard>
                      </Pressable>
                    );
                  })}
                </View>

                <AppInput
                  label="Notes (optional)"
                  value={notes}
                  onChangeText={setNotes}
                  multiline
                  inputClassName="min-h-24"
                  placeholder="Frame condition, urgent remarks, or handover notes..."
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
        ) : (
          <AppCard variant="subtle" padding="md" className="rounded-[26px]">
            <View className="gap-2">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                No booking selected
              </HeroText>
              <HeroText className="text-sm leading-6 text-neutral-600">
                Search an order ID or use the awaiting-today shortcut to start check-in.
              </HeroText>
            </View>
          </AppCard>
        )}
      </View>
    </AppScreen>
  );
}
