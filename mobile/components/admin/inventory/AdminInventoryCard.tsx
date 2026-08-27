import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';
import { Minus, Plus } from 'lucide-react-native';
import { AppCard } from '../../ui/AppCard';
import { AppChip, type AppChipVariant } from '../../ui/AppChip';
import { HeroText, cn } from '../../ui/heroui';
import { StringProductImage } from '../../shared/StringProductImage';
import { formatAvailability, formatLabel } from '../../../lib/formatters';
import {
  buildStringDisplayName,
  formatGaugeRange,
  getInventoryAttentionLabel,
  getInventoryAttentionState,
  getInventoryPriceLabel,
} from '../../../lib/inventory';
import type { StringItem } from '../../../types/domain';

function getBadgeVariant(item: StringItem): AppChipVariant {
  if (item.inventory.availabilityStatus === 'out_of_stock') {
    return 'danger';
  }
  if (item.inventory.availabilityStatus === 'low_stock') {
    return 'warning';
  }
  return 'primary';
}

function getPriceChipVariant(item: StringItem): AppChipVariant {
  const price = getInventoryPriceLabel(item);
  if (price.state === 'pending') {
    return 'warning';
  }
  if (price.state === 'quoted_at_shop') {
    return 'neutral';
  }
  return 'secondary';
}

function getAttentionChipVariant(item: StringItem): AppChipVariant {
  const state = getInventoryAttentionState(item);
  if (state === 'out_of_stock') {
    return 'danger';
  }
  if (state === 'inactive') {
    return 'neutral';
  }
  return 'warning';
}

export function AdminStringThumbnail({
  item,
  size = 48,
}: {
  item: StringItem;
  size?: number;
}) {
  const imageUrl = item.catalog.imageUrl ?? item.imageUrl;

  return (
    <View
      className="items-center justify-center overflow-hidden rounded-[10px] border border-field-border bg-app-muted"
      style={{ height: size, width: size }}
    >
      <StringProductImage
        imageUrl={imageUrl}
        brand={item.brand}
        model={item.model}
        gauge={item.gauge}
        accessibilityLabel={`${buildStringDisplayName(item)} thumbnail`}
        className="h-full w-full"
        fallbackClassName="h-full w-full rounded-[10px] border-0 bg-primary-50 shadow-none"
        fallbackTextClassName="px-0 text-center text-[10px] leading-3 tracking-tight text-primary-700"
        fallbackGaugeClassName="mt-1 px-1 py-0"
      />
    </View>
  );
}

function QuickAction({
  label,
  variant = 'outline',
  onPress,
  disabled = false,
}: {
  label: string;
  variant?: 'primary' | 'outline' | 'ghost';
  onPress?: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      className={cn(
        'h-11 items-center justify-center rounded-[12px] border px-3',
        disabled
          ? 'border-field-border bg-app-muted opacity-60'
          : variant === 'primary'
          ? 'border-primary-600 bg-primary-600'
          : variant === 'ghost'
            ? 'border-transparent bg-transparent'
            : 'border-field-border bg-white',
      )}
      style={({ pressed }) => (pressed ? styles.pressed : undefined)}
    >
      <HeroText
        className={cn(
          'text-[11px] font-semibold tracking-tight',
          variant === 'primary' ? 'text-white' : 'text-neutral-700',
        )}
      >
        {label}
      </HeroText>
    </Pressable>
  );
}

