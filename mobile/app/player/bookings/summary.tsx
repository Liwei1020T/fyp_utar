import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppDetailList } from '../../../components/shared/AppDetailList';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useWallets,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendBookingToBooking } from '../../../services/backendMappers';
import { getAdminById, getStringById } from '../../../services/mockAppService';
import { formatCurrency } from '../../../lib/formatters';

export default function BookingSummaryScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookingDraft = useAppStore((state) => state.bookingDraft);
  const clearBookingDraft = useAppStore((state) => state.clearBookingDraft);
  const prependLiveBooking = useAppStore((state) => state.prependLiveBooking);
  const wallets = useWallets();
  const token = useBackendAccessToken();
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

  const stringItem = getStringById(bookingDraft.stringId);
  const admin = getAdminById(bookingDraft.adminId);
  const wallet = wallets.find((item) => item.userId === user.id);
  const stringFee = stringItem?.price ?? 36;
  const serviceFee = 18;
  const totalPayable = stringFee + serviceFee;

  const handleProceed = async () => {
    if (!token) {
      router.push('/player/payments/draft');
      return;
    }

    setSubmitError(null);
    setIsSubmitting(true);
    try {
      const booking = await backendApi.createBooking(token, {
        string_id: bookingDraft.stringId,
        racket_brand: bookingDraft.racketBrand,
        racket_model: bookingDraft.racketModel,
        requested_tension: bookingDraft.requestedTension,
        drop_off_datetime: `${bookingDraft.dropOffDate}T${bookingDraft.dropOffTime}:00`,
        notes: bookingDraft.notes || undefined,
      });

      prependLiveBooking(
        mapBackendBookingToBooking(
          booking,
          new Map([[bookingDraft.stringId, stringFee]]),
        ),
      );
      clearBookingDraft();
      router.replace(`/player/bookings/${booking.id}`);
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
      title="Booking summary"
      subtitle="Review your string, drop-off timing, and full payment breakdown before checkout."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      <AppSection eyebrow="Summary" title="Service request">
        <AppCard variant="highlighted" padding="lg">
          <View className="gap-3">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
              {admin?.businessName}
            </HeroText>
            <HeroText className="text-[24px] font-bold tracking-tight text-neutral-950">
              {stringItem?.brand} {stringItem?.model}
            </HeroText>
            <HeroText className="text-sm leading-6 text-neutral-500">
              {bookingDraft.racketBrand} {bookingDraft.racketModel} at {bookingDraft.requestedTension} lbs
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Details" title="Drop-off and setup">
        <AppDetailList
          items={[
            {
              label: 'String',
              value: `${stringItem?.brand ?? ''} ${stringItem?.model ?? ''}`.trim(),
            },
            {
              label: 'Racket',
              value: `${bookingDraft.racketBrand} ${bookingDraft.racketModel}`,
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

      <AppSection eyebrow="Pricing" title="Payable now">
        <AppCard variant="dark" padding="lg">
          <View className="flex-row items-center justify-between">
            <HeroText className="text-sm text-primary-100">String fee</HeroText>
            <HeroText className="text-lg font-bold text-white">
              {formatCurrency(stringFee)}
            </HeroText>
          </View>
          <View className="mt-3 flex-row items-center justify-between">
            <HeroText className="text-sm text-primary-100">Service fee</HeroText>
            <HeroText className="text-lg font-bold text-white">
              {formatCurrency(serviceFee)}
            </HeroText>
          </View>
          <View className="mt-3 flex-row items-center justify-between">
            <HeroText className="text-sm text-primary-100">Wallet balance</HeroText>
            <HeroText className="text-lg font-bold text-white">
              {formatCurrency(wallet?.availableBalance ?? 0)}
            </HeroText>
          </View>
          <View className="mt-5 border-t border-white/10 pt-4 flex-row items-center justify-between">
            <HeroText className="text-sm text-primary-100">Total payable now</HeroText>
            <HeroText className="text-2xl font-bold text-white">
              {formatCurrency(totalPayable)}
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Rule" title="Before you continue">
        <AppCard variant="subtle" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            {token
              ? 'This MVP flow confirms the booking directly with the live backend. Payment stays mocked for a later phase.'
              : 'Full payment confirms the booking. You can still cancel or reschedule before payment is completed, but those actions are hidden after payment succeeds.'}
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
          label={token ? 'Confirm booking' : 'Proceed to payment'}
          size="lg"
          onPress={handleProceed}
          isLoading={isSubmitting}
        />
        <AppButton
          label="Edit booking"
          variant="outline"
          size="lg"
          onPress={() => router.push(`/player/bookings/new?stringId=${bookingDraft.stringId}`)}
        />
      </View>
    </AppScreen>
  );
}
