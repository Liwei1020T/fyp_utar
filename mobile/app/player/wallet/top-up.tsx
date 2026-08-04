import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  mapBackendPaymentToPayment,
  mapBackendWallet,
} from '../../../services/backendMappers';

const amounts = ['20', '50', '80', '100'];
const topUpMethods = [
  { value: 'online_banking', label: 'Online banking' },
  { value: 'card', label: 'Card' },
  { value: 'e_wallet', label: 'E-wallet' },
] as const;

export default function WalletTopUpScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const upsertLivePayment = useAppStore((state) => state.upsertLivePayment);
  const setLiveWallet = useAppStore((state) => state.setLiveWallet);
  const [amount, setAmount] = useState('50');
  const [method, setMethod] =
    useState<(typeof topUpMethods)[number]['value']>('online_banking');
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

    setIsSubmitting(true);
    setError(null);
    try {
      const response = await backendApi.requestWalletTopUp(token, {
        amount: numericAmount,
        method,
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
      subtitle="Create a persisted top-up request for shop verification."
      showBackButton
      onBackPress={() => router.back()}
      footer={
        <View className="gap-2 border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          <AppButton
            label="Request top-up"
            isLoading={isSubmitting}
            onPress={() => void submitTopUp()}
          />
          <AppButton label="Back to wallet" variant="outline" onPress={() => router.back()} />
        </View>
      }
    >
      <AppCard variant="highlighted" padding="lg">
        <HeroText className="text-sm leading-6 text-neutral-600">
          The requested amount stays pending until the shop verifies the external payment. Only then is wallet credit added.
        </HeroText>
      </AppCard>

      <View className="mt-6 flex-row flex-wrap gap-2">
        {amounts.map((value) => (
          <AppChip
            key={value}
            label={`RM ${value}`}
            size="md"
            variant={amount === value ? 'primary' : 'neutral'}
            onPress={() => setAmount(value)}
          />
        ))}
      </View>

      <AppInput
        label="Custom amount"
        value={amount}
        onChangeText={setAmount}
        keyboardType="numeric"
      />

      <View className="mt-6">
        <HeroText className="mb-3 text-sm font-semibold text-neutral-900">
          Payment method
        </HeroText>
        <View className="flex-row flex-wrap gap-2">
          {topUpMethods.map((item) => (
            <AppChip
              key={item.value}
              label={item.label}
              size="md"
              variant={method === item.value ? 'primary' : 'neutral'}
              onPress={() => setMethod(item.value)}
              accessibilityState={{ selected: method === item.value }}
            />
          ))}
        </View>
      </View>

      {error ? (
        <HeroText className="mt-6 text-sm font-medium text-red-600">
          {error}
        </HeroText>
      ) : null}
    </AppScreen>
  );
}
