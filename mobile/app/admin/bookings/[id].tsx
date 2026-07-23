import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Image, Platform, Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import {
  Boxes,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Circle,
  ChevronDown,
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
import { PhotoPreviewModal } from '../../../components/shared/PhotoPreviewModal';
import { getBookingStatusVariant } from '../../../components/ui/theme';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
  useStrings,
} from '../../../store/appStore';
import type { Booking, BookingStatus, BookingUpdate } from '../../../types/domain';
import {
  formatBookingOrderCode,
  formatBookingStatus,
  formatCurrency,
  formatDateLabel,
  formatDateTime,
  formatLocalDateInputValue,
  formatLocalTimeValue,
} from '../../../lib/formatters';
import {
  BackendApiError,
  backendApi,
  type BackendBookingPhotoType,
} from '../../../services/backendApi';
import { mapBackendBookingToBooking } from '../../../services/backendMappers';

const WORKFLOW_STATUSES = [
  'awaiting_dropoff',
  'in_progress',
  'ready_for_collection',
  'completed',
] as const;

const WORKFLOW_TRANSITIONS: Partial<Record<BookingStatus, BookingStatus[]>> = {
  pending: ['awaiting_dropoff'],
  pending_payment: ['awaiting_dropoff'],
  confirmed: ['awaiting_dropoff'],
  awaiting_dropoff: ['in_progress'],
  in_progress: ['ready_for_collection'],
  ready_for_collection: ['completed'],
  completed: [],
  cancelled: [],
  rejected: [],
};

const PHOTO_TYPE_OPTIONS: {
  value: BackendBookingPhotoType;
  label: string;
}[] = [
  { value: 'racket', label: 'Racket' },
  { value: 'service_progress', label: 'Progress' },
  { value: 'other', label: 'Other' },
];

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

function getAllowedNextStatuses(status: BookingStatus) {
  return WORKFLOW_TRANSITIONS[status] ?? [];
}

function getWorkflowOptionHint({
  isBookingCompleted,
  isCurrent,
  isSelectable,
  isSelected,
}: {
  isBookingCompleted: boolean;
  isCurrent: boolean;
  isSelectable: boolean;
  isSelected: boolean;
}) {
  if (isBookingCompleted) {
    return 'Workflow locked';
  }
  if (isCurrent) {
    return 'Current workflow state';
  }
  if (isSelected) {
    return 'Selected next state';
  }
  if (isSelectable) {
    return 'Tap to select';
  }
  return 'Complete the previous step first';
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
    case 'cancelled':
      return 'Booking was cancelled before the service journey finished.';
    case 'rejected':
      return 'The shop declined this booking; review the recorded reason.';
    default:
      return 'Review this booking and keep the workflow moving.';
  }
}

