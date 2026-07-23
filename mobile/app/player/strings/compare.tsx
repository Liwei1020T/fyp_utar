import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Info, Zap } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { HeroText, cn } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { StringProductImage } from '../../../components/shared/StringProductImage';
import { useAppStore, useLiveRecommendationResults, useStrings } from '../../../store/appStore';
import { formatCurrency } from '../../../lib/formatters';
import { formatTensionRange, getInventoryPriceLabel } from '../../../lib/inventory';
import { AppCompareRadarChart } from '../../../components/ui/AppCompareRadarChart';
import type { StringItem } from '../../../types/domain';

export default function CompareStringsScreen() {
  const router = useRouter();
  const compareSelection = useAppStore((state) => state.compareSelection);
  const clearCompareSelection = useAppStore((state) => state.clearCompareSelection);
  const liveResults = useLiveRecommendationResults();
  const allStrings = useStrings();

  const strings: StringItem[] = compareSelection
    .map((id) => allStrings.find((item) => item.id === id))
    .filter((item): item is StringItem => Boolean(item));

  if (strings.length < 2) {
    return (
      <AppScreen title="Compare strings">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            Select at least two strings to compare.
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Add strings from the catalog or recommendation results, then open this side-by-side view again.
          </HeroText>
          <AppButton label="Back to catalog" className="mt-6" onPress={() => router.replace('/player/strings')} />
        </AppCard>
      </AppScreen>
    );
  }

  // Focus on the first two for the main comparison as per design request
  const stringA = strings[0];
  const stringB = strings[1];

  const getMatchScore = (stringId: string) => {
    const match = liveResults.find((r) => r.stringId === stringId);
    return match ? match.matchScore : null;
  };

  const scoreA = getMatchScore(stringA.id);
  const scoreB = getMatchScore(stringB.id);

  const winner =
    scoreA !== null && scoreB !== null && scoreA !== scoreB
      ? scoreA > scoreB
        ? 'a'
        : 'b'
      : null;
  const winnerString = winner === 'a' ? stringA : winner === 'b' ? stringB : null;
  const winnerScore = winner === 'a' ? scoreA : winner === 'b' ? scoreB : null;

  const resolvePriceLabel = (item: StringItem) => {
    const label = getInventoryPriceLabel(item);
    return label.hasPrice ? formatCurrency(item.price) : label.label;
  };

  const SummaryCard = ({ item, score, isBest, label }: { item: StringItem, score: number | null, isBest: boolean, label: string }) => (
    <AppCard 
      variant={isBest ? 'highlighted' : 'elevated'} 
      padding="sm" 
      className={isBest ? 'border-primary-500 border-2' : 'border-neutral-100'}
    >
      <View className="flex-row items-center gap-3">
        {/* Left: Thumbnail */}
        <View className="h-14 w-14 rounded-lg bg-slate-50 items-center justify-center overflow-hidden border border-slate-100">
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

        {/* Center: Info */}
        <View className="flex-1">
          <View className="flex-row items-center gap-2">
            <View className={cn(
                "px-1.5 py-0.5 rounded-full",
                isBest ? "bg-primary-500" : "bg-secondary-100"
              )}>
              <HeroText className={cn(
                "text-[8px] font-black uppercase",
                isBest ? "text-white" : "text-secondary-700"
              )}>
                {label}
              </HeroText>
            </View>
            <HeroText className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
              {item.brand}
            </HeroText>
          </View>
          <HeroText className="text-[15px] font-bold text-slate-900 mt-0.5" numberOfLines={1}>
            {item.model}
          </HeroText>
          <View className="flex-row items-center gap-2 mt-0.5">
            <HeroText className="text-[11px] font-bold text-slate-400">
              P: {item.ratings.power} • C: {item.ratings.control} • D: {item.ratings.durability}
            </HeroText>
          </View>
        </View>

        {/* Right: Score */}
        {score !== null && (
          <View className="items-end pr-1">
            <HeroText className="text-[16px] font-black text-primary-600 leading-none">
              {score}%
            </HeroText>
            <HeroText className="text-[9px] font-bold text-slate-400 uppercase tracking-tighter mt-0.5">
              Match
            </HeroText>
          </View>
        )}
      </View>
    </AppCard>
  );

  return (
    <AppScreen
      headerVariant="flow"
      title="Compare strings"
      subtitle="Review specs, ratings, strengths, and booking fit in one place."
      showBackButton
      onBackPress={() => router.back()}
    >
      {/* 1. Compare Summary Strip - Redesigned to stacked catalog style */}
      <View className="gap-3 mt-4">
        <SummaryCard 
          item={stringA} 
          score={scoreA} 
          isBest={winner === 'a'}
          label={winner === 'a' ? 'Best Match' : 'Option A'}
        />
        <SummaryCard 
          item={stringB} 
          score={scoreB} 
          isBest={winner === 'b'}
          label={winner === 'b' ? 'Best Match' : 'Option B'}
        />
      </View>

      {/* 2. Performance Section */}
      <AppSection eyebrow="Performance" title="Metric comparison" variant="compact">
        <AppCard variant="elevated" padding="none" className="overflow-hidden">
          <AppCompareRadarChart 
            dataA={stringA.ratings} 
            dataB={stringB.ratings} 
            labelA={stringA.model} 
            labelB={stringB.model} 
          />
          
          <View className="bg-neutral-50 px-5 py-4 border-t border-neutral-100">
            <View className="flex-row items-center gap-2 mb-4">
              <View className="flex-row items-center gap-1.5">
                <View className="w-2 h-2 rounded-full bg-primary-500" />
                <HeroText className="text-[10px] font-bold text-neutral-600">{stringA.model}</HeroText>
              </View>
            <View className="flex-row items-center gap-1.5 ml-4">
                <View className="w-2 h-2 rounded-full bg-secondary-400" />
                <HeroText className="text-[10px] font-bold text-neutral-600">{stringB.model}</HeroText>
              </View>
            </View>

            <View className="gap-2">
              {[
                { label: 'Power', key: 'power' as const },
                { label: 'Control', key: 'control' as const },
                { label: 'Durability', key: 'durability' as const },
                { label: 'Comfort', key: 'comfort' as const },
                { label: 'Sound', key: 'sound' as const },
              ].map((metric) => (
                <View key={metric.key} className="flex-row items-center justify-between">
                  <HeroText className="text-xs font-medium text-neutral-500">{metric.label}</HeroText>
                  <View className="flex-row items-center gap-4">
                    <HeroText className={`text-xs font-bold ${stringA.ratings[metric.key] >= stringB.ratings[metric.key] ? 'text-primary-600' : 'text-neutral-400'}`}>
                      {stringA.ratings[metric.key]}
                    </HeroText>
                    <HeroText className="text-[10px] text-neutral-300">vs</HeroText>
                    <HeroText className={`text-xs font-bold ${stringB.ratings[metric.key] > stringA.ratings[metric.key] ? 'text-primary-600' : 'text-neutral-400'}`}>
                      {stringB.ratings[metric.key]}
                    </HeroText>
                  </View>
                </View>
              ))}
            </View>

            <View className="mt-4 pt-4 border-t border-neutral-100 flex-row items-start gap-2">
              <Info size={14} color="#2F64B6" className="mt-0.5" />
              <HeroText className="text-[11px] text-neutral-600 leading-relaxed italic">
                Catalog scores only. The higher value for each recorded metric is highlighted above.
              </HeroText>
            </View>
          </View>
        </AppCard>
      </AppSection>

      {/* 3. Specs Section */}
      <AppSection eyebrow="Specifications" title="Technical matchup" variant="compact">
        <AppCard variant="subtle" padding="lg">
          <View className="gap-6">
            {[
              { label: 'Gauge', valA: stringA.gauge, valB: stringB.gauge },
              { label: 'Material', valA: stringA.material, valB: stringB.material },
              {
                label: 'Catalog Tension',
                valA: formatTensionRange(
                  stringA.tensionMinLbs,
                  stringA.tensionMaxLbs,
                  'Not recorded',
                ),
                valB: formatTensionRange(
                  stringB.tensionMinLbs,
                  stringB.tensionMaxLbs,
                  'Not recorded',
                ),
              },
              { label: 'Price', valA: resolvePriceLabel(stringA), valB: resolvePriceLabel(stringB) },
            ].map((spec) => (
              <View key={spec.label}>
                <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest text-center mb-2">{spec.label}</HeroText>
                <View className="flex-row items-center justify-between">
                  <View className="flex-1 items-center">
                    <HeroText className="text-sm font-bold text-neutral-900">{spec.valA}</HeroText>
                  </View>
                  <View className="w-px h-4 bg-neutral-200" />
                  <View className="flex-1 items-center">
                    <HeroText className="text-sm font-bold text-neutral-900">{spec.valB}</HeroText>
                  </View>
                </View>
              </View>
            ))}
          </View>
        </AppCard>
      </AppSection>

      {/* 4. Booking Fit Section */}
      <AppSection eyebrow="Booking Fit" title="Setup confidence" variant="compact">
        <AppCard variant="highlighted" padding="lg">
          <View className="flex-row items-center gap-3 mb-4">
            <View className="h-10 w-10 items-center justify-center rounded-xl bg-primary-100">
              <Zap size={20} color="#2F64B6" />
            </View>
            <View className="flex-1">
              <HeroText className="text-sm font-bold text-neutral-900">Score-based comparison</HeroText>
              <HeroText className="text-xs text-neutral-500">Uses saved recommendation scores only</HeroText>
            </View>
          </View>
          <HeroText className="text-[13px] text-neutral-700 leading-relaxed mb-4">
            {winnerString && winnerScore !== null
              ? `${winnerString.model} has the higher saved match score (${winnerScore}%). Its recorded tension range is ${formatTensionRange(winnerString.tensionMinLbs, winnerString.tensionMaxLbs, 'not available')}.`
              : 'No complete pair of distinct recommendation scores is available. Compare the recorded specs and open each detail before booking.'}
          </HeroText>
          <View className="rounded-xl border border-secondary-100 bg-white/50 p-3">
            <HeroText className="mb-1 text-[11px] font-bold uppercase text-primary-700">Tension Note</HeroText>
            <HeroText className="text-xs text-neutral-600">
              {winnerString?.tensionNote ?? 'No score-based winner was selected.'}
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      {/* 5. CTA Area */}
      <View className="mt-8 mb-10 gap-4">
        <AppButton 
          label={winnerString ? `Book ${winnerString.model}` : 'No score-based winner'}
          size="lg" 
          isDisabled={!winnerString}
          onPress={() => winnerString
            ? router.push(`/player/bookings/new?stringId=${winnerString.id}`)
            : undefined}
        />
        
        <View className="flex-row gap-3">
          <View className="flex-1">
            <AppButton 
              label={`Details: ${stringA.model}`} 
              variant="outline" 
              size="md" 
              onPress={() => router.push(`/player/strings/${stringA.id}`)} 
            />
          </View>
          <View className="flex-1">
            <AppButton 
              label={`Details: ${stringB.model}`} 
              variant="outline" 
              size="md" 
              onPress={() => router.push(`/player/strings/${stringB.id}`)} 
            />
          </View>
        </View>

        <View className="flex-row items-center justify-center gap-6 mt-2">
          <Pressable onPress={() => router.push('/player/strings')}>
            <HeroText className="text-xs font-semibold text-neutral-500">Back to catalog</HeroText>
          </Pressable>
          <View className="w-1 h-1 rounded-full bg-neutral-300" />
          <Pressable onPress={clearCompareSelection}>
            <HeroText className="text-xs font-semibold text-primary-600">Clear compare list</HeroText>
          </Pressable>
        </View>
      </View>
    </AppScreen>
  );
}
