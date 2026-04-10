import React, { useEffect, useMemo, useState } from 'react';
import { Image, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import {
  Boxes,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Circle,
  Store,
  TimerReset,
  Upload,
} from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
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
import type { Booking, BookingStatus, BookingUpdate, PlayerProfile } from '../../../types/domain';
import {
  formatBookingOrderCode,
  formatBookingStatus,
  formatCurrency,
  formatDateLabel,
  formatDateTime,
} from '../../../lib/formatters';
import { getStringById, getUserById } from '../../../services/mockAppService';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendBookingToBooking } from '../../../services/backendMappers';

const WORKFLOW_STATUSES = [
  'awaiting_dropoff',
  'in_progress',
  'ready_for_collection',
  'completed',
] as const;

function getPriceStateLabel(booking: Booking) {
  if (booking.totalAmount > 0) {
    return formatCurrency(booking.totalAmount);
  }

  switch (booking.status) {
    case 'awaiting_dropoff':
      return 'Quoted at shop';
    case 'in_progress':
      return 'Vendor quote';
    default:
      return 'Price pending';
  }
}

function getWorkflowActionLabel(status: BookingStatus) {
  switch (status) {
    case 'awaiting_dropoff':
      return 'Update to Awaiting Dropoff';
    case 'in_progress':
      return 'Update to In Progress';
    case 'ready_for_collection':
      return 'Update to Ready for Collection';
    case 'completed':
      return 'Update to Completed';
    default:
      return 'Update booking workflow';
  }
}

function getStatusHeroCopy(status: BookingStatus) {
  switch (status) {
    case 'awaiting_dropoff':
      return 'Waiting for counter check-in before stringing starts.';
    case 'in_progress':
      return 'Job is active on the service bench.';
    case 'ready_for_collection':
      return 'Stringing is complete and ready for pickup handoff.';
    case 'completed':
      return 'Order is finished and handed over to the player.';
    default:
      return 'Review this booking and keep the workflow moving.';
  }
}

function getUpdateMetaLabel(update: BookingUpdate) {
  if (update.photoUrl && update.comment) {
    return 'Photo and note added';
  }
  if (update.photoUrl) {
    return 'Photo added';
  }
  return 'Note added';
}

function SummaryRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <View className="flex-row items-start justify-between gap-4">
      <HeroText className="w-[96px] text-[11px] font-semibold uppercase tracking-[0.08em] text-neutral-400">
        {label}
      </HeroText>
      <HeroText className="flex-1 text-right text-[13px] font-semibold leading-5 text-neutral-700">
        {value}
      </HeroText>
    </View>
  );
}

