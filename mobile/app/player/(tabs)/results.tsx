import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, Scale, Sparkles } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { FloatingCompareTray } from '../../../components/shared/FloatingCompareTray';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useLiveRecommendationResults,
  useStrings,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  mapBackendStringToStringItem,
  mapRecommendationResponse,
} from '../../../services/backendMappers';

function formatScore(value?: number) {
  if (value == null) {
    return '—';
  }
  return `${Math.round(value * 100)}%`;
}

function humanizeFeature(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function ScoreMeter({
  label,
  value,
  tone = 'primary',
}: {
  label: string;
  value?: number;
  tone?: 'primary' | 'accent' | 'neutral';
}) {
  const percent = value == null ? 0 : Math.max(0, Math.min(100, Math.round(value * 100)));
  const fillClassName =
    tone === 'accent'
      ? 'bg-accent-500'
      : tone === 'neutral'
        ? 'bg-neutral-500'
        : 'bg-primary-600';

  return (
    <View className="flex-1 min-w-[92px]">
      <View className="flex-row items-center justify-between">
        <HeroText className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
          {label}
        </HeroText>
        <HeroText className="text-xs font-black text-neutral-800">
          {formatScore(value)}
        </HeroText>
      </View>
      <View className="mt-2 h-2 overflow-hidden rounded-full bg-white">
        <View className={`h-full rounded-full ${fillClassName}`} style={{ width: `${percent}%` }} />
      </View>
    </View>
  );
}

export default function RecommendationResultsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const liveResults = useLiveRecommendationResults();
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);
  const setLiveRecommendationResults = useAppStore(
    (state) => state.setLiveRecommendationResults,
  );
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);
  const compareSelection = useAppStore((state) => state.compareSelection);
  const [cacheError, setCacheError] = useState<string | null>(null);
  const [isLoadingCache, setIsLoadingCache] = useState(false);

  useEffect(() => {
    if (!token || liveResults.length > 0 || isLoadingCache || cacheError) {
      return;
    }

    const accessToken = token;
    let isMounted = true;
    setIsLoadingCache(true);
    setCacheError(null);

    async function loadCachedResults() {
      try {
        const availableStrings =
          strings.length > 0
            ? strings
            : (await backendApi.listStrings(accessToken)).items.map((item) =>
                mapBackendStringToStringItem(item),
              );
        if (!isMounted) {
          return;
        }
        if (strings.length === 0) {
          setLiveStrings(availableStrings);
        }
        const response = await backendApi.fetchCachedRecommendations(accessToken, 'me');
        if (!isMounted) {
          return;
        }
        setLiveRecommendationResults(
          mapRecommendationResponse(response, availableStrings),
        );
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setCacheError(
          error instanceof BackendApiError
            ? error.message
            : 'Unable to load cached recommendations.',
        );
      } finally {
        if (isMounted) {
          setIsLoadingCache(false);
        }
      }
    }

    void loadCachedResults();

    return () => {
      isMounted = false;
    };
  }, [
    cacheError,
    isLoadingCache,
    liveResults.length,
    setLiveRecommendationResults,
    setLiveStrings,
    strings,
    token,
  ]);

  if (!user || user.role !== 'player') {
    return null;
  }

  const isLive = Boolean(token);
  const algorithmVersion = liveResults[0]?.algorithmVersion;
  const hasResults = liveResults.length > 0;

  return (
    <View className="flex-1">
      <AppScreen
        headerVariant="primary"
        title="AI Shortlist"
        subtitle="Preference-led picks with rules, budget, and review evidence separated."
      >
        {!isLive ? (
          <AppCard variant="subtle" className="mt-6" padding="lg">
            <HeroText className="text-lg font-bold text-neutral-900">
              Backend login required
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              This shortlist now only shows database-backed recommendations. Log in with a backend player account, then generate or load a saved shortlist.
            </HeroText>
            <AppButton
              label="Go to login"
              className="mt-6"
              onPress={() => router.replace('/auth/login?role=player')}
            />
          </AppCard>
        ) : !hasResults ? (
          <AppCard variant="subtle" className="mt-6" padding="lg">
            <HeroText className="text-lg font-bold text-neutral-900">
              {isLoadingCache ? 'Loading cached recommendations...' : 'No backend results yet.'}
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              {cacheError ?? 'Generate a shortlist from the recommendation lab to see ranked results here.'}
            </HeroText>
            <AppButton
              label="Back to recommendation lab"
              className="mt-6"
              onPress={() => router.replace('/player/recommend')}
            />
          </AppCard>
        ) : (
          <AppCard variant="subtle" className="mb-6 rounded-2xl border border-primary-100" padding="md">
            <View className="flex-row items-center gap-3">
              <View className="h-10 w-10 items-center justify-center rounded-full bg-primary-100">
                <Sparkles size={20} color="#2F64B6" />
              </View>
              <View className="flex-1">
                <HeroText className="text-base font-bold text-neutral-900">
                  Backend recommendation ready
                </HeroText>
                <HeroText className="text-xs text-neutral-500" numberOfLines={1}>
                  {`${liveResults.length} ranked strings · NLP folded into Preference`}
                </HeroText>
                {algorithmVersion ? (
                  <HeroText className="mt-1 text-[10px] font-bold uppercase tracking-widest text-primary-600">
                    {algorithmVersion}
                  </HeroText>
                ) : null}
              </View>
            </View>
          </AppCard>
        )}

        <AppSection eyebrow="Ranked shortlist" title="Decision cards">
          <View className="gap-5 pb-10">
            {hasResults &&
              liveResults.map((item, index) => {
                const isSelected = item.stringId ? compareSelection.includes(item.stringId) : false;
                const isTop = index === 0;
                const topAspectLabels = Object.entries(item.aspectScores)
                  .sort((left, right) => right[1] - left[1])
                  .slice(0, 2)
                  .map(([label]) => label.replace(/_/g, ' '));
                const nlpEvidenceCount = Object.keys(
                  item.rationalePayload?.nlp_review_scores ?? {},
                ).length;
                const fitAngle = item.fitAngle ?? (isTop ? 'Best match' : `Option ${index + 1}`);
                const tradeOff =
                  item.tradeOffSummary ??
                  'Balanced against your saved profile, price range, and available review signals.';

                return (
                  <AppCard key={item.id} variant={isTop ? 'highlighted' : 'elevated'} padding="md" className="rounded-[30px]">
                    <View className="flex-row items-start justify-between">
                      <View className="flex-1">
                        <View className="flex-row items-center gap-2">
                          <AppChip 
                            label={fitAngle}
                            variant={isTop ? 'primary' : 'neutral'} 
                            size="sm"
                          />
                          <HeroText className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                            {item.brand}
                          </HeroText>
                        </View>
                        <HeroText className="mt-2 text-xl font-bold tracking-tight text-neutral-950">
                          {item.modelName}
                        </HeroText>
                        <HeroText className="mt-1 text-sm font-semibold text-primary-700">
                          {item.matchScore}% match
                        </HeroText>
                      </View>
                      <View className="items-end rounded-2xl bg-white/80 px-3 py-2">
                        <HeroText className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                          Rank
                        </HeroText>
                        <HeroText className="text-lg font-black text-primary-700">
                          #{index + 1}
                        </HeroText>
                      </View>
                    </View>

                    <View className="mt-4 rounded-2xl bg-white/70 p-3">
                      <HeroText className="text-[10px] font-bold uppercase tracking-widest text-primary-700">
                        Why this one
                      </HeroText>
                      <HeroText className="mt-2 text-sm leading-5 text-neutral-700">
                        {item.reasons[0] ?? 'Ranked highly for your saved player profile.'}
                      </HeroText>
                      <View className="mt-3 h-px bg-neutral-200" />
                      <HeroText className="mt-3 text-sm leading-5 text-neutral-600">
                        <HeroText className="font-bold text-neutral-800">Trade-off:</HeroText> {tradeOff}
                      </HeroText>
                    </View>

                    {item.scoreBreakdown ? (
                      <View className="mt-4 rounded-2xl border border-primary-100 bg-primary-50/70 p-4">
                        <View className="flex-row items-center justify-between">
                          <HeroText className="text-[10px] font-bold uppercase tracking-[0.18em] text-primary-700">
                            Score model
                          </HeroText>
                          <AppChip label="NLP inside Preference" variant="info" size="sm" />
                        </View>
                        <View className="mt-4 flex-row flex-wrap gap-3">
                          <ScoreMeter
                            label="Preference"
                            value={item.scoreBreakdown.preferenceMatch}
                            tone="primary"
                          />
                          <ScoreMeter
                            label="Rule"
                            value={item.scoreBreakdown.ruleFit}
                            tone="accent"
                          />
                          <ScoreMeter
                            label="Budget"
                            value={item.scoreBreakdown.budgetFit}
                            tone="neutral"
                          />
                        </View>
                        <HeroText className="mt-3 text-xs leading-5 text-neutral-500">
                          {nlpEvidenceCount > 0
                            ? `${nlpEvidenceCount} review-derived signals are blended into Preference Match.`
                            : 'Preference Match can still use official/manual values when review signals are missing.'}
                        </HeroText>
                      </View>
                    ) : null}

                    <View className="mt-4 flex-row flex-wrap gap-2">
                      {topAspectLabels.map((label) => (
                        <AppChip key={label} label={humanizeFeature(label)} variant="primary" size="sm" />
                      ))}
                    </View>

                    <View className="mt-4 rounded-xl bg-neutral-50 px-3 py-2">
                      <HeroText className="text-xs text-neutral-500">
                        Suggested tension: <HeroText className="font-bold text-neutral-700">{item.suggestedTensionRange}</HeroText>
                      </HeroText>
                    </View>

                    <View className="mt-5 gap-3">
                      <AppButton
                        label="Book this string"
                        variant={isTop ? 'primary' : 'outline'}
                        size="md"
                        trailingIcon={isTop ? <ArrowRight size={16} color="white" /> : undefined}
                        isDisabled={!item.stringId}
                        onPress={() => item.stringId ? router.push(`/player/bookings/new?stringId=${item.stringId}`) : undefined}
                      />
                      <View className="flex-row gap-3">
                        <AppButton
                          label="Explain fit"
                          variant="ghost"
                          size="sm"
                          className="flex-1"
                          isDisabled={!item.catalogId}
                          onPress={() => item.catalogId ? router.push(`/player/recommend/explain/${item.catalogId}`) : undefined}
                        />
                        <AppButton
                          label={isSelected ? 'Selected' : 'Compare'}
                          variant={isSelected ? 'secondary' : 'ghost'}
                          size="sm"
                          className="flex-1"
                          leadingIcon={<Scale size={14} color={isSelected ? '#2F64B6' : '#64748b'} />}
                          isDisabled={!item.stringId}
                          onPress={() => item.stringId && toggleCompareSelection(item.stringId)}
                        />
                      </View>
                    </View>
                  </AppCard>
                );
              })}
          </View>
        </AppSection>
      </AppScreen>

      <FloatingCompareTray />
    </View>
  );
}
