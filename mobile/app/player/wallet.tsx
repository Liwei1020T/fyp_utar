import React, { useCallback, useState } from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { ChevronRight } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../components/shared/AppScreen';
import { formatCurrency, formatDateTime } from '../../lib/formatters';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useWallets,
  useWalletTransactions,
} from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendWallet } from '../../services/backendMappers';

export default function PlayerWalletScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const wallets = useWallets();
  const transactions = useWalletTransactions();
  const setLiveWallet = useAppStore((state) => state.setLiveWallet);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refreshWallet = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsRefreshing(true);
    setLoadError(null);
    try {
      const wallet = mapBackendWallet(await backendApi.fetchWallet(token));
      setLiveWallet(wallet.balance, wallet.transactions);
    } catch (error) {
      setLoadError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to refresh the wallet.',
      );
    } finally {
      setIsRefreshing(false);
    }
  }, [setLiveWallet, token]);

  useFocusEffect(
    useCallback(() => {
      void refreshWallet();
    }, [refreshWallet]),
  );

  if (!user || user.role !== 'player') {
    return null;
  }

  const wallet = wallets.find((item) => item.userId === user.id);
  const walletTransactions = transactions.filter((item) => item.userId === user.id);

  return (
    <AppScreen
      headerVariant="primary"
      title="Wallet balance"
      subtitle="Persisted balance and verified wallet transactions."
      showBackButton
      onBackPress={() => router.back()}
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={walletTransactions}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        refreshing={isRefreshing}
        onRefresh={() => void refreshWallet()}
        ListHeaderComponent={
          <View className="gap-4 pb-4">
            <AppCard variant="dark" padding="lg">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-100">
                Available balance
              </HeroText>
              <HeroText className="mt-2 text-[26px] font-bold tracking-tight text-white">
                {formatCurrency(wallet?.availableBalance ?? 0)}
              </HeroText>
              <HeroText className="mt-2 text-sm leading-6 text-primary-100">
                Lifetime top-up {formatCurrency(wallet?.lifetimeTopUps ?? 0)}
              </HeroText>
              {(wallet?.pendingTopUp ?? 0) > 0 ? (
                <HeroText className="mt-1 text-sm leading-6 text-primary-100">
                  Pending verification {formatCurrency(wallet?.pendingTopUp ?? 0)}
                </HeroText>
              ) : null}
            </AppCard>

            <AppButton
              label="Top up wallet"
              size="lg"
              onPress={() => router.push('/player/wallet/top-up')}
            />
          </View>
        }
        renderItem={({ item }) => (
          <AppCard variant="elevated" className="mb-3" padding="md">
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1">
                <HeroText className="text-base font-semibold text-neutral-900">
                  {item.description}
                </HeroText>
                <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                  {formatDateTime(item.createdAt)} • {item.methodLabel ?? 'Wallet ledger'}
                </HeroText>
              </View>
              <HeroText className={`text-base font-bold ${item.direction === 'credit' ? 'text-green-600' : 'text-neutral-900'}`}>
                {item.direction === 'credit' ? '+' : '-'}
                {formatCurrency(item.amount)}
              </HeroText>
            </View>
          </AppCard>
        )}
        ListEmptyComponent={
          <AppCard variant="subtle" className="mb-4" padding="md">
            <HeroText className="text-base font-semibold text-neutral-900">
              No wallet transactions yet
            </HeroText>
            <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
              Verified top-ups and booking payments will appear here.
            </HeroText>
          </AppCard>
        }
        ListFooterComponent={
          <View className="gap-3">
            {loadError ? (
              <AppCard variant="subtle" className="border border-red-100" padding="md">
                <HeroText className="text-sm font-medium text-red-600">
                  {loadError}
                </HeroText>
              </AppCard>
            ) : null}
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Use wallet in booking checkout"
              onPress={() => router.push('/player/bookings')}
            >
              <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center justify-between gap-3">
                <View className="flex-1">
                  <HeroText className="text-base font-semibold text-neutral-900">
                    Use wallet in checkout
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                    Open a priced booking and choose wallet balance as its payment method.
                  </HeroText>
                </View>
                <ChevronRight size={18} color="#94A3B8" />
              </View>
              </AppCard>
            </Pressable>
          </View>
        }
      />
    </AppScreen>
  );
}
