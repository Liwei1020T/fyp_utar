import React, { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft, CreditCard, Landmark, Smartphone, Wallet } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { PaymentMethodCard } from '../../../components/payment/PaymentMethodCard';
import {
  useAppStore,
  useBookings,
  useCurrentUser,
  useStrings,
  useWallets,
} from '../../../store/appStore';
import type { PaymentMethod, PaymentStatus } from '../../../types/domain';
import { getStringById } from '../../../services/mockAppService';
import { formatCurrency } from '../../../lib/formatters';
import { getInventoryPriceLabel } from '../../../lib/inventory';

const paymentOptions: Array<{
  method: PaymentMethod;
  title: string;
  description: string;
  badge: string;
  icon: React.ReactNode;
}> = [
  {
    method: 'card',
    title: 'Card',
    description: 'Mock card sheet for a Stripe-ready future flow.',
    badge: 'Fast',
    icon: <CreditCard size={20} color="#2F64B6" />,
  },
  {
    method: 'online_banking',
    title: 'Online banking',
    description: 'Prototype FPX-style redirect experience for full payment.',
    badge: 'Recommended',
    icon: <Landmark size={20} color="#22766D" />,
  },
  {
    method: 'e_wallet',
    title: 'E-wallet',
    description: 'Mobile payment feel for a believable demo-ready checkout.',
    badge: 'Mobile',
    icon: <Smartphone size={20} color="#6550B8" />,
  },
  {
    method: 'wallet_balance',
    title: 'Wallet balance',
    description: 'Use stored balance now while keeping future top-up support ready.',
    badge: 'Stored',
    icon: <Wallet size={20} color="#C98A2E" />,
  },
];

export default function PaymentScreen() {
  const params = useLocalSearchParams<{ bookingId?: string }>();
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const strings = useStrings();
  const wallets = useWallets();
  const bookingDraft = useAppStore((state) => state.bookingDraft);
  const submitBookingPayment = useAppStore((state) => state.submitBookingPayment);
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('online_banking');
  const [isProcessing, setIsProcessing] = useState(false);

  const booking =
    params.bookingId && params.bookingId !== 'draft'
      ? bookings.find((item) => item.id === params.bookingId)
      : null;
  const draftString = bookingDraft
    ? strings.find((item) => item.id === bookingDraft.stringId) ??
      getStringById(bookingDraft.stringId)
    : undefined;
  const existingString = booking
    ? strings.find((item) => item.id === booking.stringId) ??
      getStringById(booking.stringId)
    : undefined;
  const activeString = booking ? existingString : draftString;
  const title = activeString
    ? `${activeString.brand} ${activeString.model}`
    : 'String setup pending';
  const wallet = wallets.find((item) => item.userId === user?.id);
  const stringPriceMeta = activeString
    ? getInventoryPriceLabel(activeString)
    : {
        label: 'Price pending',
        hasPrice: false,
      };
  const isQuotePendingBooking = Boolean(
    booking && booking.paymentStatus === 'unpaid' && booking.totalAmount <= 0,
  );
  const fallbackStringFee =
    activeString?.inventory.price ??
    (activeString && activeString.price > 0 ? activeString.price : null);
  const stringFee = isQuotePendingBooking
    ? null
    : booking?.stringFee ?? (stringPriceMeta.hasPrice ? fallbackStringFee ?? 0 : null);
  const serviceFee = booking?.serviceFee ?? 0;
  const totalAmount = isQuotePendingBooking
    ? null
    : booking?.totalAmount ?? (stringFee != null ? stringFee + serviceFee : null);
  const canCheckout = totalAmount != null && totalAmount > 0;
  const stringFeeLabel =
    stringFee != null
      ? formatCurrency(stringFee)
      : isQuotePendingBooking
        ? 'Quote at shop'
        : stringPriceMeta.label;

  const handlePayment = async (status: PaymentStatus) => {
    if (!canCheckout) {
      return;
    }

    setIsProcessing(true);
    await new Promise((resolve) => setTimeout(resolve, 650));

    const result = submitBookingPayment(
      selectedMethod,
      status,
      booking ? booking.id : undefined
    );

    if (!result.bookingId) {
      setIsProcessing(false);
      return;
    }

    const resultStatus = status === 'paid' ? 'success' : status;
    router.replace(`/player/payments/${result.bookingId}/result?status=${resultStatus}`);
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Payment"
      subtitle="Frontend-only for FYP 1, but structured so future real payment integration can replace it cleanly."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
          Payment summary
        </HeroText>
        <HeroText className="mt-3 text-[28px] font-bold tracking-tight text-white">
          {title}
        </HeroText>
        <View className="mt-4 flex-row items-center justify-between">
          <HeroText className="text-sm text-primary-100">String fee</HeroText>
          <HeroText className="text-lg font-bold text-white">
            {stringFeeLabel}
          </HeroText>
        </View>
        <View className="mt-2 flex-row items-center justify-between">
          <HeroText className="text-sm text-primary-100">Service fee</HeroText>
          <HeroText className="text-lg font-bold text-white">{formatCurrency(serviceFee)}</HeroText>
        </View>
        <View className="mt-2 flex-row items-center justify-between">
          <HeroText className="text-sm text-primary-100">Wallet balance</HeroText>
          <HeroText className="text-lg font-bold text-white">
            {formatCurrency(wallet?.availableBalance ?? 0)}
          </HeroText>
        </View>
        <View className="mt-5 border-t border-white/10 pt-4 flex-row items-center justify-between">
          <HeroText className="text-sm text-primary-100">Total amount</HeroText>
          <HeroText className="text-2xl font-bold text-white">
            {totalAmount != null ? formatCurrency(totalAmount) : 'Quote at shop'}
          </HeroText>
        </View>
      </AppCard>

      <AppSection eyebrow="Methods" title="Choose a mock payment method">
        <View className="gap-3">
          {paymentOptions.map((item) => (
            <PaymentMethodCard
              key={item.method}
              title={item.title}
              description={item.description}
              badge={item.badge}
              icon={item.icon}
              selected={selectedMethod === item.method}
              onPress={() => setSelectedMethod(item.method)}
            />
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Rule" title="Checkout behavior">
        <AppCard variant="subtle" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            {canCheckout
              ? 'This FYP 1 prototype confirms bookings with one full payment. Cancellation and reschedule options stay available only before payment succeeds.'
              : 'Final quote is still pending from the service desk. Payment unlocks once a shop-confirmed amount is available.'}
          </HeroText>
        </AppCard>
      </AppSection>

      <View className="mb-12 mt-8 gap-3">
        <AppButton
          label="Pay full amount now"
          size="lg"
          isLoading={isProcessing}
          isDisabled={!canCheckout}
          onPress={() => handlePayment('paid')}
        />
        <View className="flex-row gap-3">
          <AppButton
            label="Simulate failed"
            variant="outline"
            size="lg"
            className="flex-1"
            isDisabled={!canCheckout}
            onPress={() => handlePayment('failed')}
          />
          <AppButton
            label="Cancel"
            variant="ghost"
            size="lg"
            className="flex-1"
            isDisabled={!canCheckout}
            onPress={() => handlePayment('cancelled')}
          />
        </View>
      </View>
    </AppScreen>
  );
}
