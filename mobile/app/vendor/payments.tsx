import React from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../components/shared/AppScreen';
import {
  formatCurrency,
  formatDateTime,
  formatPaymentMethod,
  formatPaymentStatus,
} from '../../lib/formatters';
import { getPaymentStatusVariant } from '../../components/ui/theme';
import { useCurrentUser, usePayments } from '../../store/appStore';

export default function AdminPaymentsScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const user = useCurrentUser();
  const payments = usePayments();

  if (!user || user.role !== 'admin') {
    return null;
  }

  const adminPayments = payments.filter((item) => item.adminId === user.id || item.type === 'wallet_top_up');

  return (
    <AppScreen
      tone="admin"
      title="Payments monitor"
      subtitle="Frontend-only view for successful, failed, and wallet-related payment activity."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={adminPayments}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        renderItem={({ item }) => (
          <AppCard variant="elevated" className="mb-4" padding="md">
            <View className="flex-row items-start justify-between gap-4">
              <View className="flex-1">
                <HeroText className="text-base font-semibold text-neutral-900">
                  {item.bookingId ?? 'Wallet top-up'} • {formatPaymentMethod(item.method)}
                </HeroText>
                <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                  {formatDateTime(item.createdAt)} • {item.reference}
                </HeroText>
              </View>
              <View className="items-end gap-2">
                <AppChip
                  label={formatPaymentStatus(item.status)}
                  variant={getPaymentStatusVariant(item.status)}
                />
                <HeroText className="text-base font-bold text-neutral-900">
                  {formatCurrency(item.amount)}
                </HeroText>
              </View>
            </View>
          </AppCard>
        )}
      />
    </AppScreen>
  );
}
