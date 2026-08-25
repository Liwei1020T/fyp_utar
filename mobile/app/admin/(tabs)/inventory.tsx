import React, { useMemo, useState } from 'react';
import { FlatList, Pressable, StyleSheet, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Search, SlidersHorizontal } from 'lucide-react-native';
import { AdminInventoryCard } from '../../../components/admin/inventory/AdminInventoryCard';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { AppSelect } from '../../../components/ui/AppSelect';
import { HeroText, cn } from '../../../components/ui/heroui';
import { appChromeColors } from '../../../components/ui/theme';
import { backendApi } from '../../../services/backendApi';
import { mapBackendInventoryStringToStringItem } from '../../../services/backendMappers';
import {
  buildStringSearchBlob,
  getInventoryAttentionState,
  getInventorySummary,
  hasPendingInventoryPrice,
  inventoryAttentionScore,
} from '../../../lib/inventory';
import { useAppStore, useBackendAccessToken, useStrings } from '../../../store/appStore';
import type { StringItem } from '../../../types/domain';

type InventoryStatusFilter =
  | 'all'
  | 'in_stock'
  | 'low_stock'
  | 'out_of_stock'
  | 'price_missing';

type InventorySort = 'attention' | 'brand' | 'stock' | 'price';

const STATUS_FILTERS: { id: InventoryStatusFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'in_stock', label: 'In Stock' },
  { id: 'low_stock', label: 'Low Stock' },
  { id: 'out_of_stock', label: 'Out of Stock' },
  { id: 'price_missing', label: 'Price Missing' },
];

const SORT_OPTIONS: { id: InventorySort; label: string }[] = [
  { id: 'attention', label: 'Attention first' },
  { id: 'brand', label: 'Brand' },
  { id: 'stock', label: 'Stock level' },
  { id: 'price', label: 'Price state' },
];

function matchesStatusFilter(item: StringItem, selected: InventoryStatusFilter) {
  if (selected === 'all') {
    return true;
  }
  if (selected === 'price_missing') {
    return hasPendingInventoryPrice(item);
  }
  return item.inventory.availabilityStatus === selected;
}

function sortInventory(items: StringItem[], sortBy: InventorySort) {
  const next = [...items];

  return next.sort((left, right) => {
    if (sortBy === 'brand') {
      return `${left.brand} ${left.model}`.localeCompare(`${right.brand} ${right.model}`);
    }

    if (sortBy === 'stock') {
      const stockDiff = left.inventory.stockQty - right.inventory.stockQty;
      return stockDiff !== 0
        ? stockDiff
        : `${left.brand} ${left.model}`.localeCompare(`${right.brand} ${right.model}`);
    }

    if (sortBy === 'price') {
      const order = { pending: 0, quoted_at_shop: 1, priced: 2 } as const;
      const leftOrder = order[left.inventory.priceStatus];
      const rightOrder = order[right.inventory.priceStatus];
      if (leftOrder !== rightOrder) {
        return leftOrder - rightOrder;
      }
      return (left.inventory.price ?? Number.MAX_SAFE_INTEGER)
        - (right.inventory.price ?? Number.MAX_SAFE_INTEGER);
    }

    const scoreDiff = inventoryAttentionScore(right) - inventoryAttentionScore(left);
    if (scoreDiff !== 0) {
      return scoreDiff;
    }
    return left.inventory.stockQty - right.inventory.stockQty;
  });
}

function SearchField({
  value,
  onChangeText,
}: {
  value: string;
  onChangeText: (value: string) => void;
}) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <View
      className={cn(
        'flex-1 flex-row items-center gap-2.5 rounded-[12px] border bg-white px-4',
        isFocused ? 'border-primary-600' : 'border-[#D2D2D7]',
      )}
      style={{ height: 52 }}
    >
      <Search
        size={20}
        color={isFocused ? appChromeColors.primary : 'rgba(29,29,31,0.48)'}
        strokeWidth={2}
      />
      <TextInput
        accessibilityLabel="Search inventory"
        placeholder="Search inventory"
        value={value}
        onChangeText={onChangeText}
        onBlur={() => setIsFocused(false)}
        onFocus={() => setIsFocused(true)}
        placeholderTextColor="rgba(29,29,31,0.48)"
        selectionColor={appChromeColors.primary}
        className="flex-1 border-0 bg-transparent px-0 text-[16px] text-neutral-900 outline-none"
        style={{ height: '100%', paddingVertical: 0 }}
      />
    </View>
  );
}

