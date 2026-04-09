import React, { useEffect, useMemo, useState } from 'react';
import { Image, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { CalendarClock, ChevronLeft, Store } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { SlotPicker } from '../../../components/booking/SlotPicker';
import {
  useAppStore,
  useBusinessHoursState,
  useBackendAccessToken,
  useCurrentUser,
  useStrings,
} from '../../../store/appStore';
import { MOCK_BOOKING_SLOTS } from '../../../mocks';
import { getAdminById, getStringById } from '../../../services/mockAppService';
import { formatDateLabel, formatLocalDateInputValue } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendSlotToBookingSlot } from '../../../services/backendMappers';
import type { BookingSlot } from '../../../types/domain';

const bookingSchema = z.object({
  racketBrand: z.string().min(1, 'Racket brand is required'),
  racketModel: z.string().min(1, 'Racket model is required'),
  requestedTension: z.coerce.number().min(18).max(32),
  notes: z.string().optional(),
});

type BookingForm = z.infer<typeof bookingSchema>;
type BookingFormInput = z.input<typeof bookingSchema>;

export default function NewBookingScreen() {
  const params = useLocalSearchParams<{ stringId?: string }>();
  const router = useRouter();
  const user = useCurrentUser();
  const strings = useStrings();
  const token = useBackendAccessToken();
  const setBookingDraft = useAppStore((state) => state.setBookingDraft);
  const businessHours = useBusinessHoursState();

  if (!user || user.role !== 'player') {
    return null;
  }

  const selectedString =
    getStringById(params.stringId) ??
    (params.stringId ? undefined : strings[0]) ??
    getStringById('string-001');
  const adminId = user.preferredAdminId;
  const today = formatLocalDateInputValue(new Date());
  const [selectedDate, setSelectedDate] = useState(today);
  const [liveSlots, setLiveSlots] = useState<BookingSlot[]>([]);
  const [didLoadLiveSlots, setDidLoadLiveSlots] = useState(false);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [slotsError, setSlotsError] = useState<string | null>(null);
  const [bookingPhoto, setBookingPhoto] = useState<{
    uri: string;
    name: string;
    type: string;
  } | null>(null);
  const sourceSlots =
    token && didLoadLiveSlots && !slotsError
      ? liveSlots
      : MOCK_BOOKING_SLOTS.filter((item) => item.adminId === adminId);
  const slots = sourceSlots.filter((item) => item.adminId === adminId && item.date === selectedDate);
  const availableSlots = useMemo(
    () => slots.filter((item) => item.availableSpots > 0),
    [slots]
  );
  const [selectedSlotId, setSelectedSlotId] = useState<string | undefined>(
    availableSlots[0]?.id
  );
  const [slotError, setSlotError] = useState<string | null>(null);
  const availableDates = Array.from(
    new Set(sourceSlots.filter((item) => item.adminId === adminId).map((item) => item.date))
  );
  const selectedSlot = slots.find(
    (item) => item.id === selectedSlotId && item.availableSpots > 0
  );
  const selectedAdmin = getAdminById(adminId);
  const adminHours = businessHours.find((item) => item.adminId === adminId);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<BookingFormInput, unknown, BookingForm>({
    resolver: zodResolver(bookingSchema),
    defaultValues: {
      racketBrand: 'Yonex',
      racketModel: 'Astrox 88D Pro',
      requestedTension: selectedString?.recommendedTension[0] ?? 26,
      notes: '',
    },
  });

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    const hydrateSlots = async () => {
      setIsLoadingSlots(true);
      setSlotsError(null);
      try {
        const response = await backendApi.listSlots(token, {
          date_from: today,
          days: 14,
        });
        if (cancelled) {
          return;
        }
        const mappedSlots = response.items.map((item) =>
          mapBackendSlotToBookingSlot(item, adminId),
        );
        setLiveSlots(mappedSlots);
        setDidLoadLiveSlots(true);
        const firstAvailable = mappedSlots.find((item) => item.availableSpots > 0);
        if (firstAvailable) {
          setSelectedDate(firstAvailable.date);
          setSelectedSlotId(firstAvailable.id);
        }
      } catch (error) {
        if (!cancelled) {
          setSlotsError(
            error instanceof BackendApiError
              ? error.message
              : 'Failed to load backend slots.',
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSlots(false);
        }
      }
    };

    void hydrateSlots();

    return () => {
      cancelled = true;
    };
  }, [adminId, today, token]);

  useEffect(() => {
    const currentSelection = slots.find((item) => item.id === selectedSlotId);

    if (currentSelection?.availableSpots) {
      if (slotError) {
        setSlotError(null);
      }
      return;
    }

    setSelectedSlotId(availableSlots[0]?.id);
    setSlotError(
      availableSlots.length > 0
        ? null
        : 'No drop-off slots are available on this date. Choose another date to continue.'
    );
  }, [availableSlots, selectedSlotId, slotError, slots]);

  const onSubmit = async (data: BookingForm) => {
    if (!selectedString || !selectedAdmin || !selectedSlot || selectedSlot.availableSpots < 1) {
      setSlotError('Select an available drop-off slot before continuing.');
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 350));
    setBookingDraft({
      stringId: selectedString.id,
      adminId: selectedAdmin.id,
      racketId: null,
      racketBrand: data.racketBrand,
      racketModel: data.racketModel,
      requestedTension: data.requestedTension,
      notes: data.notes ?? '',
      dropOffDate: selectedSlot.date,
      dropOffTime: selectedSlot.time,
      photoUri: bookingPhoto?.uri,
      photoName: bookingPhoto?.name,
      photoContentType: bookingPhoto?.type,
      saveRacket: false,
    });
    router.push('/player/bookings/summary');
  };

  const pickBookingPhoto = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.85,
      allowsEditing: false,
    });

    if (result.canceled || !result.assets[0]) {
      return;
    }

    const asset = result.assets[0];
    setBookingPhoto({
      uri: asset.uri,
      name: asset.fileName ?? `booking-photo-${Date.now()}.jpg`,
      type: asset.mimeType ?? 'image/jpeg',
    });
  };

  if (!selectedString) {
    return null;
  }

  return (
    <AppScreen
      headerVariant="flow"
      title="New booking"
      subtitle="Configure the stringing request and reserve a believable drop-off window."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="highlighted" className="rounded-[32px]" padding="lg">
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
          Selected string
        </HeroText>
        <HeroText className="mt-2 text-[26px] font-bold tracking-tight text-neutral-950">
          {selectedString.brand} {selectedString.model}
        </HeroText>
        <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
          Recommended at {selectedString.recommendedTension[0]} to {selectedString.recommendedTension[1]} lbs.
        </HeroText>
        <View className="mt-4 flex-row flex-wrap gap-2">
          <AppChip label={selectedString.gauge} variant="neutral" />
          <AppChip label={selectedString.category} variant="primary" />
        </View>
      </AppCard>

      <AppSection eyebrow="Store" title="Service desk">
        <AppCard variant="highlighted" padding="md">
          <View className="flex-row items-start gap-4">
            <View className="h-12 w-12 items-center justify-center rounded-[18px] bg-primary-50">
              <Store size={20} color="#2F64B6" />
            </View>
            <View className="flex-1">
              <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                {selectedAdmin?.businessName}
              </HeroText>
              <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                {selectedAdmin?.city} • Avg turnaround {selectedAdmin?.averageTurnaroundHours} hours
              </HeroText>
              <HeroText className="mt-2 text-xs uppercase tracking-[0.18em] text-primary-700">
                Single-store prototype
              </HeroText>
            </View>
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Setup" title="Racket and tension">
        <AppCard variant="elevated" padding="lg">
          <HeroText className="mb-3 text-sm font-semibold text-neutral-900">
            Enter the racket details for this booking.
          </HeroText>
          <Controller
            control={control}
            name="racketBrand"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Racket brand"
                placeholder="Yonex, Victor, Li-Ning..."
                value={value}
                onChangeText={onChange}
                error={errors.racketBrand?.message}
              />
            )}
          />
          <Controller
            control={control}
            name="racketModel"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Racket model"
                placeholder="Astrox 88D Pro"
                value={value}
                onChangeText={onChange}
                error={errors.racketModel?.message}
              />
            )}
          />
          <Controller
            control={control}
            name="requestedTension"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Requested tension"
                placeholder="26"
                keyboardType="numeric"
                value={String(value)}
                onChangeText={onChange}
                error={errors.requestedTension?.message}
                helperText={selectedString.tensionNote}
              />
            )}
          />
          <Controller
            control={control}
            name="notes"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Notes"
                placeholder="Knots, logo alignment, feel preference, or special request..."
                value={value}
                onChangeText={onChange}
                multiline
                inputClassName="min-h-24"
              />
            )}
          />
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Drop-off" title="Pick your date and time">
        <View className="gap-4">
          {slotsError ? (
            <AppCard variant="highlighted" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-700">
                {slotsError} Showing local fallback slots so you can continue the prototype flow.
              </HeroText>
            </AppCard>
          ) : null}
          {isLoadingSlots ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-600">
                Loading live backend slots from the store business hours...
              </HeroText>
            </AppCard>
          ) : null}
          <View className="flex-row flex-wrap gap-2">
            {availableDates.map((date) => (
              <AppChip
                key={date}
                label={formatDateLabel(date)}
                size="md"
                variant={selectedDate === date ? 'primary' : 'neutral'}
                onPress={() => {
                  setSelectedDate(date);
                  setSelectedSlotId(
                    sourceSlots.find(
                      (item) =>
                        item.adminId === adminId
                        && item.date === date
                        && item.availableSpots > 0
                    )?.id
                  );
                  setSlotError(null);
                }}
              />
            ))}
          </View>
          <SlotPicker
            slots={slots}
            selectedSlotId={selectedSlotId}
            onSelect={(slot) => {
              setSelectedSlotId(slot.id);
              setSlotError(null);
            }}
          />
          {selectedSlot ? null : (
            <AppCard variant="highlighted" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-700">
                {slotError ?? 'No drop-off slots are available on this date. Pick another date to continue.'}
              </HeroText>
            </AppCard>
          )}
          <AppCard variant="subtle" padding="md">
            <View className="flex-row items-center gap-3">
              <CalendarClock size={18} color="#2F64B6" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                Available times are shown as if driven by admin business hours. Current schedule: {adminHours?.days.find((day) => day.day === selectedSlot?.dayLabel)?.openTime} to {adminHours?.days.find((day) => day.day === selectedSlot?.dayLabel)?.closeTime} on {selectedSlot?.dayLabel}.
              </HeroText>
            </View>
          </AppCard>
        </View>
      </AppSection>

      <AppSection eyebrow="Photo" title="Optional racket photo">
        <AppCard variant="elevated" padding="lg">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Add a photo of the racket or current string condition so the admin can review it with the booking.
          </HeroText>
          {bookingPhoto ? (
            <Image
              source={{ uri: bookingPhoto.uri }}
              className="mt-4 h-48 w-full rounded-[24px] bg-neutral-100"
              resizeMode="cover"
            />
          ) : null}
          <View className="mt-4 flex-row gap-3">
            <AppButton
              label={bookingPhoto ? 'Change photo' : 'Upload photo'}
              variant="outline"
              className="flex-1"
              onPress={pickBookingPhoto}
            />
            {bookingPhoto ? (
              <AppButton
                label="Remove"
                variant="ghost"
                className="flex-1"
                onPress={() => setBookingPhoto(null)}
              />
            ) : null}
          </View>
        </AppCard>
      </AppSection>

      <View className="mb-12 mt-8">
        <AppButton
          label="Continue to summary"
          size="lg"
          onPress={handleSubmit(onSubmit)}
          isLoading={isSubmitting}
          isDisabled={!selectedSlot}
        />
      </View>
    </AppScreen>
  );
}
