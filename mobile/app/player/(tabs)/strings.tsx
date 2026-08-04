import React, { useMemo, useState } from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { 
  Search, 
  SlidersHorizontal, 
  LayoutGrid, 
  Tags,
  Plus,
  Check,
  ChevronRight,
  SearchX,
} from 'lucide-react-native';
import { HeroText, cn } from '../../../components/ui/heroui';
import { AppCard } from '../../../components/ui/AppCard';
import { AppButton } from '../../../components/ui/AppButton';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppSegmentedControl } from '../../../components/ui/AppSegmentedControl';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { FloatingCompareTray } from '../../../components/shared/FloatingCompareTray';
import { StringProductImage } from '../../../components/shared/StringProductImage';
import { useAppStore, useStrings } from '../../../store/appStore';
import { formatCurrency, formatLabel } from '../../../lib/formatters';
import { getInventoryPriceLabel } from '../../../lib/inventory';
import type { StringItem } from '../../../types/domain';

const sortOptions = [
  { id: 'power', label: 'Power' },
  { id: 'price', label: 'Price' },
  { id: 'control', label: 'Control' },
] as const;

const modeOptions = [
  { id: 'all', label: 'All Strings', icon: LayoutGrid },
  { id: 'brand', label: 'By Brand', icon: Tags },
] as const;

type DisplayMode = (typeof modeOptions)[number]['id'];
type BrandGroup = { name: string; data: StringItem[] };
type CatalogListItem = StringItem | BrandGroup;

function isBrandGroup(item: CatalogListItem): item is BrandGroup {
  return 'data' in item;
}

