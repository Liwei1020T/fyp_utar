import React, { useMemo, useState } from 'react';
import { Image, Pressable, StyleSheet, View } from 'react-native';
import { AppCard } from '../../ui/AppCard';
import { AppChip, type AppChipVariant } from '../../ui/AppChip';
import { HeroText, cn } from '../../ui/heroui';
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

function buildInitials(item: StringItem) {
  return item.brand
    .split(/\s+/)
    .map((token) => token[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export function AdminStringThumbnail({
  item,
  size = 64,
}: {
  item: StringItem;
  size?: number;
}) {
  const [hasError, setHasError] = useState(false);
  const imageUrl = item.catalog.imageUrl ?? item.imageUrl;
  const initials = useMemo(() => buildInitials(item), [item]);

  return (
    <View
      className="items-center justify-center overflow-hidden rounded-[18px] border border-field-border bg-app-muted"
      style={{ height: size, width: size }}
    >
      {!hasError && imageUrl ? (
        <Image
          source={{ uri: imageUrl }}
          resizeMode="contain"
          accessibilityLabel={`${buildStringDisplayName(item)} thumbnail`}
          onError={() => setHasError(true)}
          style={styles.thumbnailImage}
        />
      ) : (
        <View className="items-center justify-center">
          <HeroText className="text-sm font-bold tracking-[0.12em] text-primary-700">
            {initials}
          </HeroText>
          <HeroText className="mt-1 text-[10px] font-medium text-neutral-400">
            No photo
          </HeroText>
        </View>
      )}
    </View>
  );
}

function QuickAction({
  label,
  variant = 'outline',
  onPress,
}: {
  label: string;
  variant?: 'primary' | 'outline' | 'ghost';
  onPress?: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      className={cn(
        'h-11 items-center justify-center rounded-[12px] border px-3',
        variant === 'primary'
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
  quickActions,
}: {
  item: StringItem;
  onPress?: () => void;
  attentionOnly?: boolean;
  quickActions?: {
    label: string;
    variant?: 'primary' | 'outline' | 'ghost';
    onPress?: () => void;
  }[];
}) {
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

  return (
    <AppCard
      padding="sm"
      variant={attentionOnly ? 'highlighted' : 'default'}
      className={cn('rounded-[24px]', attentionOnly ? 'border-warning-100/90' : undefined)}
      contentClassName="p-3.5"
    >
      <View className="flex-row gap-3">
        <AdminStringThumbnail item={item} />
        <View className="min-w-0 flex-1">
          <View className="flex-row items-start gap-2">
            <View className="min-w-0 flex-1">
              <HeroText className="text-[15px] font-bold tracking-tight text-neutral-950" numberOfLines={1}>
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

          <HeroText className="mt-1.5 text-[12px] leading-4 text-neutral-600" numberOfLines={2}>
            {detailLine}
          </HeroText>

          <View className="mt-2 flex-row flex-wrap gap-1.5">
            <AppChip label={`Stock ${item.inventory.stockQty}`} variant="neutral" />
            <AppChip label={price.label} variant={getPriceChipVariant(item)} />
            {attentionState !== 'ready' ? (
              <AppChip
                label={getInventoryAttentionLabel(item)}
                variant={getAttentionChipVariant(item)}
              />
            ) : null}
          </View>

          <View className="mt-2.5 flex-row flex-wrap gap-2">
            {(quickActions ?? [
              {
                label:
                  attentionState === 'out_of_stock'
                    ? 'Restock'
                    : attentionState === 'price_missing'
                      ? 'Edit price'
                      : 'Edit stock',
                variant: 'primary' as const,
                onPress,
              },
              { label: 'Edit details', onPress },
              { label: 'Notes', variant: 'ghost' as const, onPress },
            ]).map((action) => (
              <QuickAction
                key={action.label}
                label={action.label}
                variant={action.variant}
                onPress={action.onPress}
              />
            ))}
          </View>
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
  thumbnailImage: {
    ...StyleSheet.absoluteFillObject,
    height: '100%',
    width: '100%',
  },
});