function ToolbarButton({
  label,
  accessibilityLabel,
  icon,
  isActive = false,
  onPress,
  className,
}: {
  label: string;
  accessibilityLabel?: string;
  icon: React.ReactNode;
  isActive?: boolean;
  onPress: () => void;
  className?: string;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ selected: isActive }}
      onPress={onPress}
      className={cn(
        'flex-row items-center justify-center gap-1.5 rounded-[10px] border px-3.5',
        isActive ? 'border-primary-100 bg-primary-50' : 'border-[#D8E2EE] bg-white',
        className,
      )}
      style={({ pressed }) => [styles.toolbarButton, pressed ? styles.pressed : undefined]}
    >
      {icon}
      <HeroText
        className={cn(
          'text-[12px] font-semibold tracking-tight',
          isActive ? 'text-primary-700' : 'text-neutral-600',
        )}
      >
        {label}
      </HeroText>
    </Pressable>
  );
}

function SectionHeader({
  title,
  countLabel,
}: {
  title: string;
  countLabel: string;
}) {
  return (
    <View className="mb-3 mt-1 flex-row items-center justify-between">
      <HeroText className="text-[15px] font-bold tracking-tight text-neutral-950">
        {title}
      </HeroText>
      <HeroText className="text-[12px] font-semibold text-neutral-500">
        {countLabel}
      </HeroText>
    </View>
  );
}

