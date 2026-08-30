import React, { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, Scale } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { FloatingCompareTray } from '../../../components/shared/FloatingCompareTray';
import { StringProductImage } from '../../../components/shared/StringProductImage';
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
import { formatCurrency } from '../../../lib/formatters';

type AgentReasonState =
  | { status: 'loading' }
  | { status: 'ready'; text: string }
  | { status: 'error' };

function humanizeFeature(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export default function RecommendationResultsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const liveResults = useLiveRecommendationResults();
  const strings = useStrings();
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);
  const setLiveRecommendationResults = useAppStore(
    (state) => state.setLiveRecommendationResults,
  );
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);
  const compareSelection = useAppStore((state) => state.compareSelection);
  const [cacheError, setCacheError] = useState<string | null>(null);
  const [isLoadingCache, setIsLoadingCache] = useState(false);
  const [hasLoadedCache, setHasLoadedCache] = useState(false);
  const [agentReasons, setAgentReasons] = useState<Record<string, AgentReasonState>>({});
  const requestedAgentReasonKey = useRef<string | null>(null);

  useEffect(() => {
    if (!token) {
      setIsLoadingCache(false);
      setHasLoadedCache(false);
      return;
    }

    if (liveResults.length > 0) {
      setIsLoadingCache(false);
      setHasLoadedCache(true);
      return;
    }

    const accessToken = token;
    let isMounted = true;
    setIsLoadingCache(true);
    setHasLoadedCache(false);
    setCacheError(null);

    async function loadCachedResults() {
      try {
        const cachedStrings = useAppStore.getState().liveStrings;
        const availableStrings =
          cachedStrings.length > 0
            ? cachedStrings
            : (await backendApi.listStrings(accessToken)).items.map((item) =>
                mapBackendStringToStringItem(item),
              );
        const response = await backendApi.fetchCachedRecommendations(accessToken, 'me');
        if (!isMounted) {
          return;
        }
        if (cachedStrings.length === 0) {
          setLiveStrings(availableStrings);
        }
        setLiveRecommendationResults(
          mapRecommendationResponse(response, availableStrings),
        );
        setHasLoadedCache(true);
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setCacheError(
          error instanceof BackendApiError
            ? error.message
            : 'Unable to load cached recommendations.',
        );
        setHasLoadedCache(true);
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
    liveResults.length,
    setLiveRecommendationResults,
    setLiveStrings,
    token,
  ]);

  useEffect(() => {
    if (!token || liveResults.length === 0) {
      setAgentReasons({});
      requestedAgentReasonKey.current = null;
      return;
    }

    const candidates = liveResults
      .filter((item) => item.catalogId && item.runId)
      .slice(0, 3);
    if (candidates.length === 0) {
      setAgentReasons({});
      requestedAgentReasonKey.current = null;
      return;
    }

    const requestKey = candidates
      .map((item) => `${item.runId}:${item.catalogId}`)
      .join('|');
    if (requestedAgentReasonKey.current === requestKey) {
      return;
    }
    requestedAgentReasonKey.current = requestKey;

    const accessToken = token;
    let isMounted = true;
    setAgentReasons(
      Object.fromEntries(
        candidates.map((item) => [item.id, { status: 'loading' as const }]),
      ),
    );

    async function loadAgentReasons() {
      await Promise.all(
        candidates.map(async (item) => {
          try {
            const response = await backendApi.queryAgent(accessToken, {
              message:
                'In one short, player-friendly sentence, explain why the string in the supplied exact recommendation context fits this player. Mention the strongest supported benefit and, only if supported, one practical trade-off. Do not mention algorithms, scores, rankings, internal data, or that you are an AI.',
              context: {
                surface: 'recommendation_explanation',
                run_id: item.runId,
                catalog_id: item.catalogId,
              },
            });
            const text = response.summary.trim() || response.answer.trim();
            if (!isMounted) {
              return;
            }
            setAgentReasons((current) => ({
              ...current,
              [item.id]: text
                ? { status: 'ready', text }
                : { status: 'error' },
            }));
          } catch {
            if (isMounted) {
              setAgentReasons((current) => ({
                ...current,
                [item.id]: { status: 'error' },
              }));
            }
          }
        }),
      );
    }

    void loadAgentReasons();

    return () => {
      isMounted = false;
    };
  }, [liveResults, token]);

  if (!user || user.role !== 'player') {
    return null;
  }

  const isLive = Boolean(token);
  const hasResults = liveResults.length > 0;
  const isWaitingForInitialResults = isLive && !hasResults && (!hasLoadedCache || isLoadingCache);

  return (
    <View className="flex-1">
      <AppScreen
        headerVariant="primary"
        title="Your shortlist"
        subtitle="Start with the best fit, then open the evidence only when you need it."
      >
        {!isLive ? (
          <AppCard variant="subtle" className="mt-4" padding="lg">
            <HeroText className="text-lg font-bold text-neutral-900">
              Backend login required
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              This shortlist now only shows database-backed recommendations. Log in with a backend player account, then generate or load a saved shortlist.
            </HeroText>
            <AppButton
              label="Go to login"
              className="mt-6"
              onPress={() => router.replace('/auth/login')}
            />
          </AppCard>
        ) : isWaitingForInitialResults ? (
          <AppCard variant="subtle" className="mt-4" padding="lg">
            <HeroText className="text-lg font-bold text-neutral-900">
              Loading backend recommendations...
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              Pulling your saved shortlist and recommendation evidence from the database.
            </HeroText>
          </AppCard>
        ) : !hasResults ? (
          <AppCard variant="subtle" className="mt-4" padding="lg">
            <HeroText className="text-lg font-bold text-neutral-900">
              No backend results yet.
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
        ) : null}

        <AppSection eyebrow="PERSONALISED" title="Best matches">
          <View className="gap-3 pb-36">
            {hasResults &&
              liveResults.map((item, index) => {
                const isSelected = item.stringId ? compareSelection.includes(item.stringId) : false;
                const isTop = index === 0;
                const topAspectLabels = Object.entries(item.aspectScores)
                  .sort((left, right) => right[1] - left[1])
                  .slice(0, 2)
                  .map(([label]) => label.replace(/_/g, ' '));
                const fitAngle = item.fitAngle ?? `Rank #${index + 1}`;
                const stringItem = strings.find(
                  (string) => string.id === item.stringId,
                );
                const isOutOfStock = stringItem?.availability === 'out_of_stock';
                const explanationRoute = item.catalogId
                  ? `/player/recommend/explain/${item.catalogId}${item.runId ? `?runId=${item.runId}` : ''}`
                  : null;
                const agentReason = agentReasons[item.id];
                const reasonText =
                  agentReason?.status === 'ready'
                    ? agentReason.text
                    : agentReason?.status === 'loading'
                      ? 'Generating a tailored explanation...'
                      : item.reasons[0] ?? 'No saved recommendation reason was returned.';

                return (
                  <AppCard key={item.id} variant={isTop ? 'highlighted' : 'elevated'} padding="md" className="rounded-[30px]">
                    <View className="flex-row items-start gap-3">
                      <View className="h-[72px] w-[72px] overflow-hidden rounded-[16px] bg-neutral-950">
                        <StringProductImage
                          imageUrl={stringItem?.imageUrl}
                          brand={item.brand}
                          model={item.modelName}
                          gauge={stringItem?.gauge ?? 'String'}
                          className="h-[72px] w-[72px]"
                          fallbackClassName="h-[72px] w-[72px] rounded-[16px] border-0"
                          fallbackTextClassName="px-2 text-[11px] leading-[13px]"
                          fallbackGaugeClassName="mt-2 px-2 py-0.5"
                        />
                      </View>
                      <View className="min-w-0 flex-1">
                        <View className="flex-row items-center gap-2">
                          <AppChip 
                            label={fitAngle}
                            variant={isTop ? 'primary' : 'neutral'} 
                            size="sm"
                          />
                          {isOutOfStock ? (
                            <AppChip label="Out of stock" variant="warning" size="sm" />
                          ) : null}
                          <HeroText className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                            {item.brand}
                          </HeroText>
                        </View>
                        <HeroText className="mt-1.5 text-lg font-bold tracking-tight text-neutral-950">
                          {item.modelName}
                        </HeroText>
                        <HeroText className="mt-1 text-sm font-semibold text-primary-700">
                          {item.matchScore}% match • {item.price != null ? formatCurrency(item.price) : 'Price pending'}
                        </HeroText>
                      </View>
                      <View className="items-end gap-1">
                        <HeroText className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                          Rank
                        </HeroText>
                        <View className="rounded-xl bg-white/80 px-2.5 py-1.5">
                          <HeroText className="text-base font-black text-primary-700">
                            #{index + 1}
                          </HeroText>
                        </View>
                      </View>
                    </View>

                    <View className="mt-3 rounded-xl bg-white/70 p-2.5">
                      <HeroText className="text-[10px] font-bold uppercase tracking-widest text-primary-700">
                        Why this one
                      </HeroText>
                      <HeroText className="mt-1.5 text-sm leading-5 text-neutral-700">
                        {reasonText}
                      </HeroText>
                      {agentReason?.status === 'error' ? (
                        <HeroText className="mt-1 text-[11px] leading-4 text-neutral-500">
                          Showing the saved match reason while AI explanation is unavailable.
                        </HeroText>
                      ) : null}
                    </View>

                    <View className="mt-3 flex-row flex-wrap gap-1.5">
                      {topAspectLabels.map((label) => (
                        <AppChip key={label} label={humanizeFeature(label)} variant="primary" size="sm" />
                      ))}
                    </View>

                    <View className="mt-3 rounded-xl bg-neutral-50 px-3 py-1.5">
                      <HeroText className="text-xs text-neutral-500">
                        Suggested tension: <HeroText className="font-bold text-neutral-700">{item.suggestedTensionRange}</HeroText>
                      </HeroText>
                    </View>

                    <View className="mt-4 gap-2.5">
                      <AppButton
                        label={isOutOfStock ? 'Find in-stock alternatives' : 'Book this string'}
                        variant={isTop ? 'primary' : 'outline'}
                        size="md"
                        trailingIcon={isTop ? <ArrowRight size={16} color="white" /> : undefined}
                        isDisabled={isOutOfStock ? !item.runId || !explanationRoute : !item.stringId}
                        onPress={() => {
                          if (isOutOfStock && explanationRoute) {
                            router.push(explanationRoute);
                          } else if (item.stringId) {
                            router.push(`/player/bookings/new?stringId=${item.stringId}`);
                          }
                        }}
                      />
                      <View className="flex-row gap-3">
                        <AppButton
                          label="Why this fits"
                          variant="ghost"
                          size="sm"
                          className="flex-1"
                          isDisabled={!item.catalogId}
                          onPress={() => explanationRoute ? router.push(explanationRoute) : undefined}
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
