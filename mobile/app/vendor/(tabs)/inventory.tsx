import React from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { formatAvailability } from '../../../lib/formatters';
import { useStrings } from '../../../store/appStore';

export default function AdminInventoryScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const strings = useStrings();

  return (
    <AppScreen title="Inventory" subtitle="Manage available strings, pricing, stock-like status, and shop notes." scrollable={false}>
      <FlatList
        className="flex-1"
        data={strings}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        renderItem={({ item }) => (
          <Pressable onPress={() => router.push(`/admin/inventory/${item.id}`)}>
            <AppCard variant="elevated" className="mb-4" padding="md">
              <View className="flex-row items-start justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                    {item.brand} {item.model}
                  </HeroText>
                  <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
                    {item.gauge} • {item.inventoryTags.join(' • ')} • stock {item.stockLevel}
                  </HeroText>
                </View>
                <AppChip
                  label={formatAvailability(item.availability)}
                  variant={item.availability === 'in_stock' ? 'success' : item.availability === 'low_stock' ? 'warning' : 'danger'}
                />
              </View>
            </AppCard>
          </Pressable>
        )}
      />
    </AppScreen>
  );
}