export function AdminInventoryCard({
  item,
  onPress,
  attentionOnly = false,
  onSaveStock,
}: {
  item: StringItem;
  onPress?: () => void;
  attentionOnly?: boolean;
  onSaveStock?: (stockQty: number) => Promise<void>;
}) {
  const [isEditingStock, setIsEditingStock] = useState(false);
  const [stockValue, setStockValue] = useState(String(item.inventory.stockQty));
  const [stockError, setStockError] = useState<string | null>(null);
  const [isSavingStock, setIsSavingStock] = useState(false);
  const price = getInventoryPriceLabel(item);
  const attentionState = getInventoryAttentionState(item);
  const detailLine = [
    formatGaugeRange(item.catalog.gaugeMinMm, item.catalog.gaugeMaxMm, item.gauge),
    item.catalog.mainTrait,
    item.category === item.catalog.mainTrait.toLowerCase()
      ? null
      : formatLabel(item.category),
  ]
    .filter(Boolean)
    .join(' \u00b7 ');

  useEffect(() => {
    if (!isEditingStock) {
      setStockValue(String(item.inventory.stockQty));
    }
  }, [isEditingStock, item.inventory.stockQty]);

  const adjustStock = (delta: number) => {
    const current = Number.parseInt(stockValue, 10);
    setStockValue(String(Math.max(0, (Number.isNaN(current) ? 0 : current) + delta)));
    setStockError(null);
  };

  const saveStock = async () => {
    const nextStock = Number(stockValue);
    if (!Number.isInteger(nextStock) || nextStock < 0 || nextStock > 99999) {
      setStockError('Enter a whole number between 0 and 99,999.');
      return;
    }
    if (!onSaveStock) {
      onPress?.();
      return;
    }

    setIsSavingStock(true);
    setStockError(null);
    try {
      await onSaveStock(nextStock);
      setIsEditingStock(false);
    } catch (error) {
      setStockError(error instanceof Error ? error.message : 'Stock could not be saved.');
    } finally {
      setIsSavingStock(false);
    }
  };

  return (
    <AppCard
      padding="none"
      variant={attentionOnly ? 'highlighted' : 'default'}
      className={cn(attentionOnly ? 'border-warning-100/90' : undefined)}
      contentClassName="p-2.5"
    >
      <View className="flex-row gap-2.5">
        <AdminStringThumbnail item={item} />
        <View className="min-w-0 flex-1">
          <View className="flex-row items-start gap-2">
            <View className="min-w-0 flex-1">
              <HeroText className="text-[14px] font-bold tracking-tight text-neutral-950" numberOfLines={1}>
                {item.model}
              </HeroText>
              <HeroText className="mt-0.5 text-[12px] font-semibold text-neutral-500" numberOfLines={1}>
                {item.brand}
              </HeroText>
            </View>
            <AppChip
              label={formatAvailability(item.inventory.availabilityStatus)}
              variant={getBadgeVariant(item)}
            />
          </View>

          <HeroText className="mt-1 text-[12px] leading-4 text-neutral-600" numberOfLines={2}>
            {detailLine}
          </HeroText>

          <View className="mt-1.5 flex-row flex-wrap gap-1.5">
            <AppChip label={`Stock ${item.inventory.stockQty}`} variant="neutral" />
            <AppChip label={price.label} variant={getPriceChipVariant(item)} />
            {attentionState !== 'ready' ? (
              <AppChip
                label={getInventoryAttentionLabel(item)}
                variant={getAttentionChipVariant(item)}
              />
            ) : null}
          </View>

          {isEditingStock ? (
            <View className="mt-2 rounded-[12px] border border-primary-100 bg-primary-50/40 p-2.5">
              <HeroText className="text-[12px] font-semibold text-neutral-700">
                Available stock
              </HeroText>
              <View className="mt-2 flex-row items-center gap-2">
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={`Decrease ${item.model} stock`}
                  onPress={() => adjustStock(-1)}
                  className="h-11 w-11 items-center justify-center rounded-[10px] border border-field-border bg-white"
                >
                  <Minus size={17} color="#475569" strokeWidth={2.2} />
                </Pressable>
                <TextInput
                  accessibilityLabel={`${item.model} stock quantity`}
                  keyboardType="number-pad"
                  value={stockValue}
                  onChangeText={(value) => {
                    setStockValue(value.replace(/[^0-9]/g, ''));
                    setStockError(null);
                  }}
                  selectTextOnFocus
                  className="h-11 min-w-0 flex-1 rounded-[10px] border border-field-border bg-white px-2 text-center text-[16px] font-semibold text-neutral-950 outline-none"
                />
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={`Increase ${item.model} stock`}
                  onPress={() => adjustStock(1)}
                  className="h-11 w-11 items-center justify-center rounded-[10px] border border-field-border bg-white"
                >
                  <Plus size={17} color="#2F64B6" strokeWidth={2.2} />
                </Pressable>
              </View>
              {stockError ? (
                <HeroText accessibilityLiveRegion="polite" className="mt-2 text-xs text-danger">
                  {stockError}
                </HeroText>
              ) : null}
              <View className="mt-3 flex-row justify-end gap-2">
                <QuickAction
                  label="Cancel stock edit"
                  onPress={() => {
                    setStockValue(String(item.inventory.stockQty));
                    setStockError(null);
                    setIsEditingStock(false);
                  }}
                  disabled={isSavingStock}
                />
                <QuickAction
                  label={isSavingStock ? 'Saving stock' : 'Save stock'}
                  variant="primary"
                  onPress={() => void saveStock()}
                  disabled={isSavingStock}
                />
              </View>
            </View>
          ) : (
            <View className="mt-2 flex-row flex-wrap gap-2">
              <QuickAction
                label={attentionState === 'out_of_stock' ? 'Restock' : 'Edit stock'}
                variant="primary"
                onPress={() => {
                  setStockValue(String(item.inventory.stockQty));
                  setStockError(null);
                  setIsEditingStock(true);
                }}
              />
              <QuickAction
                label={attentionState === 'price_missing' ? 'Add price' : 'Edit details'}
                onPress={onPress}
              />
            </View>
          )}
        </View>
      </View>
    </AppCard>
  );
}

export function AdminInventoryPreviewCard({ item }: { item: StringItem }) {
  const price = getInventoryPriceLabel(item);

  return (
    <AppCard variant="highlighted" padding="md">
      <View className="flex-row gap-4">
        <AdminStringThumbnail item={item} size={84} />
        <View className="min-w-0 flex-1">
          <HeroText className="text-[18px] font-bold tracking-tight text-neutral-950" numberOfLines={2}>
            {buildStringDisplayName(item)}
          </HeroText>
          <HeroText className="mt-1 text-[13px] font-semibold text-neutral-500">
            Brand: {item.brand}
          </HeroText>
          <HeroText className="mt-1 text-[13px] leading-5 text-neutral-600">
            {formatGaugeRange(item.catalog.gaugeMinMm, item.catalog.gaugeMaxMm, item.gauge)}
            {' \u00b7 '}
            {item.catalog.mainTrait}
          </HeroText>

          <View className="mt-3 flex-row flex-wrap gap-2">
            <AppChip
              label={formatAvailability(item.inventory.availabilityStatus)}
              variant={getBadgeVariant(item)}
            />
            <AppChip label={`Stock ${item.inventory.stockQty}`} variant="neutral" />
            <AppChip label={price.label} variant={getPriceChipVariant(item)} />
          </View>
        </View>
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  pressed: {
    opacity: 0.94,
    transform: [{ scale: 0.99 }],
  },
});
