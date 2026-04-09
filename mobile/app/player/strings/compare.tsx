import React from 'react';
import { Pressable, ScrollView, View, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, Scale, Info, Zap, ShieldCheck, Target, AlertCircle } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText, cn } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { useAppStore, useLiveRecommendationResults } from '../../../store/appStore';
import { getStringById } from '../../../services/mockAppService';
import { formatCurrency } from '../../../lib/formatters';
import { AppCompareRadarChart } from '../../../components/ui/AppCompareRadarChart';
import type { StringItem } from '../../../types/domain';

export default function CompareStringsScreen() {
  const router = useRouter();
  const compareSelection = useAppStore((state) => state.compareSelection);
  const clearCompareSelection = useAppStore((state) => state.clearCompareSelection);
  const liveResults = useLiveRecommendationResults();

  const strings: StringItem[] = compareSelection
    .map((id) => getStringById(id))
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

  // Determine if one is clearly a "best match" (higher score)
  const isABest = scoreA !== null && scoreB !== null && scoreA >= scoreB;

  const SummaryCard = ({ item, score, isBest, label }: { item: StringItem, score: number | null, isBest: boolean, label: string }) => (
    <AppCard 
      variant={isBest ? 'highlighted' : 'elevated'} 
      padding="sm" 
      className={isBest ? 'border-primary-500 border-2' : 'border-neutral-100'}
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
          <View className="flex-row items-center gap-2">
            <View className={cn(
              "px-1.5 py-0.5 rounded-full",
              isBest ? "bg-primary-500" : "bg-slate-200"
            )}>
              <HeroText className={cn(
                "text-[8px] font-black uppercase",
                isBest ? "text-white" : "text-slate-600"
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
        {score && (
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
          isBest={isABest} 
          label={isABest ? 'Best Match' : 'Option 1'} 
        />
        <SummaryCard 
          item={stringB} 
          score={scoreB} 
          isBest={!isABest} 
          label={!isABest ? 'Option 2' : 'Option 1'} 
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
                <View className="w-2 h-2 rounded-full bg-slate-400" />
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
              <Info size={14} color="#3B82F6" className="mt-0.5" />
              <HeroText className="text-[11px] text-neutral-600 leading-relaxed italic">
                {stringA.ratings.power > stringB.ratings.power 
                  ? `${stringA.model} leads in power, while ${stringB.model} is stronger in ${stringB.ratings.durability > stringA.ratings.durability ? 'durability' : 'control'}.`
                  : `${stringB.model} leads in power, while ${stringA.model} is stronger in ${stringA.ratings.durability > stringB.ratings.durability ? 'durability' : 'control'}.`}
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
              { label: 'Rec. Tension', valA: `${stringA.recommendedTension[0]}–${stringA.recommendedTension[1]} lbs`, valB: `${stringB.recommendedTension[0]}–${stringB.recommendedTension[1]} lbs` },
              { label: 'Price', valA: stringA.price > 0 ? formatCurrency(stringA.price) : 'Price at shop', valB: stringB.price > 0 ? formatCurrency(stringB.price) : 'Price at shop' },
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

      {/* 4. Best For Section */}
      <AppSection eyebrow="Best For" title="Ideal playstyle" variant="compact">
        <View className="flex-row gap-3">
          <View className="flex-1">
            <AppCard variant="elevated" padding="sm" className="h-full">
              <HeroText className="text-[10px] font-bold text-primary-700 uppercase mb-2">{stringA.model}</HeroText>
              <View className="gap-1.5">
                {stringA.bestFor.map((item) => (
                  <View key={item} className="flex-row items-center gap-1.5">
                    <Target size={10} color="#3B82F6" />
                    <HeroText className="text-[11px] text-neutral-600">{item}</HeroText>
                  </View>
                ))}
              </View>
            </AppCard>
          </View>
          <View className="flex-1">
            <AppCard variant="elevated" padding="sm" className="h-full">
              <HeroText className="text-[10px] font-bold text-neutral-500 uppercase mb-2">{stringB.model}</HeroText>
              <View className="gap-1.5">
                {stringB.bestFor.map((item) => (
                  <View key={item} className="flex-row items-center gap-1.5">
                    <Target size={10} color="#94A3B8" />
                    <HeroText className="text-[11px] text-neutral-600">{item}</HeroText>
                  </View>
                ))}
              </View>
            </AppCard>
          </View>
        </View>
      </AppSection>

      {/* 5. Strengths Section */}
      <AppSection eyebrow="Strengths" title="Winning reasons" variant="compact">
        <View className="flex-row gap-3">
          <View className="flex-1">
            <View className="gap-2">
              {stringA.strengths.slice(0, 3).map((item) => (
                <View key={item} className="flex-row items-start gap-2 bg-primary-50 p-2 rounded-xl">
                  <ShieldCheck size={14} color="#3B82F6" className="mt-0.5" />
                  <HeroText className="text-[11px] font-medium text-primary-900 flex-1 leading-tight">{item}</HeroText>
                </View>
              ))}
            </View>
          </View>
          <View className="flex-1">
            <View className="gap-2">
              {stringB.strengths.slice(0, 3).map((item) => (
                <View key={item} className="flex-row items-start gap-2 bg-neutral-100 p-2 rounded-xl">
                  <ShieldCheck size={14} color="#64748B" className="mt-0.5" />
                  <HeroText className="text-[11px] font-medium text-neutral-900 flex-1 leading-tight">{item}</HeroText>
                </View>
              ))}
            </View>
          </View>
        </View>
      </AppSection>

      {/* 6. Trade-offs Section */}
      <AppSection eyebrow="Trade-offs" title="Watch-outs" variant="compact">
        <View className="gap-3">
          <AppCard variant="subtle" padding="sm">
            <HeroText className="text-[10px] font-bold text-neutral-400 uppercase mb-2">{stringA.model}</HeroText>
            {stringA.tradeOffs.map((item) => (
              <View key={item} className="flex-row items-start gap-2 mb-1.5">
                <AlertCircle size={12} color="#94A3B8" className="mt-0.5" />
                <HeroText className="text-[11px] text-neutral-600 flex-1">{item}</HeroText>
              </View>
            ))}
          </AppCard>
          <AppCard variant="subtle" padding="sm">
            <HeroText className="text-[10px] font-bold text-neutral-400 uppercase mb-2">{stringB.model}</HeroText>
            {stringB.tradeOffs.map((item) => (
              <View key={item} className="flex-row items-start gap-2 mb-1.5">
                <AlertCircle size={12} color="#94A3B8" className="mt-0.5" />
                <HeroText className="text-[11px] text-neutral-600 flex-1">{item}</HeroText>
              </View>
            ))}
          </AppCard>
        </View>
      </AppSection>

      {/* 7. Booking Fit Section */}
      <AppSection eyebrow="Booking Fit" title="Setup confidence" variant="compact">
        <AppCard variant="highlighted" padding="lg">
          <View className="flex-row items-center gap-3 mb-4">
            <View className="h-10 w-10 items-center justify-center rounded-xl bg-primary-100">
              <Zap size={20} color="#3B82F6" />
            </View>
            <View className="flex-1">
              <HeroText className="text-sm font-bold text-neutral-900">Recommended setup</HeroText>
              <HeroText className="text-xs text-neutral-500">Based on your recent playing history</HeroText>
            </View>
          </View>
          <HeroText className="text-[13px] text-neutral-700 leading-relaxed mb-4">
            {isABest 
              ? `${stringA.model} fits your current 24–29 lbs preference more directly and supports your aggressive style.`
              : `${stringB.model} supports your range but favors durability over rebound, ideal for long social sessions.`}
          </HeroText>
          <View className="bg-white/50 p-3 rounded-xl border border-primary-100">
            <HeroText className="text-[11px] font-bold text-primary-700 uppercase mb-1">Tension Note</HeroText>
            <HeroText className="text-xs text-neutral-600">{stringA.tensionNote}</HeroText>
          </View>
        </AppCard>
      </AppSection>

      {/* 8. CTA Area */}
      <View className="mt-8 mb-10 gap-4">
        <AppButton 
          label={`Book ${isABest ? stringA.model : stringB.model}`} 
          size="lg" 
          onPress={() => router.push(`/player/bookings/new?stringId=${isABest ? stringA.id : stringB.id}`)} 
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
