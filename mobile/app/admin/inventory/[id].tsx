import React, { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { formatAvailability } from '../../../lib/formatters';
import { useAppStore, useStrings } from '../../../store/appStore';

export default function AdminInventoryDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const strings = useStrings();
  const updateStringItem = useAppStore((state) => state.updateStringItem);
  const stringItem = strings.find((item) => item.id === params.id);
  const [price, setPrice] = useState(String(stringItem?.price ?? 0));
  const [stockLevel, setStockLevel] = useState(String(stringItem?.stockLevel ?? 0));
  const [notes, setNotes] = useState(stringItem?.adminNote ?? '');

  if (!stringItem) {
    return null;
  }

  return (
    <AppScreen
      tone="admin"
      title={`${stringItem.brand} ${stringItem.model}`}
      subtitle="Frontend-only inventory edit flow for price, stock-like indicator, availability, and notes."
      headerLeft={
        <Pressable onPress={() => router.back()}>
          <ChevronLeft size={24} color="#111827" />
        </Pressable>
      }
    >
      <AppSection eyebrow="Current state" title="Inventory health">
        <AppCard variant="highlighted" padding="md">
          <View className="flex-row flex-wrap gap-2">
            <AppChip label={formatAvailability(stringItem.availability)} variant={stringItem.availability === 'in_stock' ? 'success' : 'warning'} />
            <AppChip label={`Stock ${stringItem.stockLevel}`} variant="secondary" />
          </View>
          <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
            {stringItem.reviewHighlight}
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Edit" title="Shop-facing fields">
        <AppInput label="Price" value={price} onChangeText={setPrice} keyboardType="numeric" />
        <AppInput label="Stock level" value={stockLevel} onChangeText={setStockLevel} keyboardType="numeric" />
        <AppInput label="Shop note" value={notes} onChangeText={setNotes} multiline inputClassName="min-h-24" />
      </AppSection>

      <View className="mt-6 gap-3">
        <AppButton
          label="Save inventory changes"
          onPress={() =>
            updateStringItem(stringItem.id, {
              price: Number(price) || stringItem.price,
              stockLevel: Number(stockLevel) || stringItem.stockLevel,
              adminNote: notes,
              availability:
                Number(stockLevel) <= 0
                  ? 'out_of_stock'
                  : Number(stockLevel) <= 5
                    ? 'low_stock'
                    : 'in_stock',
            })
          }
        />
        <AppButton label="Back to inventory" variant="outline" onPress={() => router.back()} />
      </View>
    </AppScreen>
  );
}
