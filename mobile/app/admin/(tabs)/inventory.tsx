import React, { useMemo, useState } from 'react';
import { FlatList, Image, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowUpDown, Search, SlidersHorizontal } from 'lucide-react-native';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText, HeroTextField, cn } from '../../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { formatAvailability, formatCurrency, formatLabel } from '../../../lib/formatters';
import { useStrings } from '../../../store/appStore';
import type { StringItem } from '../../../types/domain';

type InventoryStatusFilter =
  | 'all'
  | 'in_stock'
  | 'low_stock'
  | 'out_of_stock'
  | 'price_missing';

type InventorySort = 'attention' | 'stock' | 'brand';

type PillTone = 'blue' | 'amber' | 'red' | 'muted' | 'neutral';

const statusFilters: Array<{ id: InventoryStatusFilter; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'in_stock', label: 'In Stock' },
  { id: 'low_stock', label: 'Low Stock' },
  { id: 'out_of_stock', label: 'Out of Stock' },
  { id: 'price_missing', label: 'Price Missing' },
];

const sortOptions: Array<{ id: InventorySort; label: string }> = [
  { id: 'attention', label: 'Attention' },
  { id: 'stock', label: 'Stock' },
  { id: 'brand', label: 'Brand' },
];

const thumbnailPalette = [
  { background: 'EAF2FF', foreground: '2F64B6' },
  { background: 'FFF7E8', foreground: '9A6B17' },
  { background: 'EEF8F4', foreground: '2F7A58' },
  { background: 'F1F5F9', foreground: '475569' },
  { background: 'FFF1F1', foreground: 'B42318' },
];

function getPriceState(item: StringItem) {
  if (item.price <= 0) {
    return {
      label: 'Price pending',
      isMissing: true,
      tone: 'amber' as const,
    };
  }

  const isShopQuoted = item.inventoryTags.some((tag) =>
    ['premium', 'elite', 'top tier'].includes(tag.toLowerCase()),
  );

  if (isShopQuoted) {
    return {
      label: 'Quoted at shop',
      isMissing: false,
      tone: 'neutral' as const,
    };
  }

  return {
    label: formatCurrency(item.price),
    isMissing: false,
    tone: 'blue' as const,
  };
}

function getInventoryTone(item: StringItem): PillTone {
  if (item.availability === 'out_of_stock') {
    return 'red';
  }
  if (item.availability === 'low_stock') {
    return 'amber';
  }
  return 'blue';
}

function getAttentionScore(item: StringItem) {
  const priceState = getPriceState(item);
  let score = 0;

  if (item.availability === 'out_of_stock') {
    score += 100;
  }
  if (priceState.isMissing) {
    score += 80;
  }
  if (item.availability === 'low_stock') {
    score += 60;
  }
  if (item.stockLevel <= 2) {
    score += 20;
  }

  return score;
}

function needsAttention(item: StringItem) {
  return getAttentionScore(item) > 0;
}

function getAttentionReason(item: StringItem) {
  if (item.availability === 'out_of_stock') {
    return 'Restock before bookings';
  }
  if (getPriceState(item).isMissing) {
    return 'Add price before checkout';
  }
  if (item.stockLevel <= 2) {
    return 'Urgent stock check';
  }
  if (item.availability === 'low_stock') {
    return 'Low stock watch';
  }
  return 'Ready';
}

function compareByAttention(left: StringItem, right: StringItem) {
  const scoreDiff = getAttentionScore(right) - getAttentionScore(left);

  if (scoreDiff !== 0) {
    return scoreDiff;
  }

  const stockDiff = left.stockLevel - right.stockLevel;

  if (stockDiff !== 0) {
    return stockDiff;
  }

  return `${left.brand} ${left.model}`.localeCompare(`${right.brand} ${right.model}`);
}

function getStringPhotoUri(item: StringItem) {
  const possiblePhoto = item as StringItem & { imageUrl?: string; photoUrl?: string };

  if (possiblePhoto.imageUrl || possiblePhoto.photoUrl) {
    return possiblePhoto.imageUrl ?? possiblePhoto.photoUrl;
  }

  const paletteIndex = Math.abs(
    `${item.brand}${item.model}`
      .split('')
      .reduce((total, char) => total + char.charCodeAt(0), 0),
  ) % thumbnailPalette.length;
  const palette = thumbnailPalette[paletteIndex];
  const modelToken = item.model
    .split(/\s+/)
    .map((part) => part.replace(/[^a-zA-Z0-9]/g, ''))
    .filter(Boolean)
    .slice(0, 2)
    .join(' ')
    .slice(0, 8)
    .toUpperCase();

  return `https://placehold.co/112x112/${palette.background}/${palette.foreground}.png?text=${encodeURIComponent(modelToken || item.brand[0] || 'S')}`;
}