export default function StringsCatalogScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(20);
  const strings = useStrings();
  const compareSelection = useAppStore((state) => state.compareSelection);
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'repulsion' | 'balanced' | 'control' | 'durable'>('all');
  const [sortBy, setSortBy] = useState<(typeof sortOptions)[number]['id']>('power');
  const [showFilters, setShowFilters] = useState(false);
  const [displayMode, setDisplayMode] = useState<DisplayMode>('all');
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [selectedPrice, setSelectedPrice] = useState<
    'all' | 'below_30' | '30_50' | 'above_50'
  >('all');
  const [selectedGauge, setSelectedGauge] = useState<string | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<
    'power' | 'control' | 'durability' | 'comfort' | 'sound' | null
  >(null);

  const hasActiveFilters =
    searchQuery.trim().length > 0 ||
    selectedCategory !== 'all' ||
    selectedBrand !== null ||
    selectedPrice !== 'all' ||
    selectedGauge !== null ||
    selectedFeature !== null;

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedBrand(null);
    setSelectedPrice('all');
    setSelectedGauge(null);
    setSelectedFeature(null);
  };

  const brands = useMemo(() => {
    return Array.from(new Set(strings.map(s => s.brand))).sort();
  }, [strings]);
  const gauges = useMemo(
    () => Array.from(new Set(strings.map((item) => item.gauge))).sort(),
    [strings],
  );

  const filteredStrings = useMemo(() => {
    const next = strings.filter((item) => {
      const matchesSearch =
        item.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.brand.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategory === 'all' ? true : item.category === selectedCategory;
      const matchesBrand = !selectedBrand || item.brand === selectedBrand;
      const matchesGauge = !selectedGauge || item.gauge === selectedGauge;
      const matchesPrice =
        selectedPrice === 'all' ||
        (selectedPrice === 'below_30' && item.price > 0 && item.price < 30) ||
        (selectedPrice === '30_50' && item.price >= 30 && item.price <= 50) ||
        (selectedPrice === 'above_50' && item.price > 50);
      const matchesFeature =
        !selectedFeature || item.ratings[selectedFeature] >= 8;
      
      return (
        matchesSearch &&
        matchesCategory &&
        matchesBrand &&
        matchesGauge &&
        matchesPrice &&
        matchesFeature
      );
    });

    if (displayMode === 'all') {
      return next.sort((left, right) => {
        if (sortBy === 'price') return left.price - right.price;
        return right.ratings[sortBy] - left.ratings[sortBy];
      });
    }

    return next;
  }, [
    searchQuery,
    selectedCategory,
    sortBy,
    strings,
    displayMode,
    selectedBrand,
    selectedGauge,
    selectedPrice,
    selectedFeature,
  ]);

  const groupedByBrand = useMemo(() => {
    if (displayMode !== 'brand') return [];
    
    const groups: Record<string, StringItem[]> = {};
    filteredStrings.forEach(item => {
      if (!groups[item.brand]) groups[item.brand] = [];
      groups[item.brand].push(item);
    });

    return Object.entries(groups).map(([name, data]) => ({ name, data }));
  }, [filteredStrings, displayMode]);

  const renderHeaderComponent = () => (
    <View className="pb-3">
      <AppSegmentedControl
        options={modeOptions}
        selectedId={displayMode}
        onSelect={setDisplayMode}
        className="mb-4"
      />

      <View className="flex-row items-center gap-3 mb-5">
        <AppInput
          variant="minimal"
          accessibilityLabel="Search string catalog"
          placeholder="Search models or brands..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          leftAdornment={<Search size={18} color="#94A3B8" strokeWidth={2.5} />}
          className="flex-1 mb-0"
          inputClassName="text-[15px] font-medium"
        />
        <AppIconButton
          icon={<SlidersHorizontal size={18} color={showFilters ? '#2563EB' : '#475569'} strokeWidth={2.5} />}
          accessibilityLabel={showFilters ? 'Hide catalog filters' : 'Show catalog filters'}
          accessibilityState={{ expanded: showFilters }}
          onPress={() => setShowFilters(!showFilters)}
          className={cn(
            "h-11 w-11 rounded-full border shadow-sm",
            showFilters ? "bg-primary-50 border-primary-100" : "bg-white border-neutral-200"
          )}
        />
      </View>

      {showFilters && (
        <View className="mb-4 bg-white/40 p-3 rounded-[24px] border border-neutral-100">
          <AppSection eyebrow="Collection" title="Category" variant="compact" className="mt-0">
            <FlatList
              horizontal
              showsHorizontalScrollIndicator={false}
              data={['all', 'repulsion', 'balanced', 'control', 'durable']}
              keyExtractor={(item) => item}
              ItemSeparatorComponent={() => <View className="w-2" />}
              renderItem={({ item }) => (
                <AppChip
                  label={item === 'all' ? 'All' : formatLabel(item)}
                  size="sm"
                  variant={selectedCategory === item ? 'primary' : 'neutral'}
                  accessibilityState={{ selected: selectedCategory === item }}
                  onPress={() => setSelectedCategory(item as typeof selectedCategory)}
                />
              )}
            />
          </AppSection>

          <View className="h-px bg-neutral-100 my-4" />

          <AppSection eyebrow="Price" title="Price range" variant="compact" className="mt-0">
            <View className="flex-row flex-wrap gap-2">
              {[
                ['all', 'All prices'],
                ['below_30', 'Below RM30'],
                ['30_50', 'RM30–RM50'],
                ['above_50', 'Above RM50'],
              ].map(([id, label]) => (
                <AppChip
                  key={id}
                  label={label}
                  size="sm"
                  variant={selectedPrice === id ? 'primary' : 'neutral'}
                  accessibilityState={{ selected: selectedPrice === id }}
                  onPress={() => setSelectedPrice(id as typeof selectedPrice)}
                />
              ))}
            </View>
          </AppSection>

          <View className="h-px bg-neutral-100 my-4" />

          <AppSection eyebrow="Specification" title="Gauge" variant="compact" className="mt-0">
            <View className="flex-row flex-wrap gap-2">
              {['all', ...gauges].map((gauge) => (
                <AppChip
                  key={gauge}
                  label={gauge === 'all' ? 'All gauges' : gauge}
                  size="sm"
                  variant={
                    (gauge === 'all' && !selectedGauge) ||
                    selectedGauge === gauge
                      ? 'secondary'
                      : 'neutral'
                  }
                  accessibilityState={{
                    selected:
                      (gauge === 'all' && !selectedGauge) || selectedGauge === gauge,
                  }}
                  onPress={() => setSelectedGauge(gauge === 'all' ? null : gauge)}
                />
              ))}
            </View>
          </AppSection>

          <View className="h-px bg-neutral-100 my-4" />

          <AppSection eyebrow="Strength" title="Feature score 8+" variant="compact" className="mt-0">
            <View className="flex-row flex-wrap gap-2">
              {(['power', 'control', 'durability', 'comfort', 'sound'] as const).map(
                (feature) => (
                  <AppChip
                    key={feature}
                    label={formatLabel(feature)}
                    size="sm"
                    variant={selectedFeature === feature ? 'info' : 'neutral'}
                    accessibilityState={{ selected: selectedFeature === feature }}
                    onPress={() =>
                      setSelectedFeature((current) =>
                        current === feature ? null : feature,
                      )
                    }
                  />
                ),
              )}
            </View>
          </AppSection>

          <View className="h-px bg-neutral-100 my-4" />

          {displayMode === 'all' && (
            <AppSection eyebrow="Sort" title="Sort by" variant="compact" className="mt-0">
              <View className="flex-row gap-2">
                {sortOptions.map((item) => (
                  <AppChip
                    key={item.id}
                    label={item.label}
                    size="sm"
                    variant={sortBy === item.id ? 'info' : 'neutral'}
                    accessibilityState={{ selected: sortBy === item.id }}
                    onPress={() => setSortBy(item.id)}
                  />
                ))}
              </View>
            </AppSection>
          )}

          <AppSection eyebrow="Manufacturers" title="Brand" variant="compact" className="mt-0">
            <FlatList
              horizontal
              showsHorizontalScrollIndicator={false}
              data={['all', ...brands]}
              keyExtractor={(item) => item}
              ItemSeparatorComponent={() => <View className="w-2" />}
              renderItem={({ item }) => (
                <AppChip
                  label={item === 'all' ? 'All Brands' : item}
                  size="sm"
                  variant={(item === 'all' && !selectedBrand) || selectedBrand === item ? 'secondary' : 'neutral'}
                  accessibilityState={{
                    selected:
                      (item === 'all' && !selectedBrand) || selectedBrand === item,
                  }}
                  onPress={() => setSelectedBrand(item === 'all' ? null : item)}
                />
              )}
            />
          </AppSection>
        </View>
      )}
    </View>
  );

  const CompactStringCard = ({ item }: { item: typeof strings[0] }) => {
    const isSelected = compareSelection.includes(item.id);
    const priceLabel = getInventoryPriceLabel(item);

    return (
      <AppCard 
        className="mb-2 shadow-none" 
        variant="default" 
        padding="sm"
      >
        <View className="flex-row items-center gap-3">
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`${item.brand} ${item.model}, ${item.gauge}, ${formatLabel(item.category)}`}
            accessibilityHint="Open string details"
            className="min-w-0 flex-1 flex-row items-center gap-3 rounded-lg"
            onPress={() => router.push(`/player/strings/${item.id}`)}
          >
            <View className="h-14 w-14 items-center justify-center overflow-hidden rounded-lg border border-slate-100 bg-slate-50">
              <StringProductImage
                imageUrl={item.imageUrl}
                brand={item.brand}
                model={item.model}
                gauge={item.gauge}
                className="h-full w-full"
                fallbackClassName="h-12 w-9 rounded-xl border-[3px]"
                fallbackTextClassName="px-2 text-[8px]"
                fallbackGaugeClassName="mt-2 px-2 py-1"
                resizeMode="cover"
              />
            </View>

            <View className="min-w-0 flex-1">
              <HeroText className="text-[10px] font-bold uppercase tracking-wider text-primary-600">
                {item.brand}
              </HeroText>
              <HeroText className="text-[15px] font-bold leading-tight text-slate-900" numberOfLines={2}>
                {item.model}
              </HeroText>
              <HeroText className="mt-0.5 text-[11px] font-bold text-slate-500">
                P: {item.ratings.power} • C: {item.ratings.control} • D: {item.ratings.durability}
              </HeroText>
              <HeroText className="text-[11px] font-medium text-slate-500" numberOfLines={1}>
                {item.gauge} • {formatLabel(item.category)}
              </HeroText>
            </View>
            <ChevronRight size={16} color="#94A3B8" />
          </Pressable>

          <View className="items-end gap-1.5">
            <HeroText
              className={cn(
                'text-[10px] font-bold',
                priceLabel.hasPrice ? 'text-slate-600' : 'text-slate-400',
              )}
            >
              {priceLabel.hasPrice ? formatCurrency(item.price) : priceLabel.label}
            </HeroText>
            <Pressable 
              accessibilityRole="button"
              accessibilityLabel={`${isSelected ? 'Remove' : 'Add'} ${item.brand} ${item.model} ${isSelected ? 'from' : 'to'} comparison`}
              accessibilityState={{ selected: isSelected }}
              onPress={() => toggleCompareSelection(item.id)}
              className={cn(
                "min-h-11 min-w-[76px] flex-row items-center justify-center gap-1 rounded-full border px-2.5 py-1",
                isSelected ? "bg-primary-600 border-primary-600" : "bg-white border-slate-200"
              )}
            >
              {isSelected ? <Check size={12} color="white" strokeWidth={3} /> : <Plus size={12} color="#64748B" strokeWidth={3} />}
              <HeroText className={cn("text-[11px] font-bold", isSelected ? "text-white" : "text-slate-600")}>
                {isSelected ? 'Compared' : 'Compare'}
              </HeroText>
            </Pressable>
          </View>
        </View>
      </AppCard>
    );
  };

  return (
    <View className="flex-1 bg-[#F8FAFC]">
      <AppScreen
        headerVariant="primary"
        title="String catalog"
        subtitle="Browse, filter, and compare strings with a compact view."
        scrollable={false}
      >
        <FlatList
          className="flex-1"
          data={(displayMode === 'all' ? filteredStrings : groupedByBrand) as CatalogListItem[]}
          keyExtractor={(item) => (isBrandGroup(item) ? item.name : item.id)}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          scrollIndicatorInsets={{ bottom: bottomContentInset + 60 }}
          contentContainerStyle={{ paddingBottom: bottomContentInset + 80, paddingTop: 4 }}
          ListHeaderComponent={renderHeaderComponent}
          ListEmptyComponent={
            <AppCard variant="subtle" padding="lg" className="mt-2">
              <View className="items-center">
                <View className="h-12 w-12 items-center justify-center rounded-full bg-primary-50">
                  <SearchX size={20} color="#2563EB" />
                </View>
                <HeroText className="mt-4 text-center text-lg font-bold text-slate-900">
                  {hasActiveFilters ? 'No strings match' : 'No strings available'}
                </HeroText>
                <HeroText className="mt-1 max-w-[320px] text-center text-sm leading-5 text-slate-600">
                  {hasActiveFilters
                    ? 'Try a broader search or clear the active filters.'
                    : 'The live catalog does not contain any strings yet.'}
                </HeroText>
                {hasActiveFilters ? (
                  <AppButton
                    label="Clear filters"
                    variant="outline"
                    size="sm"
                    className="mt-4"
                    onPress={clearFilters}
                  />
                ) : null}
              </View>
            </AppCard>
          }
          renderItem={({ item }) => {
            if (isBrandGroup(item)) {
              const group = item;
              return (
                <View className="mb-4">
                  <View className="flex-row items-center justify-between mb-1.5 px-1">
                    <HeroText className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                      {group.name}
                    </HeroText>
                  </View>
                  {group.data.map((stringItem) => (
                    <CompactStringCard key={stringItem.id} item={stringItem} />
                  ))}
                </View>
              );
            }
            return <CompactStringCard item={item} />;
          }}
        />
      </AppScreen>

      <FloatingCompareTray />
    </View>
  );
}
