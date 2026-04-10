import React, { useEffect, useState } from 'react';
import { Image, Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { BookingUpdates } from '../../../components/booking/BookingUpdates';
import { getBookingStatusVariant } from '../../../components/ui/theme';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
  useStrings,
} from '../../../store/appStore';
import type { BookingStatus } from '../../../types/domain';
import {
  formatBookingOrderCode,
  formatBookingStatus,
  formatCurrency,
} from '../../../lib/formatters';
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
  const [updateComment, setUpdateComment] = useState('');
  const [updatePhoto, setUpdatePhoto] = useState<{
    uri: string;
    name: string;
    type: string;
  } | null>(null);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [isSubmittingUpdate, setIsSubmittingUpdate] = useState(false);

  useEffect(() => {
    if (booking) {
      setStatus(booking.status);
    }
  }, [booking]);

  useEffect(() => {
    if (!token || user?.role !== 'admin' || !params.id) {
      return;
    }

    const bookingId = params.id;
    let cancelled = false;

    const hydrateBooking = async () => {
      try {
        const freshBooking = await backendApi.adminFetchBooking(token, bookingId);
        if (cancelled) {
          return;
        }
        const priceByStringId = new Map(strings.map((item) => [item.id, item.price]));
        const mapped = mapBackendBookingToBooking(freshBooking, priceByStringId, user.id);
        const currentBookings = useAppStore.getState().liveBookings;
        setLiveBookings(
          currentBookings.some((item) => item.id === mapped.id)
            ? currentBookings.map((item) => (item.id === mapped.id ? mapped : item))
            : [mapped, ...currentBookings],
        );
      } catch (loadError) {
        console.warn('Failed to refresh live admin booking detail', loadError);
      }
    };

    void hydrateBooking();

    return () => {
      cancelled = true;
    };
  }, [params.id, setLiveBookings, strings, token, user?.id, user?.role]);

  if (!booking) {
    return null;
  }

  const player = getUserById(booking.playerId);
  const stringItem = getStringById(booking.stringId);
  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);
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
  const pickUpdatePhoto = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.85,
      allowsEditing: false,
    });

    if (result.canceled || !result.assets[0]) {
      return;
    }

    const asset = result.assets[0];
    setUpdatePhoto({
      uri: asset.uri,
      name: asset.fileName ?? `admin-booking-photo-${Date.now()}.jpg`,
      type: asset.mimeType ?? 'image/jpeg',
    });
  };
  const submitBookingUpdate = async () => {
    setUpdateError(null);
    if (!token || user?.role !== 'admin') {
      setUpdateError('Live admin login is required to add booking updates.');
      return;
    }
    if (!updateComment.trim() && !updatePhoto) {
      setUpdateError('Add a comment or photo before saving.');
      return;
    }

    setIsSubmittingUpdate(true);
    try {
      const updated = await backendApi.adminAddBookingUpdate(token, booking.id, {
        comment: updateComment,
        photo: updatePhoto,
      });
      const priceByStringId = new Map(strings.map((item) => [item.id, item.price]));
      const mapped = mapBackendBookingToBooking(updated, priceByStringId, user.id);
      setLiveBookings(
        bookings.map((item) => (item.id === mapped.id ? mapped : item)),
      );
      setUpdateComment('');
      setUpdatePhoto(null);
    } catch (saveError) {
      setUpdateError(
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to add booking update.',
      );
    } finally {
      setIsSubmittingUpdate(false);
    }
  };

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title={`Booking ${orderCode}`}
      subtitle="Admin detail view for service status, customer summary, booking comments, and photos."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection eyebrow="Customer" title="Player summary">
        <AppCard variant="highlighted" padding="lg">
          <HeroText className="text-xl font-bold tracking-tight text-neutral-950">{player?.name}</HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            {booking.racketBrand} {booking.racketModel} • {stringItem?.brand} {stringItem?.model} • {booking.requestedTension} lbs
          </HeroText>
          <View className="mt-4 flex-row flex-wrap gap-2">
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
          {booking.queuePosition > 0 ? (
            <HeroText className="mt-2 text-sm leading-6 text-neutral-600">
              Queue position: #{booking.queuePosition}
            </HeroText>
          ) : null}
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Updates" title="Comments and photos">
        <BookingUpdates updates={booking.updates} />
      </AppSection>

      <AppSection eyebrow="Admin update" title="Add comment or photo">
        <AppInput
          label="Comment"
          value={updateComment}
          onChangeText={setUpdateComment}
          multiline
          inputClassName="min-h-24"
          placeholder="Add service notes, condition notes, or collection instructions..."
        />
        {updatePhoto ? (
          <Image
            source={{ uri: updatePhoto.uri }}
            className="mt-4 h-48 w-full rounded-[24px] bg-neutral-100"
            resizeMode="cover"
          />
        ) : null}
        {updateError ? (
          <HeroText className="mt-3 text-sm font-semibold text-danger-600">
            {updateError}
          </HeroText>
        ) : null}
        <View className="mt-4 flex-row gap-3">
          <AppButton
            label={updatePhoto ? 'Change photo' : 'Attach photo'}
            variant="outline"
            className="flex-1"
            onPress={pickUpdatePhoto}
          />
          {updatePhoto ? (
            <AppButton
              label="Remove photo"
              variant="ghost"
              className="flex-1"
              onPress={() => setUpdatePhoto(null)}
            />
          ) : null}
        </View>
        <AppButton
          label="Save booking update"
          className="mt-4"
          onPress={submitBookingUpdate}
          isLoading={isSubmittingUpdate}
        />
      </AppSection>
    </AppScreen>
  );
}
