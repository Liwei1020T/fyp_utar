import React, { useState } from 'react';
import { Alert, Share, View, Pressable } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { 
  Scale, 
  Share2, 
  Sparkles, 
  TrendingUp, 
  Zap, 
  ShieldCheck, 
  Volume2, 
  Heart,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  BrainCircuit,
  Target
} from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { StringProductImage } from '../../../components/shared/StringProductImage';
import {
  useAppStore,
  useCurrentUser,
  useLiveRecommendationResults,
  useStrings,
} from '../../../store/appStore';
import { formatLabel } from '../../../lib/formatters';
import { formatTensionRange, getInventoryPriceLabel } from '../../../lib/inventory';
import { AppRadarChart } from '../../../components/ui/AppRadarChart';

const FEATURE_LABELS: Record<string, string> = {
  attack: 'Power',
  repulsion: 'Power',
  control: 'Control',
  durability: 'Durability',
  comfort: 'Comfort',
  sound: 'Sound',
  elasticity: 'Elasticity',
  string_movement: 'String movement',
  tension_retention: 'Tension retention',
  hitting_sound: 'Sound',
};

function toAspectLabel(featureKey?: string, displayLabel?: string) {
  if (displayLabel && displayLabel.trim().length > 0) {
    return displayLabel;
  }

  if (!featureKey) {
    return 'Community signal';
  }

  const normalized = featureKey.toLowerCase();
  const mapped = FEATURE_LABELS[normalized];

  if (mapped) {
    return mapped;
  }

  return normalized
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function toSentiment(score?: number | null): 'Positive' | 'Mixed' | 'Neutral' {
  if (score == null) {
    return 'Neutral';
  }

  if (score >= 0.65) {
    return 'Positive';
  }

  if (score >= 0.45) {
    return 'Mixed';
  }

  return 'Neutral';
}

function describeTensionFit(
  minimum: number | null,
  maximum: number | null,
  preferred: number | undefined,
) {
  if (minimum == null || maximum == null) {
    return 'No catalog tension range is recorded for this string.';
  }

  const range = formatTensionRange(minimum, maximum);
  if (preferred == null) {
    return `The recorded catalog range is ${range}.`;
  }

  const relation = preferred >= minimum && preferred <= maximum
    ? 'inside'
    : 'outside';
  return `${preferred} lbs is ${relation} the recorded ${range} catalog range.`;
}

export default function StringDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const strings = useStrings();
  const selectedString = strings.find((item) => item.id === params.id);
  const user = useCurrentUser();
  const playerUser = user?.role === 'player' ? user : null;
  const liveResults = useLiveRecommendationResults();
  const compareSelection = useAppStore((state) => state.compareSelection);
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);

  const [isExplainOpen, setIsExplainOpen] = useState(false);

  if (!selectedString) {
    return (
      <AppScreen title="String not found">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            This string is no longer available.
          </HeroText>
          <AppButton label="Back to catalog" className="mt-6" onPress={() => router.replace('/player/strings')} />
        </AppCard>
      </AppScreen>
    );
  }

  const liveResult = liveResults.find(
    (item) => item.stringId === selectedString.id
  );
  const rationale = liveResult?.rationalePayload ?? null;

  const isSelected = compareSelection.includes(selectedString.id);
  
  const performanceMetrics = [
    { key: 'power', label: 'Power', icon: <Zap size={16} color="#F59E0B" />, value: selectedString.ratings.power },
    { key: 'control', label: 'Control', icon: <Target size={16} color="#3B82F6" />, value: selectedString.ratings.control },
    { key: 'durability', label: 'Durability', icon: <ShieldCheck size={16} color="#10B981" />, value: selectedString.ratings.durability },
    { key: 'comfort', label: 'Comfort', icon: <Heart size={16} color="#EC4899" />, value: selectedString.ratings.comfort },
    { key: 'sound', label: 'Sound', icon: <Volume2 size={16} color="#8B5CF6" />, value: selectedString.ratings.sound },
  ];
  const sortedPerformanceMetrics = [...performanceMetrics].sort((a, b) => b.value - a.value);

  const evidenceSignals = (rationale?.feature_evidence ?? []).reduce<
    { label: string; score: number }[]
  >((acc, entry) => {
    const score = entry.nlp_review_score ?? null;

    if (score == null) {
      return acc;
    }

    acc.push({
      label: toAspectLabel(entry.feature_key, entry.display_label),
      score,
    });

    return acc;
  }, []).sort((left, right) => right.score - left.score);

  const sentimentSignals = evidenceSignals.reduce<
    { aspect: string; sentiment: 'Positive' | 'Mixed' | 'Neutral' }[]
  >((acc, item) => {
    if (acc.some((entry) => entry.aspect === item.label)) {
      return acc;
    }

    acc.push({
      aspect: item.label,
      sentiment: toSentiment(item.score),
    });

    return acc;
  }, []).slice(0, 5);

  const reviewThemes = evidenceSignals
    .slice(0, 2)
    .map((item) => `${item.label} review signal`);
  const highlightedStrength = evidenceSignals[0]?.label ?? 'Not established';
  const highlightedTradeOff =
    evidenceSignals.length > 1
      ? evidenceSignals[evidenceSignals.length - 1]?.label
      : 'Not established';
  const reviewSummary =
    rationale?.nlp_review_summary ??
    'No review-derived evidence is available for this item.';
  const scorerReasons = rationale?.top_reasons ?? liveResult?.reasons ?? [];
  const savedTradeOff =
    rationale?.trade_off_summary ?? liveResult?.tradeOffSummary ?? null;
  const savedReasoningParagraphs = [
    ...scorerReasons.slice(0, 2),
    rationale?.nlp_review_summary ?? null,
    savedTradeOff,
  ].filter((paragraph): paragraph is string => Boolean(paragraph?.trim()));
  const deepReasoningParagraphs = savedReasoningParagraphs.length > 0
    ? savedReasoningParagraphs
    : ['No saved recommendation rationale is available for this catalog view.'];

  const tensionLabel = formatTensionRange(
    selectedString.tensionMinLbs,
    selectedString.tensionMaxLbs,
    'Tension guidance unavailable',
  );
  const preferredTension = playerUser?.preferredTension;
  const tensionFitCopy = describeTensionFit(
    selectedString.tensionMinLbs,
    selectedString.tensionMaxLbs,
    preferredTension,
  );
  const priceLabel = getInventoryPriceLabel(selectedString).label;

  const getInsightSentence = () => {
    const top = sortedPerformanceMetrics.slice(0, 2).map((metric) => metric.label.toLowerCase());
    return `${top[0].charAt(0).toUpperCase() + top[0].slice(1)} and ${top[1]} are the highest catalog performance scores for this string.`;
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: [
          `${selectedString.brand} ${selectedString.model}`,
          `${priceLabel} • ${selectedString.gauge} • ${formatLabel(selectedString.category)}`,
          `Catalog tension: ${tensionLabel}`,
          selectedString.description,
        ].join('\n'),
      });
    } catch {
      Alert.alert('Share unavailable', 'This device could not open the share sheet for this item.');
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'Positive': return 'text-green-600';
      case 'Mixed': return 'text-amber-600';
      case 'Neutral': return 'text-neutral-500';
      default: return 'text-neutral-500';
    }
  };

  const getSentimentBg = (sentiment: string) => {
    switch (sentiment) {
      case 'Positive': return 'bg-green-50';
      case 'Mixed': return 'bg-amber-50';
      case 'Neutral': return 'bg-neutral-50';
      default: return 'bg-neutral-50';
    }
  };

  return (
    <AppScreen
      headerVariant="secondary"
      title={`${selectedString.brand} ${selectedString.model}`}
      showBackButton
      onBackPress={() => router.back()}
      headerRight={
        <AppIconButton
          icon={<Share2 size={20} color="#475569" />}
          accessibilityLabel={`Share ${selectedString.brand} ${selectedString.model}`}
          onPress={handleShare}
        />
      }
    >
      {/* 0. Product Visual Section */}
      <View className="items-center justify-center pt-2 pb-8">
        <View className="w-full aspect-[4/3] bg-neutral-50 rounded-[40px] items-center justify-center overflow-hidden border border-neutral-200/50 shadow-sm">
          <StringProductImage
            imageUrl={selectedString.imageUrl}
            brand={selectedString.brand}
            model={selectedString.model}
            gauge={selectedString.gauge}
            className="h-full w-full"
            fallbackClassName="h-60 w-48"
            resizeMode="contain"
          />
        </View>
      </View>

      {/* 1. Hero Summary */}
      <AppCard variant="dark" className="rounded-[32px] overflow-hidden" padding="none">
        <View className="p-6">
          <View className="flex-row justify-between items-start">
            <View className="flex-1 mr-4">
              <HeroText className="text-[11px] font-bold uppercase tracking-[0.24em] text-secondary-100">
                {selectedString.brand}
              </HeroText>
              <HeroText className="mt-1 text-[32px] font-black tracking-tight text-white">
                {selectedString.model}
              </HeroText>
            </View>
            {liveResult && (
              <View className="rounded-full border border-white/12 bg-primary-600 px-3 py-1.5 flex-row items-center gap-1.5 shadow-soft">
                <Sparkles size={12} color="white" />
                <HeroText className="text-[10px] font-bold text-white uppercase tracking-wider">
                  {liveResult.matchScore.toFixed(0)}% MATCH
                </HeroText>
              </View>
            )}
          </View>

          <HeroText className="mt-4 text-[13px] leading-5 text-primary-100" numberOfLines={2}>
            {selectedString.description}
          </HeroText>

          <View className="mt-6 flex-row flex-wrap gap-2">
            <AppChip
              label={formatLabel(selectedString.category)}
              variant="neutral"
              className="border-white/18 bg-white/14"
              textClassName="text-white font-semibold text-xs"
            />
            <AppChip
              label={selectedString.gauge}
              variant="neutral"
              className="border-white/18 bg-white/14"
              textClassName="text-white font-semibold text-xs"
            />
            <AppChip
              label={tensionLabel}
              variant="neutral"
              className="border-white/18 bg-white/14"
              textClassName="text-white font-semibold text-xs"
            />
          </View>
        </View>
      </AppCard>

      {/* 2. Specs - 2x2 scannable grid */}
      <AppSection eyebrow="Specs" title="Technical profile" variant="compact">
        <AppCard variant="elevated" padding="md">
          <View className="flex-row flex-wrap">
            <View className="w-1/2 mb-4 pr-2">
              <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Gauge</HeroText>
              <HeroText className="text-sm font-semibold text-neutral-900 mt-1">{selectedString.gauge}</HeroText>
            </View>
            <View className="w-1/2 mb-4 pl-2">
              <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Material</HeroText>
              <HeroText className="text-sm font-semibold text-neutral-900 mt-1" numberOfLines={1}>{selectedString.material.split(' ')[0]}</HeroText>
            </View>
            <View className="w-1/2 pr-2">
              <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Category</HeroText>
              <HeroText className="text-sm font-semibold text-neutral-900 mt-1">{formatLabel(selectedString.category)}</HeroText>
            </View>
            <View className="w-1/2 pl-2">
              <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Tension Fit</HeroText>
              <HeroText className="text-sm font-semibold text-neutral-900 mt-1">{tensionLabel}</HeroText>
            </View>
          </View>
        </AppCard>
      </AppSection>

      {/* 3. Performance Profile */}
      <AppSection eyebrow="Performance" title="Aspect profile" variant="compact">
        <AppCard variant="elevated" padding="none" className="overflow-hidden">
          <AppRadarChart data={selectedString.ratings} />
          
          <View className="bg-neutral-50 px-5 py-4 border-t border-neutral-100 flex-row items-center gap-2.5">
            <Sparkles size={16} color="#3B82F6" />
            <HeroText className="text-sm font-medium text-neutral-600 italic flex-1">
              {getInsightSentence()}
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      {/* 4. The Match Logic (Combined Why + Explain) */}
      <AppSection 
        eyebrow="Intelligence" 
        title="The match logic" 
        variant="compact"
        rightAction={
          <View className="bg-primary-100 px-2.5 py-1 rounded-md flex-row items-center gap-1.5">
            <BrainCircuit size={12} color="#1E3A8A" />
            <HeroText className="text-[10px] font-bold text-primary-900 uppercase">
              {liveResult ? 'SAVED SCORING' : 'CATALOG ONLY'}
            </HeroText>
          </View>
        }
      >
        <AppCard variant="highlighted" padding="none" className="border-primary-100 bg-primary-50/20 overflow-hidden">
          <View className="p-5 gap-5">
            <View className="flex-row gap-4 items-start">
              <View className="p-2.5 bg-blue-50 rounded-xl border border-blue-100 items-center justify-center">
                <TrendingUp size={18} color="#059669" />
              </View>
              <View className="flex-1">
                <HeroText className="text-sm font-bold text-neutral-900">Saved scorer reason</HeroText>
                <HeroText className="text-xs leading-5 text-neutral-600 mt-1">
                  {scorerReasons[0] ?? 'No personalized scorer reason is available for this catalog view.'}
                </HeroText>
              </View>
            </View>

            <View className="flex-row gap-4 items-start">
              <View className="p-2.5 bg-blue-50 rounded-xl border border-blue-100 items-center justify-center">
                <Zap size={18} color="#2563EB" />
              </View>
              <View className="flex-1">
                <HeroText className="text-sm font-bold text-neutral-900">Priority Alignment</HeroText>
                <HeroText className="text-xs leading-5 text-neutral-600 mt-1">
                  {scorerReasons[1] ?? 'No separate priority-alignment reason was saved.'}
                </HeroText>
              </View>
            </View>

            <View className="flex-row gap-4 items-start">
              <View className="p-2.5 bg-blue-50 rounded-xl border border-blue-100 items-center justify-center">
                <Target size={18} color="#3B82F6" />
              </View>
              <View className="flex-1">
                <HeroText className="text-sm font-bold text-neutral-900">Tension Fit</HeroText>
                <HeroText className="text-xs leading-5 text-neutral-600 mt-1">
                  {tensionFitCopy}
                </HeroText>
              </View>
            </View>
          </View>

          <Pressable 
            accessibilityRole="button"
            accessibilityLabel={isExplainOpen ? 'Hide deep reasoning' : 'Show deep reasoning'}
            accessibilityState={{ expanded: isExplainOpen }}
            onPress={() => setIsExplainOpen(!isExplainOpen)}
            className="bg-white border-t border-primary-100 p-4 flex-row items-center justify-between"
          >
            <View className="flex-row items-center gap-2">
              <Sparkles size={14} color="#3B82F6" />
              <HeroText className="text-sm font-bold text-primary-700">Deep Reasoning</HeroText>
            </View>
            {isExplainOpen ? <ChevronUp size={18} color="#3B82F6" /> : <ChevronDown size={18} color="#3B82F6" />}
          </Pressable>
          
          {isExplainOpen && (
            <View className="bg-white px-5 pb-6 pt-2">
              {deepReasoningParagraphs.map((paragraph, index) => (
                <HeroText
                  key={`${paragraph}-${index}`}
                  className={`text-sm leading-6 text-neutral-700 ${index > 0 ? 'mt-4' : ''}`}
                >
                  {paragraph}
                </HeroText>
              ))}
            </View>
          )}
        </AppCard>
      </AppSection>

      {/* 5. Community Intelligence (Combined NLP + Sentiment) */}
      <AppSection eyebrow="Community" title="Review intelligence" variant="compact">
        <AppCard variant="elevated" padding="none" className="overflow-hidden">
          <View className="p-5">
            {evidenceSignals.length > 0 ? (
              <>
                <View className="flex-row justify-between mb-6">
                  <View className="flex-1 mr-4">
                    <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider mb-2">Highest review signal</HeroText>
                    <HeroText className="text-sm font-bold text-neutral-900">{highlightedStrength}</HeroText>
                  </View>
                  <View className="flex-1">
                    <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider mb-2">Lowest recorded signal</HeroText>
                    <HeroText className="text-sm font-bold text-neutral-900">{highlightedTradeOff}</HeroText>
                  </View>
                </View>

                <HeroText className="mb-4 text-xs leading-5 text-neutral-500">
                  {reviewSummary}
                </HeroText>

                <View className="flex-row flex-wrap gap-2 mb-6">
                  {reviewThemes.map((theme) => (
                    <View key={theme} className="bg-neutral-50 px-3 py-1.5 rounded-lg border border-neutral-100 flex-row items-center gap-1.5">
                      <CheckCircle2 size={12} color="#10B981" />
                      <HeroText className="text-[11px] font-bold text-neutral-700 uppercase">{theme}</HeroText>
                    </View>
                  ))}
                </View>

                <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider mb-3">Review-derived aspect signal</HeroText>
                <View className="flex-row flex-wrap gap-2">
                  {sentimentSignals.map((item) => (
                    <View key={item.aspect} className={`${getSentimentBg(item.sentiment)} px-3 py-1.5 rounded-full border border-neutral-100 flex-row items-center gap-1.5`}>
                      <View className={`h-1.5 w-1.5 rounded-full ${item.sentiment === 'Positive' ? 'bg-green-500' : item.sentiment === 'Mixed' ? 'bg-amber-500' : 'bg-neutral-300'}`} />
                      <HeroText className={`text-[10px] font-bold ${getSentimentColor(item.sentiment)}`}>
                        {item.aspect.toUpperCase()}: {item.sentiment.toUpperCase()}
                      </HeroText>
                    </View>
                  ))}
                </View>
              </>
            ) : (
              <HeroText className="text-sm leading-6 text-neutral-600">
                No review-derived evidence is available for this item. Catalog scores are shown separately above.
              </HeroText>
            )}
          </View>
        </AppCard>
      </AppSection>

      {/* 8. Sticky CTA Area */}
      <View className="mb-12 mt-10 flex-row gap-3">
        <AppButton
          label="Book this string"
          className="flex-[2.5]"
          size="lg"
          onPress={() => router.push(`/player/bookings/new?stringId=${selectedString.id}`)}
        />
        <AppButton
          label="Compare"
          variant={isSelected ? 'secondary' : 'outline'}
          size="lg"
          className="flex-1"
          leadingIcon={<Scale size={16} color={isSelected ? '#78350F' : '#475569'} />}
          onPress={() => toggleCompareSelection(selectedString.id)}
        />
      </View>
    </AppScreen>
  );
}
