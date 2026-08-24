import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppInput } from '../../../components/ui/AppInput';
import { AppSelect } from '../../../components/ui/AppSelect';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { QrTransferPanel } from '../../../components/payment/QrTransferPanel';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import type { BackendUploadFile } from '../../../services/backendApi';
import {
  mapBackendPaymentToPayment,
  mapBackendWallet,
} from '../../../services/backendMappers';

const amounts = ['20', '50', '80', '100'];
export default function WalletTopUpScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const upsertLivePayment = useAppStore((state) => state.upsertLivePayment);
  const setLiveWallet = useAppStore((state) => state.setLiveWallet);
  const storeSettings = useAppStore((state) => state.storeSettings);
  const [amount, setAmount] = useState('50');
  const [method, setMethod] = useState<'qr_transfer' | 'cash'>('qr_transfer');
  const [proof, setProof] = useState<BackendUploadFile | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user || user.role !== 'player') {
    return null;
  }

  const submitTopUp = async () => {
    const numericAmount = Number(amount);
    if (!token || numericAmount < 1 || numericAmount > 5000) {
      setError('Enter an amount between RM 1 and RM 5,000.');
      return;
    }
    if (method === 'qr_transfer' && !storeSettings?.paymentQrUrl) {
      setError('The shop has not configured a payment QR yet.');
      return;
    }
    if (method === 'qr_transfer' && !proof) {
      setError('Choose the payment screenshot before submitting.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const response = await backendApi.requestWalletTopUp(token, {
        amount: numericAmount,
        method,
        proof: method === 'qr_transfer' ? proof : null,
      });
      const payment = mapBackendPaymentToPayment(response);
      upsertLivePayment(payment);
      const wallet = mapBackendWallet(await backendApi.fetchWallet(token));
      setLiveWallet(wallet.balance, wallet.transactions);
      router.replace('/player/wallet');
    } catch (requestError) {
      setError(
        requestError instanceof BackendApiError
          ? requestError.message
          : 'Failed to request wallet top-up.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Top up wallet"
      subtitle="Top up by QR transfer or cash at the shop."
      showBackButton
      onBackPress={() => router.back()}
      footer={
        <View className="gap-2 border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          <AppButton
            label="Submit for review"
            isLoading={isSubmitting}
            isDisabled={
              method === 'qr_transfer' &&
              (!storeSettings?.paymentQrUrl || !proof)
            }
            onPress={() => void submitTopUp()}
          />
          <AppButton label="Back to wallet" variant="outline" onPress={() => router.back()} />
        </View>
      }
    >
      <AppCard variant="highlighted" padding="lg">
        <HeroText className="text-sm leading-6 text-neutral-600">
          {method === 'qr_transfer'
            ? 'The requested amount stays pending until the shop verifies the QR transfer. Only then is wallet credit added.'
            : 'Pay cash at the shop. The requested amount stays pending until the admin confirms receipt and credits your wallet.'}
        </HeroText>
      </AppCard>

      <AppSelect
        label="Payment method"
        value={method}
        options={[
          {
            id: 'qr_transfer',
            label: 'QR transfer',
            description: 'Upload payment proof for admin review.',
          },
          {
            id: 'cash',
            label: 'Cash at shop',
            description: 'Pay at the counter and wait for admin confirmation.',
          },
        ]}
        onChange={(value) => setMethod(value as typeof method)}
        className="mt-6"
      />

      <AppSelect
        label="Quick amount"
        value={amounts.includes(amount) ? amount : null}
        placeholder="Choose a quick amount"
        options={amounts.map((value) => ({ id: value, label: `RM ${value}` }))}
        onChange={setAmount}
        className="mt-4"
      />

      <AppInput
        label="Custom amount"
        value={amount}
        onChangeText={setAmount}
        keyboardType="numeric"
      />

      {method === 'qr_transfer' ? (
        <View className="mt-6">
          <QrTransferPanel
            qrUrl={storeSettings?.paymentQrUrl}
            proof={proof}
            onProofChange={setProof}
          />
        </View>
      ) : null}

      {error ? (
        <HeroText className="mt-6 text-sm font-medium text-red-600">
          {error}
        </HeroText>
      ) : null}
    </AppScreen>
  );
}
