import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { AlertTriangle, CheckCircle2, CircleSlash } from 'lucide-react-native';
import { AppButton } from '../../../../components/ui/AppButton';
import { AppCard } from '../../../../components/ui/AppCard';
import { HeroText } from '../../../../components/ui/heroui';
import { AppScreen } from '../../../../components/shared/AppScreen';
import { formatBookingOrderCode, formatCurrency } from '../../../../lib/formatters';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  usePayments,
} from '../../../../store/appStore';
import { BackendApiError, backendApi } from '../../../../services/backendApi';
import { mapBackendPaymentToPayment } from '../../../../services/backendMappers';

export default function PaymentResultScreen() {
  const params = useLocalSearchParams<{ bookingId?: string }>();
  const router = useRouter();
  const bookings = useBookings();
  const payments = usePayments();
  const token = useBackendAccessToken();
  const setLivePayments = useAppStore((state) => state.setLivePayments);
  const [isRefreshing, setIsRefreshing] = useState(Boolean(token));
  const [loadError, setLoadError] = useState<string | null>(null);
  const booking = bookings.find((item) => item.id === params.bookingId);
  const payment = payments.find((item) => item.bookingId === params.bookingId);
  const status = payment?.status;
  const orderCode = booking
    ? booking.orderCode ?? formatBookingOrderCode(booking.id)
    : null;

  useEffect(() => {
    if (!token) {
      setIsRefreshing(false);
      return;
    }

    let cancelled = false;
    setIsRefreshing(true);
    setLoadError(null);
    backendApi
      .listPayments(token)
      .then((records) => {
        if (!cancelled) {
          setLivePayments(records.map(mapBackendPaymentToPayment));
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setLoadError(
            error instanceof BackendApiError
              ? error.message
              : 'Failed to refresh the payment record.',
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsRefreshing(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [setLivePayments, token]);

  if (!payment && isRefreshing) {
    return (
      <AppScreen
        headerVariant="flow"
        title="Payment result"
        subtitle="Checking the persisted payment ledger."
        showBackButton
        onBackPress={() => router.replace('/player/bookings')}
      >
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-base font-semibold text-neutral-900">
            Loading payment status...
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  if (!payment || !status) {
    return (
      <AppScreen
        headerVariant="flow"
        title="Payment record unavailable"
        subtitle="No persisted payment matches this booking."
        showBackButton
        onBackPress={() => router.replace('/player/bookings')}
      >
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-base font-semibold text-neutral-900">
            We could not verify this payment result.
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-600">
            {loadError ?? 'Open the booking and retry from its payment action.'}
          </HeroText>
          <AppButton
            label={booking ? 'Back to booking' : 'Back to bookings'}
            className="mt-6"
            onPress={() =>
              router.replace(
                booking ? `/player/bookings/${booking.id}` : '/player/bookings',
              )
            }
          />
        </AppCard>
      </AppScreen>
    );
  }

  const meta = status === 'paid'
      ? {
        title: 'Payment confirmed',
        body: 'The payment is confirmed in the ledger. Follow the booking status for the approved drop-off step.',
        icon: <CheckCircle2 size={36} color="white" />,
        variant: 'dark' as const,
      }
    : status === 'pending'
      ? {
          title: 'Verification pending',
          body: payment.method === 'cash'
            ? 'The cash payment request is saved. Pay at the shop and wait for the admin to confirm receipt.'
            : 'The payment record and screenshot are saved. The shop must verify the QR transfer before it is marked paid.',
          icon: <AlertTriangle size={36} color="#B45309" />,
          variant: 'highlighted' as const,
        }
    : status === 'failed'
      ? {
          title: 'Payment failed',
          body: 'The shop could not confirm this payment. Return to the booking and choose a payment method again.',
          icon: <AlertTriangle size={36} color="#B45309" />,
          variant: 'highlighted' as const,
        }
      : {
          title: 'Payment cancelled',
          body: 'The flow was cancelled before full payment was confirmed.',
          icon: <CircleSlash size={36} color="#64748B" />,
          variant: 'subtle' as const,
        };

  return (
    <AppScreen
      headerVariant="flow"
      title="Payment result"
      subtitle="Status loaded from the persisted payment ledger."
      showBackButton
      onBackPress={() => router.replace('/player/bookings')}
    >
      <AppCard variant={meta.variant} className="rounded-[32px]" padding="lg">
        <View className="items-center">
          <View className={`h-20 w-20 items-center justify-center rounded-full ${status === 'paid' ? 'bg-white/10' : 'bg-white/70'}`}>
            {meta.icon}
          </View>
          <HeroText className={`mt-5 text-center text-[28px] font-bold tracking-tight ${status === 'paid' ? 'text-white' : 'text-neutral-950'}`}>
            {meta.title}
          </HeroText>
          <HeroText className={`mt-2 text-center text-sm leading-6 ${status === 'paid' ? 'text-primary-100' : 'text-neutral-500'}`}>
            {meta.body}
          </HeroText>
          {status === 'paid' && booking ? (
            <View className="mt-5 w-full rounded-[22px] bg-white/10 px-4 py-4">
              <HeroText className="text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-100">
                Booking reference
              </HeroText>
              <HeroText className="mt-2 text-center text-sm leading-6 text-white">
                {orderCode} • {payment?.reference}
              </HeroText>
              <HeroText className="mt-3 text-center text-sm leading-6 text-white">
                Paid amount {formatCurrency(payment.amount)}
              </HeroText>
              <HeroText className="mt-3 text-center text-sm leading-6 text-white">
                Drop off your racket on {booking.dropOffDate} at {booking.dropOffTime}. Your next step is to show the booking token during check-in.
              </HeroText>
            </View>
          ) : null}
        </View>
      </AppCard>

      <View className="mb-12 mt-8 gap-3">
        {booking ? (
          <>
            <AppButton label="Open booking detail" size="lg" onPress={() => router.replace(`/player/bookings/${booking.id}`)} />
            <AppButton label="Open tracking" variant="outline" size="lg" onPress={() => router.replace(`/player/bookings/${booking.id}/tracking`)} />
          </>
        ) : null}
        {status === 'failed' || status === 'cancelled' ? (
          <AppButton label="Try payment again" variant="ghost" size="lg" onPress={() => router.replace(`/player/payments/${params.bookingId}`)} />
        ) : null}
      </View>
    </AppScreen>
  );
}