function getBrandInitials(item: StringItem) {
  return item.brand
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function statusVariant(id: InventoryStatusFilter) {
  if (id === 'low_stock' || id === 'price_missing') {
    return 'warning';
  }
  if (id === 'out_of_stock') {
    return 'danger';
  }
  if (id === 'in_stock') {
    return 'primary';
  }
  return 'neutral';
}

function matchesStatusFilter(item: StringItem, status: InventoryStatusFilter) {
  if (status === 'all') {
    return true;
  }
  if (status === 'price_missing') {
    return getPriceState(item).isMissing;
  }
  return item.availability === status;
}

function sortInventory(items: StringItem[], sortBy: InventorySort) {
  const next = [...items];

  if (sortBy === 'stock') {
    return next.sort((left, right) => {
      const stockDiff = left.stockLevel - right.stockLevel;
      return stockDiff !== 0
        ? stockDiff
        : `${left.brand} ${left.model}`.localeCompare(`${right.brand} ${right.model}`);
    });
  }

  if (sortBy === 'brand') {
    return next.sort((left, right) =>
      `${left.brand} ${left.model}`.localeCompare(`${right.brand} ${right.model}`),
    );
  }

  return next.sort(compareByAttention);
}

function SummaryStrip({
  itemCount,
  lowStockCount,
  pricePendingCount,
}: {
  itemCount: number;
  lowStockCount: number;
  pricePendingCount: number;
}) {
  return (
    <View className="mb-3 rounded-lg border border-[#DDE6F0] bg-white px-3.5 py-3">
      <HeroText className="text-[13px] font-semibold text-neutral-900">
        {itemCount} items / {lowStockCount} low stock / {pricePendingCount} price pending
      </HeroText>
      <HeroText className="mt-0.5 text-[12px] text-neutral-500">
        Operational stock, pricing, and readiness checks.
      </HeroText>
    </View>
  );
}

function StatusPill({ label, tone }: { label: string; tone: PillTone }) {
  const shellStyles = {
    blue: 'border-primary-100 bg-primary-50',
    amber: 'border-warning-100 bg-warning-50',
    red: 'border-red-100 bg-red-50',
    muted: 'border-[#E7DFC8] bg-[#F8F4E9]',
    neutral: 'border-neutral-200 bg-neutral-100',
  };

  const textStyles = {
    blue: 'text-primary-700',
    amber: 'text-warning-700',
    red: 'text-red-700',
    muted: 'text-[#7B6B42]',
    neutral: 'text-neutral-600',
  };

  return (
    <View className={cn('rounded-lg border px-2 py-1', shellStyles[tone])}>
      <HeroText className={cn('text-[10px] font-semibold', textStyles[tone])}>
        {label}
      </HeroText>
    </View>
  );
}

function ToolbarButton({
  label,
  isActive = false,
  icon,
  onPress,
}: {
  label: string;
  isActive?: boolean;
  icon: React.ReactNode;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      className={cn(
        'h-11 flex-row items-center gap-1.5 rounded-lg border px-3',
        isActive ? 'border-primary-100 bg-primary-50' : 'border-neutral-200 bg-white',
      )}
      style={({ pressed }) => (pressed ? styles.pressed : undefined)}
    >
      {icon}
      <HeroText
        className={cn(
          'text-[12px] font-semibold',
          isActive ? 'text-primary-700' : 'text-neutral-600',
        )}
      >
        {label}
      </HeroText>
    </Pressable>
  );
}

function SearchField({
  value,
  onChangeText,
}: {
  value: string;
  onChangeText: (value: string) => void;
}) {
  return (
    <View className="h-11 flex-1 flex-row items-center gap-2 rounded-lg border border-neutral-200 bg-white px-3">
      <Search size={17} color="#64748B" strokeWidth={2} />
      <HeroTextField
        variant="secondary"
        placeholder="Search string or brand"
        value={value}
        onChangeText={onChangeText}
        className="h-full flex-1 border-0 bg-transparent px-0 text-[14px] text-neutral-900"
        selectionColorClassName="accent-primary-600"
        placeholderColorClassName="field-placeholder"
      />
    </View>
  );
}

function MiniAction({
  label,
  variant = 'outline',
  onPress,
}: {
  label: string;
  variant?: 'primary' | 'outline' | 'ghost';
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      className={cn(
        'h-8 items-center justify-center rounded-lg border px-2.5',
        variant === 'primary'
          ? 'border-primary-600 bg-primary-600'
          : variant === 'ghost'
            ? 'border-transparent bg-transparent'
            : 'border-neutral-200 bg-white',
      )}
      style={({ pressed }) => (pressed ? styles.pressed : undefined)}
    >
      <HeroText
        className={cn(
          'text-[11px] font-semibold',
          variant === 'primary' ? 'text-white' : 'text-neutral-700',
        )}
      >
        {label}
      </HeroText>
    </Pressable>
  );
}

function StringThumbnail({ item }: { item: StringItem }) {
  const [hasImageError, setHasImageError] = useState(false);
  const photoUri = getStringPhotoUri(item);

  return (
    <View className="h-14 w-14 items-center justify-center overflow-hidden rounded-lg border border-neutral-200 bg-[#F3F5F8]">
      <View className="h-full w-full items-center justify-center">
        <HeroText className="text-sm font-bold text-neutral-500">
          {getBrandInitials(item)}
        </HeroText>
      </View>
      {!hasImageError ? (
        <Image
          source={{ uri: photoUri }}
          resizeMode="contain"
          accessibilityLabel={`${item.brand} ${item.model} string photo`}
          onError={() => setHasImageError(true)}
          style={styles.thumbnailImage}
        />
      ) : null}
    </View>
  );
}

function InventoryCard({
  item,
  isAttention = false,
  onOpen,
}: {
  item: StringItem;
  isAttention?: boolean;
  onOpen: () => void;
}) {
  const priceState = getPriceState(item);
  const traits = [
    formatLabel(item.category),
    ...item.inventoryTags.filter((tag) => tag.toLowerCase() !== item.category),
  ].slice(0, 3);

  return (
    <View
      className={cn(
        'mb-2 rounded-lg border bg-white px-3 py-3',
        isAttention ? 'border-warning-100' : 'border-[#E1E8F0]',
      )}
    >
      <View className="flex-row gap-3">
        <StringThumbnail item={item} />
        <View className="min-w-0 flex-1">
          <View className="flex-row items-start gap-2">
            <View className="min-w-0 flex-1">
              <HeroText className="text-[15px] font-bold leading-5 text-neutral-950" numberOfLines={1}>
                {item.model}
              </HeroText>
              <HeroText className="mt-0.5 text-[12px] font-semibold text-neutral-500" numberOfLines={1}>
                {item.brand}
              </HeroText>
            </View>
            <StatusPill label={formatAvailability(item.availability)} tone={getInventoryTone(item)} />
          </View>

          <HeroText className="mt-1.5 text-[12px] leading-4 text-neutral-600" numberOfLines={2}>
            {item.gauge} / {traits.join(' / ')}
          </HeroText>

          <View className="mt-2 flex-row flex-wrap gap-1.5">
            <StatusPill label={`Stock ${item.stockLevel}`} tone={item.stockLevel <= 5 ? 'amber' : 'neutral'} />
            <StatusPill
              label={priceState.label}
              tone={priceState.isMissing ? 'muted' : priceState.tone}
            />
            {isAttention ? <StatusPill label={getAttentionReason(item)} tone="amber" /> : null}
          </View>
        </View>
      </View>

      <View className="mt-2.5 flex-row gap-2">
        <MiniAction label="Edit stock" variant="primary" onPress={onOpen} />
        <MiniAction label="Edit price" onPress={onOpen} />
        <MiniAction label="Notes" variant="ghost" onPress={onOpen} />
      </View>
    </View>
  );
}

export default function AdminInventoryScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const strings = useStrings();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<InventoryStatusFilter>('all');
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<InventorySort>('attention');
  const [showFilters, setShowFilters] = useState(false);

  const brands = useMemo(
    () => Array.from(new Set(strings.map((item) => item.brand))).sort(),
    [strings],
  );

  const summary = useMemo(() => {
    return {
      itemCount: strings.length,
      lowStockCount: strings.filter((item) => item.availability === 'low_stock').length,
      pricePendingCount: strings.filter((item) => getPriceState(item).isMissing).length,
    };
  }, [strings]);

  const filteredInventory = useMemo(() => {
    const normalizedSearch = searchQuery.trim().toLowerCase();
    const next = strings.filter((item) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        item.model.toLowerCase().includes(normalizedSearch) ||
        item.brand.toLowerCase().includes(normalizedSearch);
      const matchesBrand = !selectedBrand || item.brand === selectedBrand;

      return matchesSearch && matchesBrand && matchesStatusFilter(item, selectedStatus);
    });

    return sortInventory(next, sortBy);
  }, [searchQuery, selectedBrand, selectedStatus, sortBy, strings]);

  const attentionItems = useMemo(
    () => filteredInventory.filter(needsAttention).sort(compareByAttention),
    [filteredInventory],
  );

  const cycleSort = () => {
    const currentIndex = sortOptions.findIndex((item) => item.id === sortBy);
    const next = sortOptions[(currentIndex + 1) % sortOptions.length];
    setSortBy(next.id);
  };

  const openInventoryItem = (itemId: string) => {
    router.push(`/admin/inventory/${itemId}`);
  };

  const renderFilterChip = (item: { id: InventoryStatusFilter; label: string }) => (
    <AppChip
      key={item.id}
      label={item.label}
      variant={selectedStatus === item.id ? statusVariant(item.id) : 'neutral'}
      onPress={() => setSelectedStatus(item.id)}
    />
  );

  const renderHeader = () => (
    <View className="pb-3">
      <SummaryStrip
        itemCount={summary.itemCount}
        lowStockCount={summary.lowStockCount}
        pricePendingCount={summary.pricePendingCount}
      />

      <View className="mb-3 flex-row items-center gap-2">
        <SearchField value={searchQuery} onChangeText={setSearchQuery} />
        <ToolbarButton
          label="Filter"
          isActive={showFilters || Boolean(selectedBrand)}
          icon={<SlidersHorizontal size={16} color={showFilters || selectedBrand ? '#2F64B6' : '#64748B'} strokeWidth={2} />}
          onPress={() => setShowFilters((value) => !value)}
        />
        <ToolbarButton
          label={sortOptions.find((item) => item.id === sortBy)?.label ?? 'Sort'}
          isActive
          icon={<ArrowUpDown size={16} color="#2F64B6" strokeWidth={2} />}
          onPress={cycleSort}
        />
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        className="mb-3"
        contentContainerClassName="gap-2 pr-5"
      >
        {statusFilters.map(renderFilterChip)}
      </ScrollView>

      {showFilters ? (
        <View className="mb-4 rounded-lg border border-[#DDE6F0] bg-white px-3 py-3">
          <HeroText className="text-[12px] font-bold text-neutral-900">
            By brand
          </HeroText>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            className="mt-2"
            contentContainerClassName="gap-2 pr-5"
          >
            <AppChip
              label="All Brands"
              variant={!selectedBrand ? 'primary' : 'neutral'}
              onPress={() => setSelectedBrand(null)}
            />
            {brands.map((brand) => (
              <AppChip
                key={brand}
                label={brand}
                variant={selectedBrand === brand ? 'primary' : 'neutral'}
                onPress={() => setSelectedBrand(brand)}
              />
            ))}
          </ScrollView>

          <HeroText className="mt-3 text-[12px] font-bold text-neutral-900">
            Sort
          </HeroText>
          <View className="mt-2 flex-row flex-wrap gap-2">
            {sortOptions.map((item) => (
              <AppChip
                key={item.id}
                label={item.label}
                variant={sortBy === item.id ? 'secondary' : 'neutral'}
                onPress={() => setSortBy(item.id)}
              />
            ))}
          </View>
        </View>
      ) : null}

      <View className="mb-4">
        <View className="mb-2 flex-row items-center justify-between">
          <HeroText className="text-[16px] font-bold text-neutral-950">
            Needs attention
          </HeroText>
          <HeroText className="text-[12px] font-semibold text-neutral-500">
            {attentionItems.length} item{attentionItems.length === 1 ? '' : 's'}
          </HeroText>
        </View>

        {attentionItems.length > 0 ? (
          attentionItems.map((item) => (
            <InventoryCard
              key={`attention-${item.id}`}
              item={item}
              isAttention
              onOpen={() => openInventoryItem(item.id)}
            />
          ))
        ) : (
          <View className="rounded-lg border border-[#E1E8F0] bg-white px-3 py-3">
            <HeroText className="text-[13px] font-semibold text-neutral-700">
              No stock or pricing issues in this view.
            </HeroText>
          </View>
        )}
      </View>

      <View className="mb-2 flex-row items-center justify-between">
        <HeroText className="text-[16px] font-bold text-neutral-950">
          All inventory
        </HeroText>
        <HeroText className="text-[12px] font-semibold text-neutral-500">
          {filteredInventory.length} shown
        </HeroText>
      </View>
    </View>
  );

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      compactHeader
      title="Inventory"
      subtitle="Manage stock, pricing, and shop readiness."
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={filteredInventory}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        scrollIndicatorInsets={{ bottom: bottomContentInset }}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={
          <View className="rounded-lg border border-[#E1E8F0] bg-white px-3 py-4">
            <HeroText className="text-[14px] font-bold text-neutral-900">
              No inventory matches these filters.
            </HeroText>
            <HeroText className="mt-1 text-[12px] leading-5 text-neutral-500">
              Clear search, status, or brand filters to widen the list.
            </HeroText>
          </View>
        }
        renderItem={({ item }) => (
          <InventoryCard item={item} onOpen={() => openInventoryItem(item.id)} />
        )}
      />
    </AppScreen>
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
