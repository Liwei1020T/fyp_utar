import React from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, ChevronRight } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../components/shared/AppScreen';
import { formatCurrency, formatDateTime } from '../../lib/formatters';
import { useAppStore, useCurrentUser, useWallets } from '../../store/appStore';

export default function PlayerWalletScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const user = useCurrentUser();
  const wallets = useWallets();
  const transactions = useAppStore((state) => state.walletTransactions);

  if (!user || user.role !== 'player') {
    return null;
  }

  const wallet = wallets.find((item) => item.userId === user.id);
  const walletTransactions = transactions.filter((item) => item.userId === user.id);

  return (
    <AppScreen
      headerVariant="primary"
      title="Wallet balance"
      subtitle="Stored balance for future checkout support and mock top-up behavior."
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={walletTransactions}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="gap-6 pb-6">
            <AppCard variant="dark" padding="lg">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-100">
                Available balance
              </HeroText>
              <HeroText className="mt-3 text-[30px] font-bold tracking-tight text-white">
                {formatCurrency(wallet?.availableBalance ?? 0)}
              </HeroText>
              <HeroText className="mt-2 text-sm leading-6 text-primary-100">
                Lifetime top-up {formatCurrency(wallet?.lifetimeTopUps ?? 0)}
              </HeroText>
            </AppCard>

            <AppButton
              label="Top up wallet"
              size="lg"
              onPress={() => router.push('/player/wallet/top-up')}
            />
          </View>
        }
        renderItem={({ item }) => (
          <AppCard variant="elevated" className="mb-4" padding="md">
            <View className="flex-row items-start justify-between gap-4">
              <View className="flex-1">
                <HeroText className="text-base font-semibold text-neutral-900">
                  {item.description}
                </HeroText>
                <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                  {formatDateTime(item.createdAt)} • {item.methodLabel ?? 'Mock balance event'}
                </HeroText>
              </View>
              <HeroText className={`text-base font-bold ${item.direction === 'credit' ? 'text-green-600' : 'text-neutral-900'}`}>
                {item.direction === 'credit' ? '+' : '-'}
                {formatCurrency(item.amount)}
              </HeroText>
            </View>
          </AppCard>
        )}
        ListFooterComponent={
          <Pressable onPress={() => router.push('/player/payments/draft')}>
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-base font-semibold text-neutral-900">
                    Use wallet in checkout
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                    Preview how stored balance can appear as a payment method in the booking flow.
                  </HeroText>
                </View>
                <ChevronRight size={18} color="#94A3B8" />
              </View>
            </AppCard>
          </Pressable>
        }
      />
    </AppScreen>
  );
}
