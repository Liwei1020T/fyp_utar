import React, { useCallback, useEffect, useState } from 'react';
import { Share, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { 
  Scale, 
  Share2, 
  Sparkles, 
  Zap, 
  ShieldCheck, 
  Volume2, 
  Heart,
  CheckCircle2,
  Target
} from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { AgentAnswerCard } from '../../../components/agent/AgentAnswerCard';
import { showAlert } from '../../../lib/alerts';
import { StringProductImage } from '../../../components/shared/StringProductImage';
import {
  useAppStore,
  useBackendAccessToken,
  useLiveRecommendationResults,
  useStrings,
} from '../../../store/appStore';
import { formatLabel } from '../../../lib/formatters';
import { formatTensionRange, getInventoryPriceLabel } from '../../../lib/inventory';
import { AppRadarChart } from '../../../components/ui/AppRadarChart';
import { CommunityFeatureList } from '../../../components/shared/CommunityFeatureList';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import type { BackendAgentAction, BackendAgentResponse, BackendCommunityStringSummary } from '../../../types/backend';

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

export default function StringDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const strings = useStrings();
  const selectedString = strings.find((item) => item.id === params.id);
  const token = useBackendAccessToken();
  const liveResults = useLiveRecommendationResults();
  const compareSelection = useAppStore((state) => state.compareSelection);
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);

  const [communitySummary, setCommunitySummary] = useState<
    BackendCommunityStringSummary | null
  >(null);
  const [isCommunityLoading, setIsCommunityLoading] = useState(Boolean(token));
  const [communityError, setCommunityError] = useState<string | null>(null);
  const [agentResponse, setAgentResponse] = useState<BackendAgentResponse | null>(null);
  const [isAgentLoading, setIsAgentLoading] = useState(Boolean(token));
  const [agentError, setAgentError] = useState<string | null>(null);

  const selectedStringId = selectedString?.id;
  const selectedStringLabel = selectedString
    ? `${selectedString.brand} ${selectedString.model}`
    : null;

  const loadCommunitySummary = useCallback(async () => {
    if (!token || !params.id) {
      setIsCommunityLoading(false);
      return;
    }

    setIsCommunityLoading(true);
    setCommunityError(null);
    try {
      const response = await backendApi.fetchCommunitySummary(token);
      setCommunitySummary(
        response.strings.find((item) => item.string_id === params.id) ?? null,
      );
    } catch (error) {
      setCommunityError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to load local player feedback.',
      );
    } finally {
      setIsCommunityLoading(false);
    }
  }, [params.id, token]);

  useFocusEffect(
    useCallback(() => {
      void loadCommunitySummary();
    }, [loadCommunitySummary]),
  );

  useEffect(() => {
    if (!token || !selectedStringId || !selectedStringLabel) {
      setIsAgentLoading(false);
      return;
    }

    let isMounted = true;
    setIsAgentLoading(true);
    setAgentError(null);
    setAgentResponse(null);

    void backendApi
      .queryAgent(token, {
        message: `Introduce ${selectedStringLabel} in simple player-friendly language. Explain what it is, its standout traits, who it may suit, and one practical trade-off. Use only verified catalog facts. Do not mention algorithms or internal data.`,
        context: { surface: 'chatbot', catalog_id: selectedStringId },
      })
      .then((response) => {
        if (isMounted) {
          setAgentResponse(response);
        }
      })
      .catch((error) => {
        if (isMounted) {
          setAgentError(
            error instanceof BackendApiError
              ? error.message
              : 'The AI introduction is temporarily unavailable.',
          );
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsAgentLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [selectedStringId, selectedStringLabel, token]);

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
  const tensionLabel = formatTensionRange(
    selectedString.tensionMinLbs,
    selectedString.tensionMaxLbs,
    'Tension guidance unavailable',
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
      showAlert('Share unavailable', 'This device could not open the share sheet for this item.');
    }
  };

  const handleAgentAction = (action: BackendAgentAction) => {
    if (action.action === 'open_string' && action.parameters.catalog_id) {
      router.push(`/player/strings/${action.parameters.catalog_id}`);
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
      <View className="items-center justify-center pb-2">
        <View className="w-full aspect-[3/2] items-center justify-center overflow-hidden rounded-[18px] border border-neutral-200/50 bg-neutral-50 shadow-sm">
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
      <AppCard variant="dark" className="overflow-hidden rounded-[22px]" padding="none">
        <View className="p-3">
          <View className="flex-row items-start justify-between">
            <View className="mr-2.5 flex-1">
              <HeroText className="text-[11px] font-bold uppercase tracking-[0.24em] text-secondary-100">
                {selectedString.brand}
              </HeroText>
              <HeroText className="mt-1 text-[26px] font-black tracking-tight text-white">
                {selectedString.model}
              </HeroText>
            </View>
            {liveResult && (
              <View className="flex-row items-center gap-1 rounded-full border border-white/12 bg-primary-600 px-2.5 py-1 shadow-soft">
                <Sparkles size={12} color="white" />
                <HeroText className="text-[10px] font-bold text-white uppercase tracking-wider">
                  {liveResult.matchScore.toFixed(0)}% MATCH
                </HeroText>
              </View>
            )}
          </View>

          <HeroText className="mt-2 text-[13px] leading-5 text-primary-100" numberOfLines={2}>
            {selectedString.description}
          </HeroText>

          <View className="mt-3 flex-row flex-wrap gap-1.5">
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
      <AppSection eyebrow="Specs" title="Technical profile" variant="compact" className="mt-2">
        <AppCard variant="elevated" padding="sm">
          <View className="flex-row flex-wrap">
            <View className="mb-2 w-1/2 pr-1.5">
              <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Gauge</HeroText>
              <HeroText className="mt-0.5 text-sm font-semibold text-neutral-900">{selectedString.gauge}</HeroText>
            </View>
            <View className="mb-2 w-1/2 pl-1.5">
              <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Material</HeroText>
              <HeroText className="mt-0.5 text-sm font-semibold text-neutral-900" numberOfLines={1}>{selectedString.material.split(' ')[0]}</HeroText>
            </View>
            <View className="w-1/2 pr-1.5">
              <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Category</HeroText>
              <HeroText className="mt-0.5 text-sm font-semibold text-neutral-900">{formatLabel(selectedString.category)}</HeroText>
            </View>
            <View className="w-1/2 pl-1.5">
              <HeroText className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Tension Fit</HeroText>
              <HeroText className="mt-0.5 text-sm font-semibold text-neutral-900">{tensionLabel}</HeroText>
            </View>
          </View>
        </AppCard>
      </AppSection>

      {/* 3. Performance Profile */}
      <AppSection eyebrow="Performance" title="Aspect profile" variant="compact" className="mt-2">
        <AppCard variant="elevated" padding="none" className="overflow-hidden">
          <AppRadarChart data={selectedString.ratings} size={260} />
          
          <View className="flex-row items-center gap-2 border-t border-neutral-100 bg-neutral-50 px-3 py-2.5">
            <Sparkles size={14} color="#3B82F6" />
            <HeroText className="text-sm font-medium text-neutral-600 italic flex-1">
              {getInsightSentence()}
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      {/* 4. Grounded Agent Introduction */}
      <AppSection
        eyebrow="StringSense AI"
        title="About this string"
        subtitle="A plain-language introduction from the verified catalog."
        variant="compact"
        className="mt-2"
      >
        {agentResponse ? (
          <AgentAnswerCard response={agentResponse} onAction={handleAgentAction} />
        ) : (
          <AppCard variant={agentError ? 'subtle' : 'highlighted'} padding="sm">
            <View className="flex-row items-start gap-2.5">
              <View className="h-9 w-9 items-center justify-center rounded-full bg-primary-100">
                <Sparkles size={17} color="#2563EB" />
              </View>
              <View className="flex-1">
                <HeroText className="text-sm font-bold text-neutral-900">
                  {isAgentLoading ? 'Preparing a simple introduction' : 'AI introduction unavailable'}
                </HeroText>
                <HeroText className="mt-0.5 text-xs leading-5 text-neutral-600">
                  {isAgentLoading
                    ? 'Reading the verified catalog details for this string.'
                    : agentError ?? 'The catalog summary above remains available.'}
                </HeroText>
              </View>
            </View>
          </AppCard>
        )}
      </AppSection>

      {/* 5. Community Intelligence (Combined NLP + Sentiment) */}
      <AppSection eyebrow="Community" title="Review intelligence" variant="compact" className="mt-2">
        <AppCard variant="elevated" padding="none" className="overflow-hidden">
          <View className="p-2.5">
            {evidenceSignals.length > 0 ? (
              <>
                <View className="mb-3 flex-row justify-between">
                  <View className="mr-2.5 flex-1">
                    <HeroText className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-neutral-400">Highest review signal</HeroText>
                    <HeroText className="text-sm font-bold text-neutral-900">{highlightedStrength}</HeroText>
                  </View>
                  <View className="flex-1">
                    <HeroText className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-neutral-400">Lowest recorded signal</HeroText>
                    <HeroText className="text-sm font-bold text-neutral-900">{highlightedTradeOff}</HeroText>
                  </View>
                </View>

                <HeroText className="mb-2.5 text-xs leading-5 text-neutral-500">
                  {reviewSummary}
                </HeroText>

                <View className="mb-3 flex-row flex-wrap gap-1.5">
                  {reviewThemes.map((theme) => (
                    <View key={theme} className="flex-row items-center gap-1.5 rounded-lg border border-neutral-100 bg-neutral-50 px-2.5 py-1">
                      <CheckCircle2 size={12} color="#10B981" />
                      <HeroText className="text-[11px] font-bold text-neutral-700 uppercase">{theme}</HeroText>
                    </View>
                  ))}
                </View>

                <HeroText className="mb-2.5 text-[10px] font-bold uppercase tracking-wider text-neutral-400">Review-derived aspect signal</HeroText>
                <View className="flex-row flex-wrap gap-2">
                  {sentimentSignals.map((item) => (
                    <View key={item.aspect} className={`${getSentimentBg(item.sentiment)} flex-row items-center gap-1.5 rounded-full border border-neutral-100 px-2.5 py-1`}>
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

      <AppSection
        eyebrow="Community"
        title="Local player feedback"
        subtitle="Verified completed bookings only. These ratings calibrate future recommendations without replacing official specifications."
        variant="compact"
        className="mt-2"
      >
        <AppCard variant="elevated" padding="sm">
          {isCommunityLoading ? (
            <HeroText className="text-sm text-neutral-600">
              Loading local feedback evidence...
            </HeroText>
          ) : communityError ? (
            <View className="gap-3">
              <HeroText
                selectable
                accessibilityLiveRegion="polite"
                className="text-sm leading-6 text-red-700"
              >
                {communityError}
              </HeroText>
              <AppButton
                label="Try again"
                variant="outline"
                size="sm"
                onPress={() => void loadCommunitySummary()}
              />
            </View>
          ) : communitySummary && Object.keys(communitySummary.features).length > 0 ? (
            <CommunityFeatureList features={communitySummary.features} />
          ) : (
            <HeroText className="text-sm leading-6 text-neutral-600">
              No eligible local ratings yet. This string continues using its official and reviewed baseline.
            </HeroText>
          )}
        </AppCard>
      </AppSection>

      {/* 8. Sticky CTA Area */}
      <View className="mb-8 mt-6 flex-row gap-2.5">
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