function getUpdateMetaLabel(update: BookingUpdate) {
  if (update.photoType === 'racket') {
    return update.comment ? 'Racket photo and note added' : 'Racket photo added';
  }
  if (update.photoType === 'service_progress') {
    return update.comment ? 'Progress photo and note added' : 'Progress photo added';
  }
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

function SelectionField({
  label,
  value,
  placeholder,
  isOpen,
  onPress,
}: {
  label: string;
  value?: string;
  placeholder: string;
  isOpen: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      className={`flex-1 rounded-[20px] border px-4 py-4 ${
        isOpen ? 'border-primary-500 bg-primary-50/50' : 'border-[#DCE6F7] bg-white'
      }`}
    >
      <View className="flex-row items-start justify-between gap-3">
        <View className="flex-1">
          <HeroText className="text-[13px] font-semibold text-neutral-800">
            {label}
          </HeroText>
          <HeroText
            className={`mt-3 text-[16px] font-semibold ${
              value ? 'text-neutral-900' : 'text-neutral-400'
            }`}
          >
            {value ?? placeholder}
          </HeroText>
        </View>
        <ChevronDown
          size={18}
          color={isOpen ? '#2F64B6' : '#94A3B8'}
        />
      </View>
    </Pressable>
  );
}

function AdminUpdateFeed({
  updates,
  onOpenPhoto,
}: {
  updates: BookingUpdate[];
  onOpenPhoto: (update: BookingUpdate) => void;
}) {
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
                <Pressable
                  accessibilityRole="imagebutton"
                  accessibilityLabel={`Open ${item.photoOriginalName ?? 'booking update photo'}`}
                  onPress={() => onOpenPhoto(item)}
                >
                  <Image
                    source={{ uri: item.photoUrl }}
                    className="h-36 w-full rounded-[22px] bg-neutral-100"
                    resizeMode="cover"
                  />
                  <View className="absolute bottom-2 right-2 rounded-full bg-black/55 px-3 py-1.5">
                    <HeroText className="text-[11px] font-semibold text-white">
                      View photo
                    </HeroText>
                  </View>
                </Pressable>
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
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);
  const booking = bookings.find((item) => item.id === params.id);
  const [status, setStatus] = useState<BookingStatus>(booking?.status ?? 'confirmed');
  const [expectedCompletionDate, setExpectedCompletionDate] = useState('');
  const [expectedCompletionTime, setExpectedCompletionTime] = useState('');
  const [openExpectedCompletionSelector, setOpenExpectedCompletionSelector] = useState<
    'date' | 'time' | null
  >(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [updateComment, setUpdateComment] = useState('');
  const [updatePhoto, setUpdatePhoto] = useState<{
    uri: string;
    name: string;
    type: string;
  } | null>(null);
  const [updatePhotoType, setUpdatePhotoType] = useState<BackendBookingPhotoType>('racket');
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [isSubmittingUpdate, setIsSubmittingUpdate] = useState(false);
  const [previewUpdate, setPreviewUpdate] = useState<BookingUpdate | null>(null);

  useEffect(() => {
    if (booking) {
      setStatus(booking.status);
      setExpectedCompletionDate(
        booking.expectedCompletionAt
          ? formatLocalDateInputValue(booking.expectedCompletionAt)
          : '',
      );
      setExpectedCompletionTime(
        booking.expectedCompletionAt
          ? formatLocalTimeValue(booking.expectedCompletionAt)
          : '',
      );
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

  const expectedCompletionDateOptions = useMemo(() => {
    const options: { value: string; label: string }[] = [];
    const start = new Date();
    start.setHours(0, 0, 0, 0);

    for (let offset = 0; offset < 14; offset += 1) {
      const next = new Date(start);
      next.setDate(start.getDate() + offset);
      options.push({
        value: formatLocalDateInputValue(next),
        label: next.toLocaleDateString('en-MY', {
          weekday: 'short',
          day: 'numeric',
          month: 'short',
        }),
      });
    }

    return options;
  }, []);

  const expectedCompletionTimeOptions = useMemo(() => {
    const options: string[] = [];
    for (let hour = 10; hour <= 21; hour += 1) {
      for (const minute of [0, 30]) {
        if (hour === 21 && minute > 0) {
          continue;
        }
        options.push(
          `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`,
        );
      }
    }
    return options;
  }, []);

  if (!booking) {
    return null;
  }

  const stringItem = strings.find((item) => item.id === booking.stringId);
  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);
  const priceState = getPriceStateLabel(booking);
  const workflowCTA = getWorkflowActionLabel(status);
  const allowedNextStatuses = getAllowedNextStatuses(booking.status);
  const isWorkflowUnchanged = status === booking.status;
  const originalExpectedCompletionDate = booking.expectedCompletionAt
    ? formatLocalDateInputValue(booking.expectedCompletionAt)
    : '';
  const originalExpectedCompletionTime = booking.expectedCompletionAt
    ? formatLocalTimeValue(booking.expectedCompletionAt)
    : '';
  const hasExpectedCompletionChange =
    expectedCompletionDate !== originalExpectedCompletionDate
    || expectedCompletionTime !== originalExpectedCompletionTime;
  const isBookingCompleted = booking.status === 'completed';
  const isStatusChangeAllowed = !isWorkflowUnchanged && allowedNextStatuses.includes(status);
  const canSaveWorkflow =
    (!isWorkflowUnchanged && isStatusChangeAllowed) || hasExpectedCompletionChange;
  const selectedExpectedCompletionDateLabel =
    expectedCompletionDateOptions.find((item) => item.value === expectedCompletionDate)?.label;

  const buildExpectedCompletionTimestamp = () => {
    const dateValue = expectedCompletionDate.trim();
    const timeValue = expectedCompletionTime.trim();

    if (!dateValue && !timeValue) {
      return { value: null, errorMessage: null as string | null };
    }
    if (!dateValue || !timeValue) {
      return {
        value: null,
        errorMessage: 'Enter both expected completion date and time.',
      };
    }

    const normalized = `${dateValue}T${timeValue}`;
    const parsed = new Date(normalized);
    if (Number.isNaN(parsed.getTime())) {
      return {
        value: null,
        errorMessage: 'Expected completion time is invalid.',
      };
    }

    return { value: parsed.toISOString(), errorMessage: null as string | null };
  };

  const applyStatusChange = async () => {
    setError(null);

    const expectedCompletion = buildExpectedCompletionTimestamp();
    if (expectedCompletion.errorMessage) {
      setError(expectedCompletion.errorMessage);
      return;
    }

    if (!hasExpectedCompletionChange && status === booking.status) {
      return;
    }

    if (!isWorkflowUnchanged && !allowedNextStatuses.includes(status)) {
      setError(
        `Move this booking to ${formatBookingStatus(allowedNextStatuses[0] ?? booking.status)} before selecting ${formatBookingStatus(status)}.`,
      );
      return;
    }

    if (!token || user?.role !== 'admin') {
      setError('Your admin session expired. Sign in again before updating the workflow.');
      return;
    }

    setIsSaving(true);
    try {
      const updated = await backendApi.adminUpdateBookingStatus(token, booking.id, {
        status,
        expected_completion_datetime: hasExpectedCompletionChange
          ? expectedCompletion.value
          : undefined,
      });
      const priceByStringId = new Map(strings.map((item) => [item.id, item.price]));
      const mapped = mapBackendBookingToBooking(updated, priceByStringId, user.id);
      setLiveBookings(
        bookings.map((item) => (item.id === mapped.id ? mapped : item)),
      );
    } catch (saveError) {
      const message = saveError instanceof BackendApiError
        ? saveError.message
        : 'Failed to update booking status.';
      setError(message);
      Alert.alert('Status update failed', message);
    } finally {
      setIsSaving(false);
    }
  };

  const saveStatus = () => {
    setError(null);

    if (isBookingCompleted) {
      Alert.alert(
        'Booking already completed',
        'Completed bookings are locked so the workflow cannot be changed accidentally.',
      );
      return;
    }

    if (!hasExpectedCompletionChange && status === booking.status) {
      return;
    }

    if (!isWorkflowUnchanged && !isStatusChangeAllowed) {
      const nextStatus = allowedNextStatuses[0];
      setError(
        nextStatus
          ? `Next valid workflow step is ${formatBookingStatus(nextStatus)}.`
          : 'This workflow state cannot be changed.',
      );
      return;
    }

    const expectedCompletion = buildExpectedCompletionTimestamp();
    if (expectedCompletion.errorMessage) {
      setError(expectedCompletion.errorMessage);
      return;
    }

    const expectedCompletionLabel = expectedCompletion.value
      ? formatDateTime(expectedCompletion.value)
      : 'Not set';
    const message = isWorkflowUnchanged
      ? `Update the expected completion time to ${expectedCompletionLabel}?`
      : `Change this booking from ${formatBookingStatus(booking.status)} to ${formatBookingStatus(status)} and set expected completion to ${expectedCompletionLabel}?`;

    if (Platform.OS === 'web') {
      if (typeof globalThis.confirm !== 'function' || globalThis.confirm(message)) {
        void applyStatusChange();
      }
      return;
    }

    Alert.alert('Confirm status update', message, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Confirm', onPress: () => void applyStatusChange() },
    ]);
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
      const updated = updatePhoto
        ? await backendApi.adminUploadBookingPhoto(token, booking.id, {
            comment: updateComment,
            photo: updatePhoto,
            photoType: updatePhotoType,
          })
        : await backendApi.adminAddBookingUpdate(token, booking.id, {
            comment: updateComment,
          });
      const priceByStringId = new Map(strings.map((item) => [item.id, item.price]));
      const mapped = mapBackendBookingToBooking(updated, priceByStringId, user.id);
      setLiveBookings(
        bookings.map((item) => (item.id === mapped.id ? mapped : item)),
      );
      setUpdateComment('');
      setUpdatePhoto(null);
      setUpdatePhotoType('racket');
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
            <View className="gap-3" style={{ gap: 12 }}>
              <View
                className="flex-row items-start justify-between gap-3"
                style={{
                  flexDirection: 'row',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: 12,
                }}
              >
                <HeroText
                  className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700"
                  style={{
                    color: '#2563EB',
                    fontSize: 11,
                    fontWeight: '700',
                    letterSpacing: 1.9,
                    textTransform: 'uppercase',
                  }}
                >
                  Current status
                </HeroText>
                <AppChip
                  label={formatBookingStatus(booking.status)}
                  variant={getBookingStatusVariant(booking.status)}
                  size="md"
                />
              </View>

              <HeroText
                className="text-[28px] font-bold tracking-tight text-neutral-950"
                style={{
                  color: '#0A1020',
                  fontSize: 30,
                  fontWeight: '800',
                  lineHeight: 36,
                }}
              >
                {formatBookingStatus(booking.status)}
              </HeroText>
              <HeroText
                className="text-sm leading-5 text-neutral-500"
                style={{
                  color: '#737373',
                  fontSize: 14,
                  lineHeight: 22,
                }}
              >
                {getStatusHeroCopy(booking.status)}
              </HeroText>
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
              <View className="flex-row items-center gap-2">
                <CalendarClock size={15} color="#2F64B6" />
                <HeroText className="text-[13px] font-semibold text-neutral-700">
                  Expected completion: {booking.expectedCompletionAt ? formatDateTime(booking.expectedCompletionAt) : 'Not set'}
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
              const isSelectable = allowedNextStatuses.includes(item);

              return (
                <AppCard
                  key={item}
                  variant={isCurrent || isSelected ? 'highlighted' : 'subtle'}
                  padding="sm"
                  onPress={isSelectable ? () => setStatus(item) : undefined}
                  className={`min-w-[148px] flex-1 ${!isCurrent && !isSelectable ? 'opacity-60' : ''}`}
                >
                  <View className="gap-1.5">
                    <View className="flex-row items-center justify-between gap-2">
                      <AppChip
                        label={formatBookingStatus(item)}
                        variant={isCurrent || isSelected ? getBookingStatusVariant(item) : 'neutral'}
                        size="sm"
                        style={{ pointerEvents: 'none' }}
                      />
                      {isCurrent ? <CheckCircle2 size={15} color="#2F64B6" /> : null}
                    </View>
                    <HeroText className="text-[11px] font-medium leading-4 text-neutral-500">
                      {getWorkflowOptionHint({
                        isBookingCompleted,
                        isCurrent,
                        isSelectable,
                        isSelected,
                      })}
                    </HeroText>
                  </View>
                </AppCard>
              );
            })}
          </View>

          <View className="rounded-[22px] border border-[#DCE6F7] bg-white px-4 py-4">
            <HeroText className="text-[13px] font-semibold text-neutral-800">
              Expected completion
            </HeroText>
            <HeroText className="mt-1 text-[12px] leading-5 text-neutral-500">
              Set when the racket should be ready for collection.
            </HeroText>
            <View className="mt-3 flex-row gap-3">
              <SelectionField
                label="Date"
                value={selectedExpectedCompletionDateLabel}
                placeholder="Select date"
                isOpen={openExpectedCompletionSelector === 'date'}
                onPress={() =>
                  setOpenExpectedCompletionSelector((current) =>
                    current === 'date' ? null : 'date'
                  )
                }
              />
              <SelectionField
                label="Time"
                value={expectedCompletionTime || undefined}
                placeholder="Select time"
                isOpen={openExpectedCompletionSelector === 'time'}
                onPress={() =>
                  setOpenExpectedCompletionSelector((current) =>
                    current === 'time' ? null : 'time'
                  )
                }
              />
            </View>
            {openExpectedCompletionSelector === 'date' ? (
              <View className="mt-4 flex-row flex-wrap gap-2">
                {expectedCompletionDateOptions.map((option) => (
                  <AppChip
                    key={option.value}
                    label={option.label}
                    variant={
                      expectedCompletionDate === option.value ? 'primary' : 'neutral'
                    }
                    onPress={() => {
                      setExpectedCompletionDate(option.value);
                      setOpenExpectedCompletionSelector('time');
                    }}
                  />
                ))}
              </View>
            ) : null}
            {openExpectedCompletionSelector === 'time' ? (
              <View className="mt-4 flex-row flex-wrap gap-2">
                {expectedCompletionTimeOptions.map((option) => (
                  <AppChip
                    key={option}
                    label={option}
                    variant={expectedCompletionTime === option ? 'primary' : 'neutral'}
                    onPress={() => {
                      setExpectedCompletionTime(option);
                      setOpenExpectedCompletionSelector(null);
                    }}
                  />
                ))}
              </View>
            ) : null}
            {(expectedCompletionDate || expectedCompletionTime) ? (
              <View className="mt-4">
                <AppChip
                  label="Clear expected completion"
                  variant="neutral"
                  onPress={() => {
                    setExpectedCompletionDate('');
                    setExpectedCompletionTime('');
                    setOpenExpectedCompletionSelector(null);
                  }}
                />
              </View>
            ) : null}
          </View>

          {error ? (
            <HeroText className="text-sm font-semibold text-danger-600">
              {error}
            </HeroText>
          ) : null}

          {isBookingCompleted ? (
            <HeroText className="text-sm font-semibold text-neutral-500">
              This booking is completed. Status changes are disabled to prevent accidental edits.
            </HeroText>
          ) : null}

          <AppButton
            label={
              !canSaveWorkflow
                ? `Current status: ${formatBookingStatus(booking.status)}`
                : hasExpectedCompletionChange && isWorkflowUnchanged
                  ? 'Save expected completion'
                  : isStatusChangeAllowed
                    ? workflowCTA
                    : 'Select the next workflow step'
            }
            size="lg"
            className="mt-1"
            onPress={saveStatus}
            isLoading={isSaving}
            isDisabled={!canSaveWorkflow || isBookingCompleted}
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
            <SummaryRow
              label="Player"
              value={booking.customerName ?? 'Walk-in player'}
            />
            <SummaryRow
              label="Contact"
              value={
                booking.customerPhone
                ?? 'No contact provided'
              }
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
            <SummaryRow
              label="Expected ready"
              value={
                booking.expectedCompletionAt
                  ? formatDateTime(booking.expectedCompletionAt)
                  : 'Not set'
              }
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
        <AdminUpdateFeed updates={sortedUpdates} onOpenPhoto={setPreviewUpdate} />
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
            <View className="mt-3 gap-3">
              <Image
                source={{ uri: updatePhoto.uri }}
                className="h-36 w-full rounded-[22px] bg-neutral-100"
                resizeMode="cover"
              />
              <View className="flex-row flex-wrap gap-2">
                {PHOTO_TYPE_OPTIONS.map((option) => (
                  <AppChip
                    key={option.value}
                    label={option.label}
                    variant={updatePhotoType === option.value ? 'primary' : 'neutral'}
                    onPress={() => setUpdatePhotoType(option.value)}
                  />
                ))}
              </View>
            </View>
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
                onPress={() => {
                  setUpdatePhoto(null);
                  setUpdatePhotoType('racket');
                }}
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

      <PhotoPreviewModal
        visible={Boolean(previewUpdate?.photoUrl)}
        imageUrl={previewUpdate?.photoUrl}
        title="Uploaded photo"
        subtitle={previewUpdate ? getUpdateMetaLabel(previewUpdate) : 'Booking photo'}
        note={previewUpdate?.comment}
        accessibilityLabel={previewUpdate?.photoOriginalName ?? 'Booking update photo'}
        onClose={() => setPreviewUpdate(null)}
      />
    </AppScreen>
  );
}
