import React, { useEffect, useMemo, useState } from 'react';
import { Image, Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { CalendarClock, ChevronDown, ChevronUp, Minus, Plus, Store, Upload } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppSelect } from '../../../components/ui/AppSelect';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { SlotPicker } from '../../../components/booking/SlotPicker';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  usePreferredAdminId,
  useRackets,
  useStrings,
} from '../../../store/appStore';
import { formatCurrency, formatDateLabel, formatLocalDateInputValue } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendSlotToBookingSlot } from '../../../services/backendMappers';
import type { BookingSlot, PlayerProfile } from '../../../types/domain';

const bookingSchema = z.object({
  racketBrand: z.string().min(1, 'Racket brand is required'),
  racketModel: z.string().min(1, 'Racket model is required'),
  requestedTension: z.coerce.number().min(18).max(32),
  notes: z.string().optional(),
});

type BookingForm = z.infer<typeof bookingSchema>;
type BookingFormInput = z.input<typeof bookingSchema>;
type SlotPeriod = 'morning' | 'afternoon' | 'evening';
type BookingStep = 1 | 2 | 3;

const BOOKING_STEPS = [
  { id: 1, label: 'String' },
  { id: 2, label: 'Setup' },
  { id: 3, label: 'Drop-off' },
] as const;

const SLOT_PERIOD_OPTIONS = [
  { id: 'morning', label: 'Morning' },
  { id: 'afternoon', label: 'Afternoon' },
  { id: 'evening', label: 'Evening' },
] as const;

const MANUAL_RACKET_OPTION_ID = '__manual_racket__';

function getSlotPeriod(slot: BookingSlot): SlotPeriod {
  const hour = Number(slot.time.split(':')[0] ?? '0');

  if (hour < 12) {
    return 'morning';
  }

  if (hour < 17) {
    return 'afternoon';
  }

  return 'evening';
}

export default function NewBookingScreen() {
  const user = useCurrentUser();

  if (!user || user.role !== 'player') {
    return null;
  }

  return <NewBookingContent user={user} />;
}

