import React, { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { useAppStore, useCurrentUser } from '../../../store/appStore';

const amounts = ['20', '50', '80', '100'];

export default function WalletTopUpScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const topUpWallet = useAppStore((state) => state.topUpWallet);
  const [amount, setAmount] = useState('50');

  if (!user || user.role !== 'player') {
    return null;
  }

  return (
    <AppScreen
      title="Top up wallet"
      subtitle="Frontend-only top-up flow to support future stored-balance checkout."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      <AppCard variant="highlighted" padding="lg">
        <HeroText className="text-sm leading-6 text-neutral-600">
          Choose an amount and simulate a top-up. The balance updates locally and is immediately available in payment selection.
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

      <View className="mt-6 gap-3">
        <AppButton
          label="Confirm top-up"
          onPress={() => {
            topUpWallet(user.id, Number(amount) || 0, 'Online banking');
            router.replace('/player/wallet');
          }}
        />
        <AppButton label="Back to wallet" variant="outline" onPress={() => router.back()} />
      </View>
    </AppScreen>
  );
}
