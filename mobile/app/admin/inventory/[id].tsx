import React, { useEffect, useState } from 'react';
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
import { useAppStore, useBackendAccessToken, useStrings } from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendInventoryStringToStringItem } from '../../../services/backendMappers';

export default function AdminInventoryDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const updateStringItem = useAppStore((state) => state.updateStringItem);
  const stringItem = strings.find((item) => item.id === params.id);
  const [price, setPrice] = useState(String(stringItem?.price ?? 0));
  const [stockLevel, setStockLevel] = useState(String(stringItem?.stockLevel ?? 0));
  const [notes, setNotes] = useState(stringItem?.adminNote ?? '');
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!token || !params.id) {
      return;
    }

    const stringId = params.id;
    let cancelled = false;

    const hydrateInventoryItem = async () => {
      try {
        const response = await backendApi.adminFetchInventoryString(token, stringId);
        if (cancelled) {
          return;
        }
        const mapped = mapBackendInventoryStringToStringItem(response);
        updateStringItem(mapped.id, mapped);
        setPrice(String(mapped.price));
        setStockLevel(String(mapped.stockLevel));
        setNotes(mapped.adminNote ?? '');
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof BackendApiError
              ? loadError.message
              : 'Failed to load inventory item.',
          );
        }
      }
    };

    void hydrateInventoryItem();

    return () => {
      cancelled = true;
    };
  }, [params.id, token, updateStringItem]);

  if (!stringItem) {
    return null;
  }

  const saveInventory = async () => {
    const nextPrice = Number(price) || stringItem.price;
    const nextStockLevel = Number(stockLevel) || 0;
    const patch = {
      price: nextPrice,
      stockLevel: nextStockLevel,
      adminNote: notes,
      availability:
        nextStockLevel <= 0
          ? 'out_of_stock'
          : nextStockLevel <= 5
            ? 'low_stock'
            : 'in_stock',
    } as const;

    setError(null);

    if (!token) {
      updateStringItem(stringItem.id, patch);
      return;
    }

    setIsSaving(true);
    try {
      const updated = await backendApi.adminUpdateInventoryString(token, stringItem.id, {
        price_rm: nextPrice,
        stock_level: nextStockLevel,
        admin_note: notes,
      });
      updateStringItem(stringItem.id, mapBackendInventoryStringToStringItem(updated));
    } catch (saveError) {
      setError(
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to update inventory.',
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <AppScreen
      tone="admin"
      title={`${stringItem.brand} ${stringItem.model}`}
      subtitle="Live inventory edit flow for price, stock level, availability, and shop notes."
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
        {error ? (
          <HeroText className="text-sm font-semibold text-danger-600">
            {error}
          </HeroText>
        ) : null}
      </AppSection>

      <View className="mt-6 gap-3">
        <AppButton
          label="Save inventory changes"
          onPress={saveInventory}
          isLoading={isSaving}
        />
        <AppButton label="Back to inventory" variant="outline" onPress={() => router.back()} />
      </View>
    </AppScreen>
  );
}
