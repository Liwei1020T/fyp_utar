import React from 'react';
import { Image, View } from 'react-native';
import { useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { HeroText } from '../../../components/ui/heroui';
import { AppDetailList } from '../../../components/shared/AppDetailList';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useRackets,
  useStrings,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendBookingToBooking } from '../../../services/backendMappers';
import { formatCurrency } from '../../../lib/formatters';
import { getInventoryPriceLabel } from '../../../lib/inventory';

function normalizeStoreText(value: unknown) {
  return typeof value === 'string' ? value.trim() : '';
}

export default function BookingSummaryScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookingDraft = useAppStore((state) => state.bookingDraft);
  const adminSettings = useAppStore((state) => state.adminSettings);
  const clearBookingDraft = useAppStore((state) => state.clearBookingDraft);
  const prependLiveBooking = useAppStore((state) => state.prependLiveBooking);
  const token = useBackendAccessToken();
  const strings = useStrings();
  const rackets = useRackets();
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  if (!bookingDraft || !user || user.role !== 'player') {
    return (
      <AppScreen title="Booking summary">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            No booking draft found.
          </HeroText>
          <AppButton
            label="Start new booking"
            className="mt-6"
            onPress={() => router.replace('/player/bookings/new')}
          />
        </AppCard>
      </AppScreen>
    );
  }

  const stringItem = strings.find(
    (item) => item.id === bookingDraft.stringId,
  );
  const selectedRacket = bookingDraft.racketId
    ? rackets.find((item) => item.id === bookingDraft.racketId)
    : undefined;
  const currentStoreSettings = adminSettings.find(
    (item) => item.adminId === 'main',
  );
  const vendorLabel =
    normalizeStoreText(currentStoreSettings?.storeName) ||
    'Assigned shop';
  const stringLabel = stringItem
    ? `${stringItem.brand} ${stringItem.model}`
    : 'Selected string';
  const stringPrice =
    stringItem?.inventory.price ?? (stringItem && stringItem.price > 0 ? stringItem.price : null);
  const stringPriceMeta = stringItem
    ? getInventoryPriceLabel(stringItem)
    : {
        label: 'Price pending',
        hasPrice: false,
      };
  const stringFee = stringPriceMeta.hasPrice ? stringPrice ?? 0 : null;
  const serviceFee = 0;
  const totalPayable = stringFee != null ? stringFee + serviceFee : null;

  const handleProceed = async () => {
    if (!token) {
      setSubmitError('Your player session expired. Sign in again to confirm this booking.');
      return;
    }

    setSubmitError(null);
    setIsSubmitting(true);
    try {
      let photoUploadFailed = false;
      let booking = await backendApi.createBooking(token, {
        string_id: bookingDraft.stringId,
        racket_id: bookingDraft.racketId ?? undefined,
        racket_brand: bookingDraft.racketBrand,
        racket_model: bookingDraft.racketModel,
        requested_tension: bookingDraft.requestedTension,
        slot_id: bookingDraft.slotId,
        notes: bookingDraft.notes || undefined,
      });

      if (bookingDraft.photoUri) {
        try {
          booking = await backendApi.addBookingUpdate(token, booking.id, {
            photo: {
              uri: bookingDraft.photoUri,
              name: bookingDraft.photoName ?? `booking-photo-${booking.id}.jpg`,
              type: bookingDraft.photoContentType ?? 'image/jpeg',
            },
          });
        } catch {
          photoUploadFailed = true;
        }
      }

      const priceByStringId = new Map<string, number>();
      if (stringFee != null) {
        priceByStringId.set(bookingDraft.stringId, stringFee);
      }

      const mappedBooking = mapBackendBookingToBooking(booking, priceByStringId);
      if (stringFee == null) {
        mappedBooking.paymentStatus = 'unpaid';
        mappedBooking.stringFee = 0;
        mappedBooking.totalAmount = 0;
        mappedBooking.amountPaid = 0;
        mappedBooking.paymentRuleNote =
          'Final string quote is pending. Payment unlocks after shop confirms the amount.';
      }

      prependLiveBooking(mappedBooking);
      clearBookingDraft();
      router.replace(
        `/player/bookings/${booking.id}${photoUploadFailed ? '?photoUpload=failed' : ''}`,
      );
    } catch (error) {
      setSubmitError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to create booking.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Booking summary"
      subtitle="Review your string, drop-off timing, and booking photo before confirming."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection eyebrow="Summary" title="Service request">
        <AppCard variant="highlighted" padding="lg">
          <View className="gap-3">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
              {vendorLabel}
            </HeroText>
            <HeroText className="text-[24px] font-bold tracking-tight text-neutral-950">
              {stringLabel}
            </HeroText>
            <HeroText className="text-sm leading-6 text-neutral-500">
              {bookingDraft.racketBrand} {bookingDraft.racketModel} at {bookingDraft.requestedTension} lbs
            </HeroText>
            {selectedRacket ? (
              <HeroText className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-700">
                Saved passport: {selectedRacket.nickname}
              </HeroText>
            ) : null}
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Details" title="Drop-off and setup">
        <AppDetailList
          items={[
            {
              label: 'String',
              value: stringLabel,
            },
            {
              label: 'Racket',
              value: selectedRacket
                ? `${selectedRacket.nickname} · ${bookingDraft.racketBrand} ${bookingDraft.racketModel}`
                : `${bookingDraft.racketBrand} ${bookingDraft.racketModel}`,
            },
            {
              label: 'Requested tension',
              value: `${bookingDraft.requestedTension} lbs`,
            },
            {
              label: 'Drop-off date and time',
              value: `${bookingDraft.dropOffDate} at ${bookingDraft.dropOffTime}`,
            },
            {
              label: 'Notes',
              value: bookingDraft.notes || 'No extra notes provided.',
            },
          ]}
        />
      </AppSection>

      <AppSection eyebrow="Pricing" title="Estimated service cost">
        <AppCard variant="dark" padding="lg">
          <View className="flex-row items-center justify-between">
            <HeroText className="text-sm text-primary-100">String fee</HeroText>
            <HeroText className="text-lg font-bold text-white">
              {stringFee != null ? formatCurrency(stringFee) : stringPriceMeta.label}
            </HeroText>
          </View>
          <View className="mt-3 flex-row items-center justify-between">
            <HeroText className="text-sm text-primary-100">Service fee</HeroText>
            <HeroText className="text-lg font-bold text-white">
              {formatCurrency(serviceFee)}
            </HeroText>
          </View>
          <View className="mt-5 border-t border-white/10 pt-4 flex-row items-center justify-between">
            <HeroText className="text-sm text-primary-100">Estimated total</HeroText>
            <HeroText className="text-2xl font-bold text-white">
              {totalPayable != null ? formatCurrency(totalPayable) : 'Quote at shop'}
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      {bookingDraft.photoUri ? (
        <AppSection eyebrow="Photo" title="Attached racket photo">
          <AppCard variant="elevated" padding="md">
            <Image
              source={{ uri: bookingDraft.photoUri }}
              className="h-52 w-full rounded-[24px] bg-neutral-100"
              resizeMode="cover"
            />
            <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
              This photo will be uploaded to the backend after the booking is created.
            </HeroText>
          </AppCard>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Rule" title="Before you continue">
        <AppCard variant="subtle" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            {token
              ? stringFee != null
                ? 'The booking is saved to the live backend. Continue from its booking detail to submit payment.'
                : 'The booking is saved to the live backend. Payment unlocks after the shop confirms the final string quote.'
              : 'Sign in to confirm this booking with the shop.'}
          </HeroText>
        </AppCard>
      </AppSection>

      {submitError ? (
        <AppCard variant="subtle" className="mt-4 border border-red-100" padding="md">
          <HeroText className="text-sm font-medium text-red-600">
            {submitError}
          </HeroText>
        </AppCard>
      ) : null}

      <View className="mb-12 mt-8 gap-3">
        <AppButton
          label="Confirm booking"
          size="lg"
          onPress={handleProceed}
          isLoading={isSubmitting}
        />
        <AppButton
          label="Edit booking"
          variant="outline"
          size="lg"
          onPress={() =>
            router.push(
              `/player/bookings/new?stringId=${bookingDraft.stringId}${
                bookingDraft.racketId
                  ? `&racketId=${bookingDraft.racketId}`
                  : ''
              }`,
            )
          }
        />
      </View>
    </AppScreen>
  );
}