function AdminUpdateFeed({ updates }: { updates: BookingUpdate[] }) {
  if (updates.length === 0) {
    return (
      <AppCard variant="subtle" padding="md">
        <View className="flex-row items-start gap-3">
          <View className="mt-0.5 h-10 w-10 items-center justify-center rounded-[16px] bg-primary-50">
            <Boxes size={18} color="#2F64B6" />
          </View>
          <View className="flex-1">
            <HeroText className="text-[15px] font-semibold tracking-tight text-neutral-900">
              No admin updates yet
            </HeroText>
            <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
              Use the composer below to log condition notes, service progress, or collection instructions.
            </HeroText>
          </View>
        </View>
      </AppCard>
    );
  }

  return (
    <View className="gap-3">
      {updates.map((item, index) => (
        <AppCard key={item.id} variant="elevated" padding="md">
          <View className="flex-row gap-3">
            <View className="items-center">
              <View className="h-8 w-8 items-center justify-center rounded-full bg-primary-50">
                <Circle size={10} fill="#2F64B6" color="#2F64B6" />
              </View>
              {index < updates.length - 1 ? (
                <View className="mt-2 h-full min-h-8 w-px bg-[#D9E6F4]" />
              ) : null}
            </View>
            <View className="flex-1 gap-2.5">
              <View className="flex-row items-start justify-between gap-3">
                <View className="flex-1">
                  <HeroText className="text-[14px] font-semibold tracking-tight text-neutral-950">
                    {item.authorRole === 'admin' ? 'Admin update' : 'Player note'}
                  </HeroText>
                  <HeroText className="mt-0.5 text-[11px] font-medium text-neutral-500">
                    {getUpdateMetaLabel(item)}
                  </HeroText>
                </View>
                <HeroText className="text-[11px] font-medium text-neutral-500">
                  {formatDateTime(item.createdAt)}
                </HeroText>
              </View>
              {item.comment ? (
                <HeroText className="text-sm leading-6 text-neutral-700">
                  {item.comment}
                </HeroText>
              ) : null}
              {item.photoUrl ? (
                <Image
                  source={{ uri: item.photoUrl }}
                  className="h-36 w-full rounded-[22px] bg-neutral-100"
                  resizeMode="cover"
                  accessibilityLabel={item.photoOriginalName ?? 'Booking update photo'}
                />
              ) : null}
            </View>
          </View>
        </AppCard>
      ))}
    </View>
  );
}

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

  const sortedUpdates = useMemo(
    () => [...(booking?.updates ?? [])].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()),
    [booking?.updates]
  );

  if (!booking) {
    return null;
  }

  const player = getUserById(booking.playerId) as PlayerProfile | undefined;
  const stringItem = getStringById(booking.stringId);
  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);
  const priceState = getPriceStateLabel(booking);
  const workflowCTA = getWorkflowActionLabel(status);
  const isWorkflowUnchanged = status === booking.status;

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
      subtitle="Update service status and admin notes."
      compactHeader
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection variant="compact">
        <AppCard variant="highlighted" padding="lg">
          <View className="gap-4">
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                  Current status
                </HeroText>
                <HeroText className="mt-1 text-[28px] font-bold tracking-tight text-neutral-950">
                  {formatBookingStatus(booking.status)}
                </HeroText>
                <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
                  {getStatusHeroCopy(booking.status)}
                </HeroText>
              </View>
              <AppChip
                label={formatBookingStatus(booking.status)}
                variant={getBookingStatusVariant(booking.status)}
                size="md"
              />
            </View>

            <View className="gap-2.5 rounded-[22px] border border-white/80 bg-white/80 px-4 py-4">
              <View className="flex-row items-center gap-2">
                <CalendarClock size={15} color="#2F64B6" />
                <HeroText className="text-[13px] font-semibold text-neutral-700">
                  Drop-off: {booking.dropOffDate} · {booking.dropOffTime}
                </HeroText>
              </View>
              <View className="flex-row items-center gap-2">
                <Store size={15} color="#2F64B6" />
                <HeroText className="text-[13px] font-semibold text-neutral-700">
                  {booking.racketBrand} {booking.racketModel}
                </HeroText>
              </View>
              <View className="flex-row items-center gap-2">
                <TimerReset size={15} color="#2F64B6" />
                <HeroText className="text-[13px] font-semibold text-neutral-700">
                  {stringItem?.brand} {stringItem?.model} · {booking.requestedTension} lbs
                </HeroText>
              </View>
              <View className="flex-row items-center gap-2">
                <Clock3 size={15} color="#2F64B6" />
                <HeroText className="text-[13px] font-semibold text-neutral-700">
                  {priceState}
                </HeroText>
              </View>
            </View>
          </View>
        </AppCard>
      </AppSection>

      <AppSection
        eyebrow="Workflow"
        title="Service actions"
        subtitle="Move the booking through the shop workflow."
        variant="compact"
      >
        <View className="gap-3">
          <View className="flex-row flex-wrap gap-2.5">
            {WORKFLOW_STATUSES.map((item) => {
              const isCurrent = booking.status === item;
              const isSelected = status === item;

              return (
                <AppCard
                  key={item}
                  variant={isCurrent || isSelected ? 'highlighted' : 'subtle'}
                  padding="sm"
                  onPress={() => setStatus(item)}
                  className="min-w-[148px] flex-1"
                >
                  <View className="gap-1.5">
                    <View className="flex-row items-center justify-between gap-2">
                      <AppChip
                        label={formatBookingStatus(item)}
                        variant={isCurrent || isSelected ? getBookingStatusVariant(item) : 'neutral'}
                        size="sm"
                      />
                      {isCurrent ? <CheckCircle2 size={15} color="#2F64B6" /> : null}
                    </View>
                    <HeroText className="text-[11px] font-medium leading-4 text-neutral-500">
                      {isCurrent ? 'Current workflow state' : isSelected ? 'Selected next state' : 'Tap to select'}
                    </HeroText>
                  </View>
                </AppCard>
              );
            })}
          </View>

          {error ? (
            <HeroText className="text-sm font-semibold text-danger-600">
              {error}
            </HeroText>
          ) : null}

          <AppButton
            label={isWorkflowUnchanged ? `Current status: ${formatBookingStatus(booking.status)}` : workflowCTA}
            size="lg"
            className="mt-1"
            onPress={saveStatus}
            isLoading={isSaving}
            isDisabled={isWorkflowUnchanged}
          />
        </View>
      </AppSection>

      <AppSection
        eyebrow="Booking summary"
        title="Counter-ready details"
        subtitle="Everything staff need at a glance."
        variant="compact"
      >
        <AppCard variant="elevated" padding="md">
          <View className="gap-3.5">
            <SummaryRow label="Order ID" value={orderCode} />
            <SummaryRow label="Player" value={player?.name ?? 'Walk-in player'} />
            <SummaryRow
              label="Contact"
              value={player?.phone ?? player?.email ?? 'No contact provided'}
            />
            <SummaryRow label="Racket" value={`${booking.racketBrand} ${booking.racketModel}`} />
            <SummaryRow
              label="String"
              value={stringItem ? `${stringItem.brand} ${stringItem.model}` : 'String to confirm'}
            />
            <SummaryRow label="Tension" value={`${booking.requestedTension} lbs`} />
            <SummaryRow
              label="Drop-off"
              value={`${formatDateLabel(booking.dropOffDate)} · ${booking.dropOffTime}`}
            />
            <SummaryRow label="Price state" value={priceState} />
            {booking.queuePosition > 0 ? (
              <SummaryRow label="Queue" value={`#${booking.queuePosition}`} />
            ) : null}
            {booking.notes ? (
              <View className="rounded-[18px] bg-[#F5F8FC] px-3.5 py-3">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.08em] text-neutral-400">
                  Service note
                </HeroText>
                <HeroText className="mt-1.5 text-sm leading-6 text-neutral-600">
                  {booking.notes}
                </HeroText>
              </View>
            ) : null}
          </View>
        </AppCard>
      </AppSection>

      <AppSection
        eyebrow="Admin updates"
        title="Service log"
        subtitle="Track progress notes and photos in one feed."
        variant="compact"
      >
        <AdminUpdateFeed updates={sortedUpdates} />
      </AppSection>

      <AppSection
        eyebrow="Add update"
        title="Log a note or photo"
        subtitle="Keep the service record current while the racket moves through the bench."
        variant="compact"
        className="mb-8"
      >
        <AppCard variant="subtle" padding="md">
          <AppInput
            label="Comment"
            value={updateComment}
            onChangeText={setUpdateComment}
            multiline
            className="mb-0"
            inputClassName="min-h-24"
            placeholder="Add service notes, frame condition, or collection instructions..."
          />
          {updatePhoto ? (
            <Image
              source={{ uri: updatePhoto.uri }}
              className="mt-3 h-36 w-full rounded-[22px] bg-neutral-100"
              resizeMode="cover"
            />
          ) : null}
          {updateError ? (
            <HeroText className="mt-3 text-sm font-semibold text-danger-600">
              {updateError}
            </HeroText>
          ) : null}
          <View className="mt-3 flex-row gap-3">
            <AppButton
              label={updatePhoto ? 'Change photo' : 'Attach photo'}
              variant="outline"
              className="flex-1"
              leadingIcon={<Upload size={16} color="#475569" />}
              onPress={pickUpdatePhoto}
            />
            {updatePhoto ? (
              <AppButton
                label="Remove"
                variant="ghost"
                className="px-4"
                onPress={() => setUpdatePhoto(null)}
              />
            ) : null}
          </View>
          <AppButton
            label="Save update"
            className="mt-3"
            onPress={submitBookingUpdate}
            isLoading={isSubmittingUpdate}
          />
        </AppCard>
      </AppSection>
    </AppScreen>
  );
}
