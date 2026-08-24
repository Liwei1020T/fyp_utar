import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppSelect } from '../../../components/ui/AppSelect';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { QrTransferPanel } from '../../../components/payment/QrTransferPanel';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
  usePayments,
  useStrings,
  useWallets,
} from '../../../store/appStore';
import type { BackendBookingPaymentQuote } from '../../../types/backend';
import type { BackendUploadFile } from '../../../services/backendApi';
import { formatCurrency } from '../../../lib/formatters';
import { showAlert } from '../../../lib/alerts';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  mapBackendPaymentToPayment,
  mapBackendWallet,
} from '../../../services/backendMappers';

const paymentOptions: {
  method: 'qr_transfer' | 'cash' | 'wallet_balance';
  title: string;
  description: string;
  badge: string;
}[] = [
  {
    method: 'qr_transfer',
    title: 'QR transfer',
    description: 'Scan the shop QR and submit your transfer screenshot for review.',
    badge: 'Recommended',
  },
  {
    method: 'cash',
    title: 'Cash',
    description: 'Pay at the shop and wait for the admin to confirm receipt.',
    badge: 'At shop',
  },
  {
    method: 'wallet_balance',
    title: 'Wallet balance',
    description: 'Pay immediately from your persisted StringSense balance.',
    badge: 'Stored',
  },
];