function NewBookingContent({ user }: { user: PlayerProfile }) {
  const params = useLocalSearchParams<{ racketId?: string; stringId?: string }>();
  const router = useRouter();
  const preferredAdminId = usePreferredAdminId();
  const strings = useStrings();
  const rackets = useRackets();
  const token = useBackendAccessToken();
  const setBookingDraft = useAppStore((state) => state.setBookingDraft);
  const storeSettings = useAppStore((state) => state.storeSettings);
  const playerRackets = rackets.filter((item) => item.playerId === user.id);
  const [selectedRacketId, setSelectedRacketId] = useState<string | null>(
    params.racketId ?? null,
  );
  const [currentStep, setCurrentStep] = useState<BookingStep>(1);
  const selectedRacket = playerRackets.find(
    (item) => item.id === selectedRacketId,
  );

  const requestedStringId = params.stringId;
  const requestedString = requestedStringId
    ? strings.find((item) => item.id === requestedStringId)
    : undefined;
  const fallbackString = strings[0];
  const [selectedStringId, setSelectedStringId] = useState(
    requestedString?.id ?? fallbackString?.id ?? ''
  );
  const [isStringPickerOpen, setIsStringPickerOpen] = useState(!requestedStringId);
  const selectedString =
    strings.find((item) => item.id === selectedStringId) ??
    requestedString ??
    fallbackString;
  const adminId = preferredAdminId ?? 'main';
  const today = formatLocalDateInputValue(new Date());
  const [selectedDate, setSelectedDate] = useState(today);
  const [liveSlots, setLiveSlots] = useState<BookingSlot[]>([]);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [slotsError, setSlotsError] = useState<string | null>(null);
  const [bookingPhoto, setBookingPhoto] = useState<{
    uri: string;
    name: string;
    type: string;
  } | null>(null);
  const [serviceMethod, setServiceMethod] = useState<
    'counter_dropoff' | 'pickup_request'
  >('counter_dropoff');
  const sourceSlots = liveSlots;
  const slots = sourceSlots.filter((item) => item.adminId === adminId && item.date === selectedDate);
  const availableSlots = useMemo(
    () => slots.filter((item) => item.availableSpots > 0),
    [slots]
  );
  const [selectedSlotId, setSelectedSlotId] = useState<string | undefined>(
    availableSlots[0]?.id
  );
  const [slotError, setSlotError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<SlotPeriod>('morning');
  const availableDates = Array.from(
    new Set(sourceSlots.filter((item) => item.adminId === adminId).map((item) => item.date))
  );
  const selectDate = (date: string) => {
    setSelectedDate(date);
    setSelectedSlotId(
      sourceSlots.find(
        (item) => item.adminId === adminId && item.date === date && item.availableSpots > 0,
      )?.id,
    );
    setSlotError(null);
  };
  const selectedSlot = slots.find(
    (item) => item.id === selectedSlotId && item.availableSpots > 0
  );
  const selectedAdminName =
    storeSettings?.storeName.trim()
    || 'Assigned shop';
  const selectedAdminMeta =
    storeSettings?.address.trim()
    || 'Drop-off service desk';
  const recommendedMin = selectedString?.recommendedTension[0] ?? 24;
  const recommendedMax = selectedString?.recommendedTension[1] ?? 29;
  const showPeriodFilter = slots.length > 6;
  const visibleSlots = showPeriodFilter
    ? slots.filter((item) => getSlotPeriod(item) === selectedPeriod)
    : slots;

  const openRacketRegistration = () => {
    const stringQuery = requestedStringId
      ? `&stringId=${encodeURIComponent(requestedStringId)}`
      : '';
    router.push(`/player/rackets/new?returnTo=booking${stringQuery}`);
  };

  const {
    control,
    handleSubmit,
    trigger,
    formState: { errors, isSubmitting },
    setValue,
  } = useForm<BookingFormInput, unknown, BookingForm>({
    resolver: zodResolver(bookingSchema),
    defaultValues: {
      racketBrand: '',
      racketModel: '',
      requestedTension: selectedString?.recommendedTension[0] ?? 26,
      notes: '',
    },
  });
  useEffect(() => {
    if (!selectedString) {
      return;
    }

    setValue('requestedTension', selectedString.recommendedTension[0]);
  }, [selectedString?.id, selectedString, setValue]);

  useEffect(() => {
    if (selectedRacket) {
      setValue('racketBrand', selectedRacket.brand, { shouldValidate: true });
      setValue('racketModel', selectedRacket.model, { shouldValidate: true });
    }
  }, [selectedRacket, setValue]);

  useEffect(() => {
    if (requestedString?.id) {
      setSelectedStringId(requestedString.id);
      setIsStringPickerOpen(false);
      return;
    }

    if (!selectedStringId && fallbackString?.id) {
      setSelectedStringId(fallbackString.id);
    }
  }, [fallbackString?.id, requestedString?.id, selectedStringId]);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    const hydrateSlots = async () => {
      setIsLoadingSlots(true);
      setSlotsError(null);
      setLiveSlots([]);
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
        const firstAvailable = mappedSlots.find((item) => item.availableSpots > 0);
        if (firstAvailable) {
          setSelectedDate(firstAvailable.date);
          setSelectedSlotId(firstAvailable.id);
        }
      } catch (error) {
        if (!cancelled) {
          setLiveSlots([]);
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

  useEffect(() => {
    if (!selectedString || !showPeriodFilter) {
      return;
    }

    const hasVisibleSlots = slots.some((item) => getSlotPeriod(item) === selectedPeriod);

    if (hasVisibleSlots) {
      return;
    }

    const fallbackSlot =
      slots.find((item) => item.id === selectedSlotId) ??
      availableSlots[0] ??
      slots[0];

    if (fallbackSlot) {
      setSelectedPeriod(getSlotPeriod(fallbackSlot));
    }
  }, [availableSlots, selectedPeriod, selectedSlotId, selectedString, showPeriodFilter, slots]);

  const onSubmit = (data: BookingForm) => {
    if (!token) {
      setSlotError('Your player session expired. Sign in again to continue.');
      return;
    }

    if (!selectedString || !selectedSlot || selectedSlot.availableSpots < 1) {
      setSlotError('Select an available drop-off slot before continuing.');
      return;
    }

    setBookingDraft({
      stringId: selectedString.id,
      adminId,
      racketId: selectedRacket?.id ?? null,
      racketBrand: data.racketBrand,
      racketModel: data.racketModel,
      requestedTension: data.requestedTension,
      notes: data.notes ?? '',
      serviceMethod,
      slotId: selectedSlot.id,
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

  const currentStepLabel = BOOKING_STEPS[currentStep - 1]?.label ?? 'String';

  const goBackStep = () => {
    if (currentStep === 1) {
      router.back();
      return;
    }
    setCurrentStep((step) => (step - 1) as BookingStep);
  };

  const advanceStep = async () => {
    if (currentStep === 1) {
      setCurrentStep(2);
      return;
    }

    if (currentStep === 2) {
      const isSetupValid = await trigger([
        'racketBrand',
        'racketModel',
        'requestedTension',
      ]);
      if (!isSetupValid) {
        return;
      }
      setCurrentStep(3);
      return;
    }

    await handleSubmit(onSubmit)();
  };

  if (requestedStringId && !requestedString && strings.length === 0 && token) {
    return (
      <AppScreen
        title="Loading catalog"
        subtitle="Checking the selected string against the active catalog."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Please wait while the live catalog is loaded.
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  if (requestedStringId && !requestedString) {
    return (
      <AppScreen
        title="String unavailable"
        subtitle="The selected string is no longer in the active catalog."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Choose another string from the catalog before creating this booking.
          </HeroText>
          <View className="mt-4">
            <AppButton
              label="Browse strings"
              onPress={() => router.replace('/player/strings')}
            />
          </View>
        </AppCard>
      </AppScreen>
    );
  }

  if (!selectedString) {
    return (
      <AppScreen
        title="Catalog unavailable"
        subtitle="No live string data is available for a new booking."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Return to the catalog and retry after the backend connection is restored.
          </HeroText>
          <View className="mt-4">
            <AppButton
              label="Back to catalog"
              onPress={() => router.replace('/player/strings')}
            />
          </View>
        </AppCard>
      </AppScreen>
    );
  }

  const selectedDateLabel = formatDateLabel(selectedSlot?.date ?? selectedDate);
  const selectedTimeLabel = selectedSlot?.label ?? 'Select a slot';
  const slotSupportCopy = slotsError
    ? `${slotsError} Live slots are unavailable; retry before continuing.`
    : 'Times reflect current shop availability.';
  const selectedCategoryLabel =
    selectedString.category.charAt(0).toUpperCase() + selectedString.category.slice(1);
  const selectedStringHasPrice = selectedString.priceStatus === 'priced' && selectedString.price > 0;

  return (
    <AppScreen
      headerVariant="flow"
      compactHeader
      title="New booking"
      subtitle={`Step ${currentStep} of ${BOOKING_STEPS.length} · ${currentStepLabel}`}
      showBackButton
      onBackPress={() => router.back()}
      footer={
        <View className="gap-2 border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          <AppButton
            label={
              currentStep === 1
                ? 'Continue to setup'
                : currentStep === 2
                  ? 'Continue to drop-off'
                  : 'Review booking'
            }
            size="lg"
            onPress={() => void advanceStep()}
            isLoading={isSubmitting}
            isDisabled={currentStep === 3 && !selectedSlot}
          />
          {currentStep > 1 ? (
            <AppButton
              label="Back"
              variant="outline"
              size="lg"
              onPress={goBackStep}
            />
          ) : null}
        </View>
      }
    >
      <View
        className="mb-4"
        accessibilityRole="progressbar"
        accessibilityLabel="Booking progress"
        accessibilityValue={{
          min: 1,
          max: BOOKING_STEPS.length,
          now: currentStep,
        }}
      >
        <View className="flex-row gap-1.5">
          {BOOKING_STEPS.map((step) => (
            <View key={step.id} className="flex-1 gap-1">
              <View
                className={`h-1 rounded-full ${
                  step.id <= currentStep ? 'bg-primary-600' : 'bg-primary-100'
                }`}
              />
              <HeroText
                className={`text-[10px] font-semibold uppercase tracking-[0.12em] ${
                  step.id === currentStep ? 'text-primary-700' : 'text-slate-400'
                }`}
              >
                {step.id}. {step.label}
              </HeroText>
            </View>
          ))}
        </View>
      </View>

      {currentStep === 1 ? (
        <AppCard variant="highlighted" className="rounded-[28px]" padding="md">
        <View className="flex-row items-start justify-between gap-3">
          <View className="min-w-0 flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
              Selected string
            </HeroText>
            <HeroText className="mt-1.5 text-[22px] font-bold tracking-tight text-neutral-950">
              {selectedString.brand} {selectedString.model}
            </HeroText>
            <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
              Recommended at {recommendedMin}–{recommendedMax} lbs
            </HeroText>
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Choose string"
            onPress={() => setIsStringPickerOpen((current) => !current)}
            className="h-11 w-11 items-center justify-center rounded-[16px] border border-primary-600 bg-primary-600 shadow-soft"
          >
            {isStringPickerOpen ? (
              <ChevronUp size={20} color="#FFFFFF" strokeWidth={2.7} />
            ) : (
              <ChevronDown size={20} color="#FFFFFF" strokeWidth={2.7} />
            )}
          </Pressable>
        </View>
        <View className="mt-3 flex-row flex-wrap gap-2">
          <AppChip label={selectedString.gauge} variant="neutral" />
          <AppChip label={selectedCategoryLabel} variant="primary" />
          {selectedStringHasPrice ? (
            <AppChip label={formatCurrency(selectedString.price)} variant="secondary" />
          ) : null}
        </View>

        {isStringPickerOpen ? (
          <View className="mt-4 rounded-[22px] border border-[#DCE6F7] bg-white px-3 py-3">
            <HeroText className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              Choose from catalog
            </HeroText>
            <View className="gap-2">
              {strings.map((item) => {
                const isSelected = item.id === selectedString.id;
                const shouldShowPrice = item.priceStatus === 'priced' && item.price > 0;

                return (
                  <Pressable
                    key={item.id}
                    accessibilityRole="button"
                    accessibilityLabel={`${item.brand} ${item.model}, ${item.gauge}`}
                    accessibilityState={{ selected: isSelected }}
                    onPress={() => {
                      setSelectedStringId(item.id);
                      setIsStringPickerOpen(false);
                    }}
                    className={`rounded-[18px] border px-3 py-3 ${
                      isSelected
                        ? 'border-primary-200 bg-primary-50'
                        : 'border-[#E8EEF8] bg-white'
                    }`}
                  >
                    <View className="flex-row items-start justify-between gap-3">
                      <View className="min-w-0 flex-1">
                        <HeroText
                          className={`text-[14px] font-semibold ${
                            isSelected ? 'text-primary-700' : 'text-slate-900'
                          }`}
                          numberOfLines={1}
                        >
                          {item.brand} {item.model}
                        </HeroText>
                        <HeroText className="mt-1 text-[12px] text-slate-500" numberOfLines={1}>
                          {item.gauge} · {item.category}
                        </HeroText>
                      </View>
                      <View className="items-end gap-2">
                        {shouldShowPrice ? (
                          <HeroText className="text-[13px] font-bold text-slate-900">
                            {formatCurrency(item.price)}
                          </HeroText>
                        ) : null}
                        {isSelected ? <AppChip label="Selected" variant="primary" /> : null}
                      </View>
                    </View>
                  </Pressable>
                );
              })}
            </View>
          </View>
        ) : null}
        </AppCard>
      ) : null}

      {currentStep === 3 ? (
        <AppSection eyebrow="Store" title="Service desk" variant="compact">
        <AppCard variant="elevated" padding="md">
          <View className="flex-row items-start gap-3">
            <View className="h-11 w-11 items-center justify-center rounded-[16px] bg-primary-50">
              <Store size={20} color="#2F64B6" />
            </View>
            <View className="flex-1">
              <HeroText className="text-[17px] font-bold tracking-tight text-neutral-950">
                {selectedAdminName}
              </HeroText>
              <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
                {selectedAdminMeta}
              </HeroText>
            </View>
          </View>
        </AppCard>
        </AppSection>
      ) : null}

      {currentStep === 2 ? (
        <AppSection eyebrow="Setup" title="Racket and tension" variant="compact">
        <AppCard variant="elevated" padding="md">
          <View className="mb-4 gap-3">
            <AppSelect
              label="Racket passport"
              value={selectedRacket?.id ?? MANUAL_RACKET_OPTION_ID}
              options={[
                {
                  id: MANUAL_RACKET_OPTION_ID,
                  label: 'Manual racket entry',
                  description: 'Use this for a frame that is not registered yet.',
                },
                ...playerRackets.map((racket) => ({
                  id: racket.id,
                  label: racket.nickname,
                  description: `${racket.brand} ${racket.model} · ${racket.currentTension} lbs · ${racket.serviceCount} services`,
                })),
              ]}
              onChange={(id) => {
                const nextRacketId = id === MANUAL_RACKET_OPTION_ID ? null : id;
                setSelectedRacketId(nextRacketId);
                if (!nextRacketId) {
                  setValue('racketBrand', '', { shouldValidate: true });
                  setValue('racketModel', '', { shouldValidate: true });
                }
              }}
              helperText={
                playerRackets.length === 0
                  ? 'No saved rackets yet. Continue manually or register this frame here.'
                  : 'Choose a saved racket or enter the frame details manually.'
              }
            />
            {params.racketId && !selectedRacket ? (
              <HeroText className="text-xs font-medium leading-5 text-amber-700">
                The requested saved racket is unavailable. Choose another racket
                or continue with manual entry.
              </HeroText>
            ) : null}
            <AppButton
              label={playerRackets.length === 0 ? 'Register this racket' : 'Register another racket'}
              variant="outline"
              onPress={openRacketRegistration}
            />
          </View>
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
                isDisabled={Boolean(selectedRacket)}
                helperText={
                  selectedRacket
                    ? 'Snapshot copied from the selected passport.'
                    : undefined
                }
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
                isDisabled={Boolean(selectedRacket)}
              />
            )}
          />
          <Controller
            control={control}
            name="requestedTension"
            render={({ field: { onChange, value } }) => (
              <View className="mb-4">
                <HeroText className="mb-2 ml-1 text-sm font-semibold text-foreground">
                  Requested tension
                </HeroText>
                <View className="rounded-[24px] border border-separator bg-surface-secondary p-1 shadow-soft">
                  <View className="rounded-[20px] border border-field-border bg-field-background px-4 py-3">
                    <View className="flex-row items-center justify-between gap-2">
                      <AppIconButton
                        icon={<Minus size={16} color="#2F64B6" />}
                        accessibilityLabel="Decrease requested tension"
                        variant="surface"
                        onPress={() => onChange(Math.max(18, Number(value) - 1))}
                      />
                      <View className="min-w-0 flex-1 items-center" style={{ minWidth: 0, flex: 1, alignItems: 'center' }}>
                        <HeroText
                          className="text-[28px] font-bold tracking-tight text-neutral-950"
                          numberOfLines={1}
                          adjustsFontSizeToFit
                        >
                          {String(value)} lbs
                        </HeroText>
                        <HeroText
                          className="mt-1 text-xs uppercase tracking-[0.18em] text-neutral-400"
                          numberOfLines={1}
                          adjustsFontSizeToFit
                        >
                          Requested tension
                        </HeroText>
                      </View>
                      <AppIconButton
                        icon={<Plus size={16} color="#2F64B6" />}
                        accessibilityLabel="Increase requested tension"
                        variant="surface"
                        onPress={() => onChange(Math.min(32, Number(value) + 1))}
                      />
                    </View>
                    <AppInput
                      className="mb-0 mt-3"
                      label="Set exact value"
                      placeholder="24"
                      keyboardType="numeric"
                      value={String(value)}
                      onChangeText={onChange}
                      error={errors.requestedTension?.message}
                      containerClassName="border-0 bg-transparent p-0 shadow-none"
                      innerContainerClassName="min-h-[44px] rounded-[18px] px-3 py-0"
                    />
                  </View>
                </View>
                <HeroText className="mt-2 ml-1 text-xs leading-5 text-muted">
                  Recommended range: {recommendedMin}–{recommendedMax} lbs based on your saved profile.
                </HeroText>
              </View>
            )}
          />
          <Controller
            control={control}
            name="notes"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Notes (optional)"
                placeholder="Knots, logo alignment, feel preference, or special request..."
                value={value}
                onChangeText={onChange}
                multiline
                inputClassName="min-h-20"
              />
            )}
          />
        </AppCard>
        </AppSection>
      ) : null}

      {currentStep === 3 ? (
        <AppSection
          eyebrow="Handover"
          title="Pickup or counter drop-off"
          variant="compact"
        >
        <AppSelect
          label="Service method"
          value={serviceMethod}
          options={[
            {
              id: 'counter_dropoff',
              label: 'Counter drop-off',
              description: 'Bring the racket to the shop service desk.',
            },
            {
              id: 'pickup_request',
              label: 'Request pickup',
              description: 'Ask the shop to confirm pickup logistics.',
            },
          ]}
          onChange={(id) => setServiceMethod(id as typeof serviceMethod)}
        />
        <HeroText className="mt-3 text-xs leading-5 text-neutral-500">
          Pickup is a request for the selected slot; the shop confirms logistics
          through booking updates.
        </HeroText>
        </AppSection>
      ) : null}

      {currentStep === 3 ? (
        <AppSection eyebrow="Drop-off" title="Date and time" variant="compact">
        <View className="gap-4">
          {slotsError && !isLoadingSlots ? (
            <AppCard variant="highlighted" padding="sm">
              <HeroText className="text-sm leading-6 text-neutral-700">
                {slotSupportCopy}
              </HeroText>
            </AppCard>
          ) : null}
          {isLoadingSlots ? (
            <AppCard variant="subtle" padding="sm">
              <HeroText className="text-sm leading-6 text-neutral-600">
                Loading live backend slots from the store business hours...
              </HeroText>
            </AppCard>
          ) : null}
          <AppSelect
            label="Drop-off date"
            value={selectedDate}
            placeholder="Choose a date"
            options={availableDates.map((date) => ({
              id: date,
              label: formatDateLabel(date),
              description: `${sourceSlots.filter((item) => item.adminId === adminId && item.date === date && item.availableSpots > 0).length} available time slots`,
            }))}
            onChange={selectDate}
          />
          {showPeriodFilter ? (
            <AppSelect
              label="Time of day"
              value={selectedPeriod}
              options={SLOT_PERIOD_OPTIONS.map((option) => ({
                id: option.id,
                label: option.label,
              }))}
              onChange={(id) => setSelectedPeriod(id as SlotPeriod)}
            />
          ) : null}
          <SlotPicker
            slots={visibleSlots}
            selectedSlotId={selectedSlotId}
            onSelect={(slot) => {
              setSelectedSlotId(slot.id);
              setSelectedPeriod(getSlotPeriod(slot));
              setSlotError(null);
            }}
          />
          {selectedSlot ? null : (
            <AppCard variant="highlighted" padding="sm">
              <HeroText className="text-sm leading-6 text-neutral-700">
                {slotError ?? 'No drop-off slots are available on this date. Pick another date to continue.'}
              </HeroText>
            </AppCard>
          )}
          <AppCard variant="subtle" padding="sm">
            <View className="flex-row items-center gap-3">
              <CalendarClock size={18} color="#2F64B6" />
              <HeroText className="flex-1 text-sm leading-5 text-neutral-600">
                {slotSupportCopy}
              </HeroText>
            </View>
          </AppCard>
          <HeroText className="text-sm font-semibold tracking-tight text-neutral-700">
            {selectedSlot
              ? `Selected: ${selectedDateLabel} · ${selectedTimeLabel}`
              : 'Select a time slot to continue'}
          </HeroText>
        </View>
        </AppSection>
      ) : null}

      {currentStep === 3 ? (
        <AppSection eyebrow="Photo" title="Optional photo" variant="compact">
        <AppCard variant="elevated" padding="md">
          <HeroText className="text-sm leading-5 text-neutral-600">
            Add a racket photo for admin review.
          </HeroText>
          {bookingPhoto ? (
            <Image
              source={{ uri: bookingPhoto.uri }}
              className="mt-3 h-32 w-full rounded-[20px] bg-neutral-100"
              resizeMode="cover"
              accessibilityLabel="Selected racket photo"
            />
          ) : null}
          <View className="mt-3 flex-row gap-3">
            <AppButton
              label={bookingPhoto ? 'Change photo' : 'Upload photo'}
              variant="outline"
              className="flex-1"
              onPress={pickBookingPhoto}
              leadingIcon={<Upload size={16} color="#4B5563" />}
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
      ) : null}

    </AppScreen>
  );
}
