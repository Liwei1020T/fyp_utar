import React, { useMemo, useState } from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowUpWideNarrow, Search, Scale, SlidersHorizontal, Sparkles, ChevronLeft } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { useAppStore, useStrings } from '../../../store/appStore';
import { formatCurrency, formatLabel } from '../../../lib/formatters';

const sortOptions = [
  { id: 'power', label: 'Power' },
  { id: 'price', label: 'Price' },
  { id: 'control', label: 'Control' },
] as const;

export default function StringsCatalogScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(20);
  const strings = useStrings();
  const compareSelection = useAppStore((state) => state.compareSelection);
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'repulsion' | 'balanced' | 'control' | 'durable'>('all');
  const [sortBy, setSortBy] = useState<(typeof sortOptions)[number]['id']>('power');
  const [showControls, setShowControls] = useState(false);

  const filteredStrings = useMemo(() => {
    const next = strings.filter((item) => {
      const matchesSearch =
        item.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.brand.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.inventoryTags.join(' ').toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategory === 'all' ? true : item.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });

    return next.sort((left, right) => {
      if (sortBy === 'price') {
        return left.price - right.price;
      }

      return right.ratings[sortBy] - left.ratings[sortBy];
    });
  }, [searchQuery, selectedCategory, sortBy, strings]);

  return (
    <AppScreen
      title="String catalog"
      subtitle="Search, filter, sort, and build a compare shortlist."
      scrollable={false}
      headerLeft={
        router.canGoBack() ? (
          <AppIconButton
            icon={<ChevronLeft size={20} color="#111827" />}
            accessibilityLabel="Go back"
            onPress={() => router.back()}
          />
        ) : undefined
      }
    >
      <FlatList
        className="flex-1"
        data={filteredStrings}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        scrollIndicatorInsets={{ bottom: bottomContentInset }}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="gap-6 pb-6">
            <AppCard variant="highlighted" padding="lg">
              <View className="flex-row items-start justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
                    Product discovery
                  </HeroText>
                  <HeroText className="mt-2 text-[24px] font-bold tracking-tight text-neutral-950">
                    Compare the shortlist before you book.
                  </HeroText>
                  <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
                    Search quickly, keep filters nearby, and push the winner straight into booking.
                  </HeroText>
                </View>
                <View className="h-12 w-12 items-center justify-center rounded-2xl bg-primary-600">
                  <Sparkles size={20} color="white" />
                </View>
              </View>
            </AppCard>

            <View className="flex-row items-start gap-3">
              <AppInput
                className="mb-0 flex-1"
                containerClassName="shadow-none"
                placeholder="Search strings, brands, or traits..."
                value={searchQuery}
                onChangeText={setSearchQuery}
                leftAdornment={<Search size={18} color="#94A3B8" />}
              />
              <AppIconButton
                icon={<SlidersHorizontal size={20} color="#475569" />}
                accessibilityLabel={showControls ? 'Hide filter and sort controls' : 'Show filter and sort controls'}
                onPress={() => setShowControls((current) => !current)}
                className="mt-1 h-14 w-14 rounded-[24px]"
              />
            </View>

            {showControls ? (
              <>
                <AppSection eyebrow="Filters" title="Catalog controls" variant="compact" className="mt-0">
                  <FlatList
                    horizontal
                    showsHorizontalScrollIndicator={false}
                    data={['all', 'repulsion', 'balanced', 'control', 'durable']}
                    keyExtractor={(item) => item}
                    ItemSeparatorComponent={() => <View className="w-2" />}
                    renderItem={({ item }) => (
                      <AppChip
                        label={item === 'all' ? 'All strings' : formatLabel(item)}
                        size="md"
                        variant={selectedCategory === item ? 'primary' : 'neutral'}
                        onPress={() => setSelectedCategory(item as typeof selectedCategory)}
                      />
                    )}
                  />
                </AppSection>

                <AppSection eyebrow="Sort" title="Ranking lens" variant="compact" className="mt-0">
                  <View className="flex-row flex-wrap gap-2">
                    {sortOptions.map((item) => (
                      <AppChip
                        key={item.id}
                        label={item.label}
                        size="md"
                        variant={sortBy === item.id ? 'info' : 'neutral'}
                        onPress={() => setSortBy(item.id)}
                      />
                    ))}
                  </View>
                </AppSection>
              </>
            ) : (
              <AppCard variant="subtle" padding="sm">
                <HeroText className="text-sm leading-6 text-neutral-600">
                  Showing {selectedCategory === 'all' ? 'all strings' : formatLabel(selectedCategory)} • sorted by {formatLabel(sortBy)}
                </HeroText>
              </AppCard>
            )}

            {compareSelection.length >= 2 ? (
              <AppCard variant="dark" padding="md">
                <View className="flex-row items-center justify-between gap-4">
                  <View>
                    <HeroText className="text-base font-bold text-white">
                      Compare {compareSelection.length} strings
                    </HeroText>
                    <HeroText className="mt-1 text-sm text-primary-100">
                      Open the side-by-side view with your current shortlist.
                    </HeroText>
                  </View>
                  <AppButton
                    label="Compare"
                    variant="secondary"
                    size="sm"
                    onPress={() => router.push('/player/strings/compare')}
                  />
                </View>
              </AppCard>
            ) : null}
          </View>
        }
        renderItem={({ item }) => {
          const isSelected = compareSelection.includes(item.id);

          return (
            <AppCard className="mb-4" variant="elevated" padding="md">
              <View className="gap-4">
                <View className="flex-row items-start justify-between gap-4">
                  <View className="flex-1">
                    <HeroText className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary-700">
                      {item.brand}
                    </HeroText>
                    <HeroText className="mt-1 text-[22px] font-bold tracking-tight text-neutral-950">
                      {item.model}
                    </HeroText>
                    <HeroText className="mt-2 text-sm leading-6 text-neutral-500" numberOfLines={2}>
                      {item.description}
                    </HeroText>
                  </View>

                  <View className="items-end gap-3">
                    <HeroText className="rounded-[18px] bg-primary-50 px-3 py-2 text-lg font-bold tracking-tight text-neutral-950">
                      {formatCurrency(item.price)}
                    </HeroText>
                    <AppChip label={item.category} variant="neutral" />
                  </View>
                </View>

                <View className="flex-row flex-wrap gap-2">
                  <AppChip label={`${item.ratings.power}/10 power`} variant="secondary" />
                  <AppChip label={`${item.ratings.control}/10 control`} variant="info" />
                  <AppChip label={`${item.ratings.durability}/10 durability`} variant="success" />
                  <AppChip label={item.gauge} variant="neutral" />
                </View>

                <View className="flex-row gap-3">
                  <AppButton
                    label="View details"
                    size="md"
                    className="flex-1"
                    trailingIcon={<ArrowUpWideNarrow size={16} color="white" />}
                    onPress={() => router.push(`/player/strings/${item.id}`)}
                  />
                  <AppButton
                    label={isSelected ? 'Selected' : 'Compare'}
                    variant={isSelected ? 'secondary' : 'outline'}
                    size="md"
                    className="w-28"
                    leadingIcon={<Scale size={16} color={isSelected ? '#78350F' : '#475569'} />}
                    onPress={() => toggleCompareSelection(item.id)}
                  />
                </View>
              </View>
            </AppCard>
          );
        }}
      />
    </AppScreen>
  );
}