export default function PaymentScreen() {
  const params = useLocalSearchParams<{ bookingId?: string }>();
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const payments = usePayments();
  const strings = useStrings();
  const wallets = useWallets();
  const storeSettings = useAppStore((state) => state.storeSettings);
  const upsertLivePayment = useAppStore((state) => state.upsertLivePayment);
  const setLiveWallet = useAppStore((state) => state.setLiveWallet);
  const [selectedMethod, setSelectedMethod] = useState<
    'qr_transfer' | 'cash' | 'wallet_balance'
  >('qr_transfer');
  const [proof, setProof] = useState<BackendUploadFile | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [quote, setQuote] = useState<BackendBookingPaymentQuote | null>(null);
  const [quoteError, setQuoteError] = useState<string | null>(null);
  const [quoteRefreshKey, setQuoteRefreshKey] = useState(0);

  const booking = bookings.find((item) => item.id === params.bookingId);
  const activeString = booking
    ? strings.find((item) => item.id === booking.stringId)
    : undefined;
  useEffect(() => {
    if (!token || !booking) {
      setQuote(null);
      setQuoteError(null);
      return;
    }

    let active = true;
    setQuote(null);
    setQuoteError(null);
    void backendApi
      .fetchBookingPaymentQuote(token, booking.id)
      .then((response) => {
        if (active) {
          setQuote(response);
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setQuoteError(
            error instanceof BackendApiError
              ? error.message
              : 'Unable to load the current server quote.',
          );
        }
      });

    return () => {
      active = false;
    };
  }, [booking, quoteRefreshKey, token]);

  const activePayment =
    quote?.active_payment ??
    payments.find(
      (item) =>
        item.bookingId === booking?.id &&
        (item.status === 'pending' || item.status === 'paid'),
    );
  const title = activeString
    ? `${activeString.brand} ${activeString.model}`
    : 'String setup pending';
  const wallet = wallets.find((item) => item.userId === user?.id);
  const isQuotePendingBooking = Boolean(
    booking && booking.paymentStatus === 'unpaid' && booking.totalAmount <= 0,
  );
  const stringFee = quote?.string_fee ?? null;
  const serviceFee = quote?.service_fee ?? 0;
  const totalAmount = quote?.total_amount ?? null;
  const hasSufficientWallet =
    selectedMethod !== 'wallet_balance' ||
    (quote != null &&
      totalAmount != null &&
      quote.wallet_balance >= totalAmount);
  const hasQrTransferEvidence =
    selectedMethod !== 'qr_transfer' ||
    Boolean(storeSettings?.paymentQrUrl && proof);
  const canCheckout =
    Boolean(token && booking) &&
    totalAmount != null &&
    totalAmount > 0 &&
    hasSufficientWallet &&
    hasQrTransferEvidence &&
    !activePayment;
  const stringFeeLabel =
    stringFee != null
      ? formatCurrency(stringFee)
      : isQuotePendingBooking
        ? 'Quote at shop'
        : 'Loading server quote';
  let checkoutRule = 'Final quote is still pending from the service desk.';
  if (!token) {
    checkoutRule = 'Sign in through the live backend to submit or verify a payment.';
  } else if (quoteError) {
    checkoutRule = quoteError;
  } else if (!quote) {
    checkoutRule = 'Loading the current price and wallet balance from the server.';
  } else if (!hasSufficientWallet) {
    checkoutRule =
      'Your persisted wallet balance is lower than this server quote. Top up or choose another method.';
  } else if (activePayment) {
    checkoutRule = `This booking already has a ${activePayment.status} payment record.`;
  } else if (selectedMethod === 'qr_transfer' && !storeSettings?.paymentQrUrl) {
    checkoutRule = 'The shop has not configured a payment QR yet.';
  } else if (selectedMethod === 'qr_transfer' && !proof) {
    checkoutRule = 'Upload the payment screenshot before submitting for review.';
  } else if (canCheckout) {
    checkoutRule =
      selectedMethod === 'wallet_balance'
        ? 'Wallet payment completes only when the server confirms sufficient persisted balance.'
        : selectedMethod === 'cash'
          ? 'Cash payment stays pending until the shop confirms payment at the counter.'
          : 'QR transfers remain pending until the shop verifies the payment screenshot.';
  }

  if (!booking) {
    return (
      <AppScreen
        headerVariant="flow"
        title="Payment unavailable"
        subtitle="The linked booking could not be found."
        showBackButton
        onBackPress={() => router.replace('/player/bookings')}
      >
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-base font-semibold text-neutral-900">
            Open an existing booking to start payment.
          </HeroText>
          <AppButton
            label="Back to bookings"
            className="mt-6"
            onPress={() => router.replace('/player/bookings')}
          />
        </AppCard>
      </AppScreen>
    );
  }

  const handlePayment = async () => {
    if (!canCheckout || !token || !booking) {
      return;
    }

    setIsProcessing(true);
    try {
      const response = await backendApi.createBookingPayment(
        token,
        booking.id,
        selectedMethod,
        quote?.total_amount,
        selectedMethod === 'qr_transfer' ? proof : null,
      );
      const payment = mapBackendPaymentToPayment(response);
      upsertLivePayment(payment);
      if (selectedMethod === 'wallet_balance') {
        const refreshedWallet = mapBackendWallet(await backendApi.fetchWallet(token));
        setLiveWallet(refreshedWallet.balance, refreshedWallet.transactions);
      }
      router.replace(`/player/payments/${booking.id}/result`);
    } catch (paymentError) {
      const message = paymentError instanceof BackendApiError
        ? paymentError.message
        : 'Failed to create payment.';
      if (
        paymentError instanceof BackendApiError &&
        paymentError.statusCode === 409
      ) {
        setQuoteRefreshKey((value) => value + 1);
      }
      showAlert('Payment unavailable', message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Payment"
      subtitle="Pay by QR transfer, cash, or wallet balance."
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
            {formatCurrency(quote?.wallet_balance ?? wallet?.availableBalance ?? 0)}
          </HeroText>
        </View>
        <View className="mt-5 border-t border-white/10 pt-4 flex-row items-center justify-between">
          <HeroText className="text-sm text-primary-100">Total amount</HeroText>
          <HeroText className="text-2xl font-bold text-white">
            {totalAmount != null ? formatCurrency(totalAmount) : 'Quote at shop'}
          </HeroText>
        </View>
      </AppCard>

      <AppSection eyebrow="Methods" title="Choose a payment method">
        <AppSelect
          label="Payment method"
          value={selectedMethod}
          options={paymentOptions.map((item) => ({
            id: item.method,
            label: item.title,
            description: `${item.badge} · ${item.description}`,
          }))}
          onChange={(value) => setSelectedMethod(value as typeof selectedMethod)}
        />
        {selectedMethod === 'qr_transfer' ? (
          <View className="mt-4">
            <QrTransferPanel
              qrUrl={storeSettings?.paymentQrUrl}
              proof={proof}
              onProofChange={setProof}
            />
          </View>
        ) : null}
      </AppSection>

      <AppSection eyebrow="Rule" title="Checkout behavior">
        <AppCard variant="subtle" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            {checkoutRule}
          </HeroText>
        </AppCard>
      </AppSection>

      <View className="mb-12 mt-8 gap-3">
        {quoteError ? (
          <AppButton
            label="Retry server quote"
            variant="outline"
            size="lg"
            onPress={() => setQuoteRefreshKey((value) => value + 1)}
          />
        ) : null}
        <AppButton
          label={
            selectedMethod === 'wallet_balance'
              ? 'Pay from wallet'
              : selectedMethod === 'cash'
                ? 'Submit cash payment request'
                : 'Submit payment for verification'
          }
          size="lg"
          isLoading={isProcessing}
          isDisabled={!canCheckout}
          onPress={() => void handlePayment()}
        />
        <AppButton
          label="Back to booking"
          variant="outline"
          size="lg"
          onPress={() => router.back()}
        />
      </View>
    </AppScreen>
  );
}
