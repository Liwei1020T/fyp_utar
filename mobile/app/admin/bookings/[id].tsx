import React, { useEffect, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { getBookingStatusVariant } from '../../../components/ui/theme';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
  useStrings,
} from '../../../store/appStore';
import type { BookingStatus } from '../../../types/domain';
import { formatBookingStatus, formatCurrency, formatPaymentStatus } from '../../../lib/formatters';
import { getStringById, getUserById } from '../../../services/mockAppService';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendBookingToBooking } from '../../../services/backendMappers';

export default function AdminBookingDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const token = useBackendAccessToken();
  const user = useCurrentUser();
  const bookings = useBookings();
  const strings = useStrings();
  const updateBookingStatus = useAppStore((state) => state.updateBookingStatus);
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);
  const booking = bookings.find((item) => item.id === params.id);
  const [status, setStatus] = useState<BookingStatus>(booking?.status ?? 'confirmed');
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (booking) {
      setStatus(booking.status);
    }
  }, [booking]);

  if (!booking) {
    return null;
  }

  const player = getUserById(booking.playerId);
  const stringItem = getStringById(booking.stringId);
  const saveStatus = async () => {
    setError(null);

    if (status === booking.status) {
      return;
    }

    if (!token || user?.role !== 'admin') {
      updateBookingStatus(booking.id, status);
      return;
    }

    setIsSaving(true);
    try {
      const updated = await backendApi.adminUpdateBookingStatus(token, booking.id, {
        status,
      });
      const priceByStringId = new Map(strings.map((item) => [item.id, item.price]));
      const mapped = mapBackendBookingToBooking(updated, priceByStringId, user.id);
      setLiveBookings(
        bookings.map((item) => (item.id === mapped.id ? mapped : item)),
      );
    } catch (saveError) {
      setError(
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to update booking status.',
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <AppScreen
      tone="admin"
      title={`Booking ${booking.id}`}
      subtitle="Admin detail view for service status, payment, customer summary, and quick actions."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      <AppSection eyebrow="Customer" title="Player summary">
        <AppCard variant="highlighted" padding="lg">
          <HeroText className="text-xl font-bold tracking-tight text-neutral-950">{player?.name}</HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            {booking.racketBrand} {booking.racketModel} • {stringItem?.brand} {stringItem?.model} • {booking.requestedTension} lbs
          </HeroText>
          <View className="mt-4 flex-row flex-wrap gap-2">
            <AppChip label={formatPaymentStatus(booking.paymentStatus)} variant="primary" />
            <AppChip label={formatCurrency(booking.totalAmount)} variant="secondary" />
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Workflow" title="Update service status">
        <View className="flex-row flex-wrap gap-2">
          {(['awaiting_dropoff', 'in_progress', 'ready_for_collection', 'completed'] as const).map((item) => (
            <AppChip
              key={item}
              label={formatBookingStatus(item)}
              size="md"
              variant={status === item ? getBookingStatusVariant(item) : 'neutral'}
              onPress={() => setStatus(item)}
            />
          ))}
        </View>
        {error ? (
          <HeroText className="mt-3 text-sm font-semibold text-danger-600">
            {error}
          </HeroText>
        ) : null}
        <AppButton
          label="Save status"
          className="mt-4"
          onPress={saveStatus}
          isLoading={isSaving}
        />
      </AppSection>

      <AppSection eyebrow="Operations" title="Booking details">
        <AppCard variant="elevated" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Drop-off window: {booking.dropOffDate} at {booking.dropOffTime}
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-600">
            Check-in reference: {booking.checkInReference}
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-600">
            Queue position: #{booking.queuePosition}
          </HeroText>
        </AppCard>
      </AppSection>
    </AppScreen>
  );
}
