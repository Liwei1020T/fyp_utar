import React, { useMemo, useState } from 'react';
import { FlatList, Pressable, View, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { 
  Search, 
  Scale, 
  SlidersHorizontal, 
  ChevronLeft, 
  LayoutGrid, 
  Tags,
  Plus,
  Check,
  X
} from 'lucide-react-native';
import { HeroText, HeroTextField } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { useAppStore, useStrings } from '../../../store/appStore';
import { formatLabel } from '../../../lib/formatters';
import { cn } from '../../../components/ui/heroui';

const sortOptions = [
  { id: 'power', label: 'Power' },
  { id: 'price', label: 'Price' },
  { id: 'control', label: 'Control' },
] as const;

type DisplayMode = 'all' | 'brand';

export default function StringsCatalogScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(20);
  const strings = useStrings();
  const compareSelection = useAppStore((state) => state.compareSelection);
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);
  const clearCompareSelection = useAppStore((state) => state.clearCompareSelection);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'repulsion' | 'balanced' | 'control' | 'durable'>('all');
  const [sortBy, setSortBy] = useState<(typeof sortOptions)[number]['id']>('power');
  const [showFilters, setShowFilters] = useState(false);
  const [displayMode, setDisplayMode] = useState<DisplayMode>('all');
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);

  const brands = useMemo(() => {
    return Array.from(new Set(strings.map(s => s.brand))).sort();
  }, [strings]);

  const filteredStrings = useMemo(() => {
    const next = strings.filter((item) => {
      const matchesSearch =
        item.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.brand.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategory === 'all' ? true : item.category === selectedCategory;
      const matchesBrand = !selectedBrand || item.brand === selectedBrand;
      
      return matchesSearch && matchesCategory && matchesBrand;
    });

    if (displayMode === 'all') {
      return next.sort((left, right) => {
        if (sortBy === 'price') return left.price - right.price;
        return right.ratings[sortBy] - left.ratings[sortBy];
      });
    }

    return next;
  }, [searchQuery, selectedCategory, sortBy, strings, displayMode, selectedBrand]);

  const groupedByBrand = useMemo(() => {
    if (displayMode !== 'brand') return [];
    
    const groups: Record<string, typeof strings> = {};
    filteredStrings.forEach(item => {
      if (!groups[item.brand]) groups[item.brand] = [];
      groups[item.brand].push(item);
    });

    return Object.entries(groups).map(([name, data]) => ({ name, data }));
  }, [filteredStrings, displayMode]);

  const renderModeSwitch = () => (
    <View className="flex-row bg-neutral-100/80 p-1 rounded-[16px] mb-4 border border-neutral-200/50">
      <Pressable 
        onPress={() => setDisplayMode('all')}
        className={cn(
          "flex-1 flex-row items-center justify-center gap-2 py-1.5 rounded-[12px]",
          displayMode === 'all' ? "bg-white shadow-sm border border-neutral-200/40" : ""
        )}
      >
        <LayoutGrid size={14} color={displayMode === 'all' ? '#0F172A' : '#64748B'} strokeWidth={2.5} />
        <HeroText className={cn(
          "text-[12px] font-bold tracking-tight",
          displayMode === 'all' ? "text-slate-900" : "text-slate-500"
        )}>
          All Strings
        </HeroText>
      </Pressable>
      <Pressable 
        onPress={() => setDisplayMode('brand')}
        className={cn(
          "flex-1 flex-row items-center justify-center gap-2 py-1.5 rounded-[12px]",
          displayMode === 'brand' ? "bg-white shadow-sm border border-neutral-200/40" : ""
        )}
      >
        <Tags size={14} color={displayMode === 'brand' ? '#0F172A' : '#64748B'} strokeWidth={2.5} />
        <HeroText className={cn(
          "text-[12px] font-bold tracking-tight",
          displayMode === 'brand' ? "text-slate-900" : "text-slate-500"
        )}>
          By Brand
        </HeroText>
      </Pressable>
    </View>
  );

  const renderHeaderComponent = () => (
    <View className="pb-3">
      {renderModeSwitch()}

      <View className="flex-row items-center gap-3 mb-5">
        <View className="flex-1 h-11 flex-row items-center bg-white border border-neutral-200 rounded-full px-4 shadow-sm">
          <Search size={18} color="#94A3B8" strokeWidth={2.5} />
          <HeroTextField
            placeholder="Search models or brands..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            className="flex-1 ml-3 h-full border-0 bg-transparent text-[15px] font-medium text-slate-900"
            selectionColorClassName="accent-primary-600"
            placeholderColorClassName="field-placeholder"
          />
        </View>
        <AppIconButton
          icon={<SlidersHorizontal size={18} color={showFilters ? '#2563EB' : '#475569'} strokeWidth={2.5} />}
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
                  onPress={() => setSelectedCategory(item as typeof selectedCategory)}
                />
              )}
            />
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
                    onPress={() => setSortBy(item.id)}
                  />
                ))}
              </View>
            </AppSection>
          )}

          {displayMode === 'brand' && (
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
                    onPress={() => setSelectedBrand(item === 'all' ? null : item)}
                  />
                )}
              />
            </AppSection>
          )}
        </View>
      )}
    </View>
  );

  const CompactStringCard = ({ item }: { item: typeof strings[0] }) => {
    const isSelected = compareSelection.includes(item.id);

    return (
      <AppCard 
        className="mb-2 shadow-none" 
        variant="default" 
        padding="sm"
        onPress={() => router.push(`/player/strings/${item.id}`)}
      >
        <View className="flex-row items-center gap-3">
          {/* Left: Thumbnail */}
          <View className="h-14 w-14 rounded-lg bg-slate-50 items-center justify-center overflow-hidden border border-slate-100">
            <Image 
              source={{ uri: 'https://images.unsplash.com/photo-1617083277661-8488e0867018?w=100&h=100&fit=crop' }} 
              className="h-full w-full opacity-60"
            />
          </View>

          {/* Center: Info */}
          <View className="flex-1">
            <HeroText className="text-[9px] font-bold uppercase tracking-wider text-primary-600">
              {item.brand}
            </HeroText>
            <HeroText className="text-[15px] font-bold text-slate-900 leading-tight" numberOfLines={1}>
              {item.model}
            </HeroText>
            <HeroText className="text-[11px] font-bold text-slate-400 mt-0.5">
              P: {item.ratings.power} • C: {item.ratings.control} • D: {item.ratings.durability}
            </HeroText>
            <HeroText className="text-[11px] text-slate-500 font-medium" numberOfLines={1}>
              {item.gauge} • {formatLabel(item.category)}
            </HeroText>
          </View>

          {/* Right: Actions */}
          <View className="items-end gap-1.5">
            <HeroText className="text-[10px] font-bold text-slate-400">
              Price at shop
            </HeroText>
            <Pressable 
              onPress={() => toggleCompareSelection(item.id)}
              className={cn(
                "flex-row items-center gap-1 px-2.5 py-1 rounded-full border",
                isSelected ? "bg-primary-600 border-primary-600" : "bg-white border-slate-200"
              )}
            >
              {isSelected ? <Check size={10} color="white" strokeWidth={3} /> : <Plus size={10} color="#64748B" strokeWidth={3} />}
              <HeroText className={cn("text-[9px] font-black uppercase tracking-tighter", isSelected ? "text-white" : "text-slate-500")}>
                {isSelected ? 'Compared' : 'Compare'}
              </HeroText>
            </Pressable>
            <Pressable onPress={() => router.push(`/player/strings/${item.id}`)}>
              <HeroText className="text-[10px] font-bold text-primary-600 uppercase tracking-wider">Details</HeroText>
            </Pressable>
          </View>
        </View>
      </AppCard>
    );
  };

  return (
    <View className="flex-1 bg-[#F8FAFC]">
      <AppScreen
        title="String catalog"
        subtitle="Unified, compact product browsing."
        scrollable={false}
        headerLeft={
          router.canGoBack() ? (
            <AppIconButton
              icon={<ChevronLeft size={20} color="#1E293B" />}
              onPress={() => router.back()}
              className="h-9 w-9 bg-white border border-slate-200"
            />
          ) : undefined
        }
      >
        <FlatList
          className="flex-1"
          data={displayMode === 'all' ? filteredStrings : groupedByBrand}
          keyExtractor={(item) => (displayMode === 'all' ? (item as any).id : (item as any).name)}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          scrollIndicatorInsets={{ bottom: bottomContentInset + 60 }}
          contentContainerStyle={{ paddingBottom: bottomContentInset + 80, paddingTop: 4 }}
          ListHeaderComponent={renderHeaderComponent}
          renderItem={({ item }) => {
            if (displayMode === 'brand') {
              const group = item as { name: string; data: typeof strings };
              return (
                <View className="mb-4">
                  <View className="flex-row items-center justify-between mb-1.5 px-1">
                    <HeroText className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                      {group.name}
                    </HeroText>
                    <Pressable>
                      <HeroText className="text-[9px] font-bold text-primary-600 uppercase tracking-widest">
                        View All
                      </HeroText>
                    </Pressable>
                  </View>
                  {group.data.map((stringItem) => (
                    <CompactStringCard key={stringItem.id} item={stringItem} />
                  ))}
                </View>
              );
            }
            return <CompactStringCard item={item as any} />;
          }}
        />
      </AppScreen>

      {/* Floating Compare Tray */}
      {compareSelection.length >= 2 && (
        <View 
          className="absolute left-4 right-4 z-50 bg-slate-900 rounded-2xl shadow-xl p-3.5 flex-row items-center justify-between"
          style={{ bottom: bottomContentInset - 8 }}
        >
          <View className="flex-row items-center gap-2.5">
            <View className="h-7 w-7 rounded-full bg-primary-600 items-center justify-center">
              <HeroText className="text-[11px] font-bold text-white">{compareSelection.length}</HeroText>
            </View>
            <View>
              <HeroText className="text-[13px] font-bold text-white leading-none">Shortlist Ready</HeroText>
              <HeroText className="text-[10px] text-slate-400 font-medium mt-0.5">Open side-by-side compare</HeroText>
            </View>
          </View>
          <View className="flex-row items-center gap-2">
            <Pressable 
              onPress={clearCompareSelection}
              className="h-9 w-9 items-center justify-center rounded-full bg-white/10"
            >
              <X size={16} color="white" />
            </Pressable>
            <AppButton 
              label="Compare" 
              size="sm" 
              variant="primary" 
              className="h-9 px-4 rounded-full"
              onPress={() => router.push('/player/strings/compare')}
            />
          </View>
        </View>
      )}
    </View>
  );
}