export default function AdminInventoryScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(18);
  const token = useBackendAccessToken();
  const strings = useStrings();
  const updateStringItem = useAppStore((state) => state.updateStringItem);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<InventoryStatusFilter>('all');
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<InventorySort>('attention');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  const brands = useMemo(
    () => Array.from(new Set(strings.map((item) => item.brand))).sort(),
    [strings],
  );

  const summary = useMemo(() => getInventorySummary(strings), [strings]);

  const filteredInventory = useMemo(() => {
    const normalizedSearch = searchQuery.trim().toLowerCase();
    const filtered = strings.filter((item) => {
      const matchesSearch =
        normalizedSearch.length === 0
        || buildStringSearchBlob(item).includes(normalizedSearch);
      const matchesBrand = !selectedBrand || item.brand === selectedBrand;

      return matchesSearch && matchesBrand && matchesStatusFilter(item, selectedStatus);
    });

    return sortInventory(filtered, sortBy);
  }, [searchQuery, selectedBrand, selectedStatus, sortBy, strings]);

  const attentionItems = useMemo(
    () =>
      filteredInventory.filter(
        (item) => getInventoryAttentionState(item) !== 'ready',
      ),
    [filteredInventory],
  );

  const saveStock = async (item: StringItem, stockQty: number) => {
    if (!token) {
      throw new Error('Your admin session expired. Sign in again before saving.');
    }

    const updated = await backendApi.adminUpdateInventoryString(token, item.id, {
      stock_level: stockQty,
      movement_type: stockQty > item.inventory.stockQty ? 'RESTOCK' : 'ADJUSTMENT',
      reference_type: 'manual_quick_edit',
    });
    updateStringItem(item.id, mapBackendInventoryStringToStringItem(updated));
  };

  return (
    <AppScreen
      tone="admin"
      headerVariant="primary"
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
        ListHeaderComponent={
          <View className="pb-2">
            <HeroText className="mb-3 text-[13px] font-semibold tracking-tight text-neutral-700">
              {summary.itemCount} items · {summary.lowStockCount} low stock · {summary.pricePendingCount} price pending
            </HeroText>

            <View className="mb-3 flex-row gap-2">
              <SearchField value={searchQuery} onChangeText={setSearchQuery} />
              <ToolbarButton
                label={selectedBrand ? 'Filters · 1' : 'Filters'}
                accessibilityLabel="Show inventory filters"
                isActive={showAdvancedFilters || Boolean(selectedBrand)}
                icon={
                  <SlidersHorizontal
                    size={17}
                    color={showAdvancedFilters || selectedBrand ? '#2F64B6' : '#64748B'}
                    strokeWidth={2}
                  />
                }
                onPress={() => setShowAdvancedFilters((value) => !value)}
              />
            </View>

            <View className="mb-3 flex-row items-end gap-2">
              <AppSelect
                label="Stock status"
                value={selectedStatus}
                options={STATUS_FILTERS.map((filter) => ({
                  id: filter.id,
                  label: filter.label,
                }))}
                onChange={(id) => setSelectedStatus(id as InventoryStatusFilter)}
                className="flex-1"
              />
              <AppSelect
                label="Sort order"
                value={sortBy}
                options={SORT_OPTIONS.map((option) => ({
                  id: option.id,
                  label: option.label,
                }))}
                onChange={(id) => setSortBy(id as InventorySort)}
                className="flex-1"
              />
            </View>

            {showAdvancedFilters ? (
              <View className="mb-4 rounded-[14px] border border-[#D8E2EE] bg-white px-4 py-4">
                <HeroText className="text-[12px] font-bold uppercase tracking-[0.18em] text-primary-700">
                  Filters
                </HeroText>

                <AppSelect
                  label="Brand"
                  value={selectedBrand ?? '__all_brands__'}
                  placeholder="All brands"
                  options={[
                    { id: '__all_brands__', label: 'All brands' },
                    ...brands.map((brand) => ({ id: brand, label: brand })),
                  ]}
                  onChange={(id) => setSelectedBrand(id === '__all_brands__' ? null : id)}
                />
              </View>
            ) : null}

            <SectionHeader
              title="Needs attention"
              countLabel={`${attentionItems.length} item${attentionItems.length === 1 ? '' : 's'}`}
            />
            {attentionItems.length > 0 ? (
              <View className="gap-2">
                {attentionItems.map((item) => (
                  <AdminInventoryCard
                    key={`attention-${item.id}`}
                    item={item}
                    attentionOnly
                    onPress={() => router.push(`/admin/inventory/${item.id}`)}
                    onSaveStock={(stockQty) => saveStock(item, stockQty)}
                  />
                ))}
              </View>
            ) : (
              <View className="mb-3 rounded-[22px] border border-[#D8E2EE] bg-white px-4 py-4">
                <HeroText className="text-[14px] font-semibold text-neutral-900">
                  No urgent stock or pricing issues in this view.
                </HeroText>
                <HeroText className="mt-1 text-[12px] leading-5 text-neutral-500">
                  Inventory is currently ready for bookings based on the selected filters.
                </HeroText>
              </View>
            )}

            <SectionHeader
              title="All inventory"
              countLabel={`${filteredInventory.length} shown`}
            />
          </View>
        }
        ListEmptyComponent={
          <View className="rounded-[22px] border border-[#D8E2EE] bg-white px-4 py-4">
            <HeroText className="text-[14px] font-semibold text-neutral-900">
              No inventory matches these filters.
            </HeroText>
            <HeroText className="mt-1 text-[12px] leading-5 text-neutral-500">
              Clear the search, status, or brand filters to widen the list again.
            </HeroText>
          </View>
        }
        renderItem={({ item }) => (
          <View className="mb-2">
            <AdminInventoryCard
              item={item}
              onPress={() => router.push(`/admin/inventory/${item.id}`)}
              onSaveStock={(stockQty) => saveStock(item, stockQty)}
            />
          </View>
        )}
      />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  toolbarButton: {
    height: 52,
    minWidth: 104,
  },
  pressed: {
    opacity: 0.94,
    transform: [{ scale: 0.99 }],
  },
});
