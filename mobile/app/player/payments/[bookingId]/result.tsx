import React from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { AlertTriangle, CheckCircle2, ChevronLeft, CircleSlash } from 'lucide-react-native';
import { AppButton } from '../../../../components/ui/AppButton';
import { AppCard } from '../../../../components/ui/AppCard';
import { HeroText } from '../../../../components/ui/heroui';
import { AppScreen } from '../../../../components/shared/AppScreen';
import { formatCurrency } from '../../../../lib/formatters';
import { useBookings, usePayments } from '../../../../store/appStore';

export default function PaymentResultScreen() {
  const params = useLocalSearchParams<{ bookingId?: string; status?: string }>();
  const router = useRouter();
  const bookings = useBookings();
  const payments = usePayments();
  const booking = bookings.find((item) => item.id === params.bookingId);
  const payment = payments.find((item) => item.bookingId === params.bookingId);
  const status = params.status ?? 'success';

  const meta = status === 'success'
    ? {
        title: 'Payment confirmed',
        body: 'Your booking is now confirmed and ready for the selected drop-off window.',
        icon: <CheckCircle2 size={36} color="white" />,
        variant: 'dark' as const,
      }
    : status === 'failed'
      ? {
          title: 'Payment failed',
          body: 'The mock payment did not go through. You can retry using another method.',
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
      subtitle="Use this page in the demo to show success, failure, and cancellation states."
      showBackButton
      onBackPress={() => router.replace('/player/bookings')}
    >
      <AppCard variant={meta.variant} className="rounded-[32px]" padding="lg">
        <View className="items-center">
          <View className={`h-20 w-20 items-center justify-center rounded-full ${status === 'success' ? 'bg-white/10' : 'bg-white/70'}`}>
            {meta.icon}
          </View>
          <HeroText className={`mt-5 text-center text-[28px] font-bold tracking-tight ${status === 'success' ? 'text-white' : 'text-neutral-950'}`}>
            {meta.title}
          </HeroText>
          <HeroText className={`mt-2 text-center text-sm leading-6 ${status === 'success' ? 'text-primary-100' : 'text-neutral-500'}`}>
            {meta.body}
          </HeroText>
          {status === 'success' && booking ? (
            <View className="mt-5 w-full rounded-[22px] bg-white/10 px-4 py-4">
              <HeroText className="text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-100">
                Booking reference
              </HeroText>
              <HeroText className="mt-2 text-center text-sm leading-6 text-white">
                {booking.id} • {payment?.reference ?? 'Mock payment reference pending'}
              </HeroText>
              <HeroText className="mt-3 text-center text-sm leading-6 text-white">
                Paid amount {formatCurrency(payment?.amount ?? booking.totalAmount)}
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
        {status !== 'success' ? (
          <AppButton label="Try payment again" variant="ghost" size="lg" onPress={() => router.replace(`/player/payments/${params.bookingId}`)} />
        ) : null}
      </View>
    </AppScreen>
  );
}
