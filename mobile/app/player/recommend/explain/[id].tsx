import React, { useCallback, useEffect, useRef, useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import {
  SendHorizontal,
  Target,
  WalletCards,
} from 'lucide-react-native';
import { HeroText } from '../../../../components/ui/heroui';
import { agentResponseToHistoryContent } from '../../../../lib/agentHistory';
import { AgentAnswerCard } from '../../../../components/agent/AgentAnswerCard';
import { AppButton } from '../../../../components/ui/AppButton';
import { AppCard } from '../../../../components/ui/AppCard';
import { AppChip } from '../../../../components/ui/AppChip';
import { AppInput } from '../../../../components/ui/AppInput';
import { AppScreen } from '../../../../components/shared/AppScreen';
import { AppSection } from '../../../../components/shared/AppSection';
import { formatLabel } from '../../../../lib/formatters';
import { getInventoryPriceLabel } from '../../../../lib/inventory';
import {
  useBackendAccessToken,
  useCurrentUser,
  useLiveRecommendationResults,
  useStrings,
} from '../../../../store/appStore';
import { BackendApiError, backendApi } from '../../../../services/backendApi';
import type {
  BackendAgentAction,
  BackendAgentMessage,
  BackendAgentResponse,
  BackendRecommendationResult,
} from '../../../../types/backend';

function humanizeFeature(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function compactSentence(value: string) {
  return value.trim().replace(/\.$/, '');
}

function formatExperienceScope(value?: string | null) {
  if (value === 'same_racket') {
    return 'from this exact racket';
  }
  if (value === 'same_racket_model') {
    return 'from this racket model';
  }
  return 'from your completed string bookings';
}

function formatRating(value?: number | null) {
  return value == null ? null : `${value.toFixed(1)}/5`;
}

function formatPercent(value?: number | null) {
  return value == null ? null : `${Math.round(value * 100)}%`;
}

export default function RecommendationExplanationScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string; runId?: string }>();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const liveResults = useLiveRecommendationResults();
  const [backendDetail, setBackendDetail] = useState<BackendRecommendationResult | null>(null);
  const [detailRunId, setDetailRunId] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [agentResponse, setAgentResponse] = useState<BackendAgentResponse | null>(null);
  const [agentHistory, setAgentHistory] = useState<BackendAgentMessage[]>([]);
  const [agentDraft, setAgentDraft] = useState('');
  const [agentError, setAgentError] = useState<string | null>(null);
  const [isAgentLoading, setIsAgentLoading] = useState(false);
  const requestedExplanationKey = useRef<string | null>(null);

  const stringItem = strings.find((item) => item.id === params.id);
  const liveResult = liveResults.find(
    (item) => item.catalogId === params.id || item.stringId === params.id || item.id === params.id,
  );
  const detailResult = backendDetail ?? null;
  const runId = params.runId ?? liveResult?.runId ?? detailRunId;
  const rationale = detailResult?.rationale_payload ?? liveResult?.rationalePayload ?? null;
  const scoreBreakdown =
    liveResult?.scoreBreakdown ??
    (detailResult?.score_breakdown
      ? {
          preferenceMatch: detailResult.score_breakdown.preference_match,
          ruleFit: detailResult.score_breakdown.rule_fit,
          valueForMoney: detailResult.score_breakdown.value_for_money,
          nlpReviewScore: detailResult.score_breakdown.nlp_review_score,
          personalHistoryScore: detailResult.score_breakdown.personal_history_score,
          personalHistoryWeight: detailResult.score_breakdown.personal_history_weight,
          personalizedBaseScore: detailResult.score_breakdown.personalized_base_score,
          finalScore: detailResult.score_breakdown.final_score,
        }
      : undefined);
  const matchScore =
    liveResult?.matchScore ??
    (scoreBreakdown?.finalScore != null
      ? Math.round(scoreBreakdown.finalScore * 100)
      : detailResult
        ? Math.round(detailResult.score * 100)
        : undefined);
  const suggestedTensionRange =
    liveResult?.suggestedTensionRange ??
    (stringItem
      ? `${stringItem.recommendedTension[0]}-${stringItem.recommendedTension[1]} lbs`
      : 'your saved setup range');
  const topPriorities = Object.entries(user?.role === 'player' ? user.priorities : {})
    .sort((left, right) => right[1] - left[1])
    .slice(0, 3);
  const topPriorityLabels = topPriorities.map(([key]) => humanizeFeature(key));
  const bestForLabel =
    stringItem?.bestFor?.slice(0, 2).join(' · ') ||
    topPriorityLabels.slice(0, 2).join(' · ') ||
    'Your saved priorities';
  const priceLabel = stringItem
    ? getInventoryPriceLabel(stringItem).label
    : 'Price pending';
  const availabilityLabel = stringItem
    ? formatLabel(stringItem.availability)
    : 'Availability pending';
  const availabilityClassName =
    stringItem?.availability === 'out_of_stock'
      ? 'text-red-700'
      : stringItem?.availability === 'low_stock'
        ? 'text-warning-700'
        : 'text-success-700';
  const strongestReason =
    rationale?.top_reasons?.[0] ??
    liveResult?.reasons[0] ??
    detailResult?.reasons?.[0] ??
    'A detailed explanation is loading for this result.';
  const bestReason = compactSentence(strongestReason);
  const racketContext = rationale?.racket_context;
  const profileContext = rationale?.profile_context;
  const personalHistory = rationale?.personal_history;
  const personalHistoryUsed =
    rationale?.personal_history_used === true &&
    personalHistory?.mode === 'enabled';
  const similarPlayersUsed =
    rationale?.collaborative_filtering_used === true &&
    rationale.cf_shadow?.mode === 'enabled' &&
    Number(rationale.cf_shadow.cf_weight ?? 0) > 0;
  const currentRacketLabel =
    [racketContext?.brand, racketContext?.model].filter(Boolean).join(' ') ||
    'No saved racket selected';
  const targetTension = racketContext?.target_tension ?? profileContext?.preferred_tension;
  const targetTensionLabel = targetTension != null ? `${targetTension} lbs` : 'Saved profile tension';
  const playingContextLabel = [
    profileContext?.skill_level,
    profileContext?.playing_style,
    profileContext?.frequency_per_week != null
      ? `${profileContext.frequency_per_week} sessions/week`
      : null,
  ]
    .filter(Boolean)
    .map((value) => formatLabel(String(value)))
    .join(' · ') || 'Saved player profile';
  const personalSatisfaction = formatRating(personalHistory?.string_satisfaction);
  const personalWouldUseAgain = formatPercent(personalHistory?.would_use_again_ratio);
  const similarPlayerCount = Number(
    rationale?.cf_shadow?.distinct_supporting_users ?? 0,
  );

  useEffect(() => {
    if (!token || !params.id) {
      return;
    }

    const accessToken = token;
    const catalogId = params.id;
    let isMounted = true;
    setDetailError(null);

    async function loadRecommendationDetail() {
      try {
        const response = await backendApi.fetchRecommendationDetail(accessToken, 'me', catalogId);
        if (isMounted) {
          setBackendDetail(response.result);
          setDetailRunId(response.run_id ?? null);
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setDetailError(
          error instanceof BackendApiError
            ? error.message
            : 'Unable to load recommendation details.',
        );
      }
    }

    void loadRecommendationDetail();

    return () => {
      isMounted = false;
    };
  }, [params.id, token]);

  const askAgent = useCallback(
    async (rawQuestion: string) => {
      const question = rawQuestion.trim();
      if (!token || !params.id || !runId || !question || isAgentLoading) {
        return;
      }
      setAgentError(null);
      setIsAgentLoading(true);
      try {
        const response = await backendApi.queryAgent(token, {
          message: question,
          context: {
            surface: 'recommendation_explanation',
            run_id: runId,
            catalog_id: params.id,
          },
          conversation_history: agentHistory.slice(-12),
        });
        setAgentResponse(response);
        setAgentHistory((current) => [
          ...current,
          { role: 'user' as const, content: question },
          {
            role: 'assistant' as const,
            content: agentResponseToHistoryContent(response),
          },
        ].slice(-12));
        setAgentDraft('');
      } catch (error) {
        setAgentError(
          error instanceof BackendApiError
            ? error.message
            : 'The dynamic explanation is temporarily unavailable.',
        );
      } finally {
        setIsAgentLoading(false);
      }
    }, [agentHistory, isAgentLoading, params.id, runId, token],
  );

  const handleAgentAction = (action: BackendAgentAction) => {
    if (action.action === 'open_string' && action.parameters.catalog_id) {
      router.push(`/player/strings/${action.parameters.catalog_id}`);
      return;
    }

    /* Deferred FYP scope; re-enable with ACTIVE_AGENT_ACTIONS.
    if (action.action === 'open_booking' && action.parameters.booking_id) {
      router.push(`/player/bookings/${action.parameters.booking_id}`);
      return;
    }
    if (
      action.action === 'open_recommendation' &&
      action.parameters.catalog_id &&
      action.parameters.run_id
    ) {
      router.push(
        `/player/recommend/explain/${action.parameters.catalog_id}?runId=${action.parameters.run_id}`,
      );
      return;
    }
    if (action.action !== 'request_human_handoff') {
      return;
    }
    const bookingId = action.parameters.booking_id;
    if (!bookingId || !token) {
      router.push('/player/chat');
      return;
    }
    setAgentError(null);
    try {
      const conversation = await backendApi.requestBookingSupport(token, bookingId);
      router.push(`/player/chat/${conversation.id}`);
    } catch (error) {
      setAgentError(
        error instanceof BackendApiError
          ? error.message
          : 'Unable to request human support.',
      );
    }
    */
  };

  useEffect(() => {
    if (!runId || !params.id) {
      return;
    }
    const key = `${runId}:${params.id}`;
    if (requestedExplanationKey.current === key) {
      return;
    }
    requestedExplanationKey.current = key;
    void askAgent(
      'Using the exact saved recommendation context, write a natural explanation of why this string suits me. Use my profile, racket/tension context, and only evidence marked as used; mention personal experience, community feedback, or similar players only when active. Include the strongest supported benefit and one supported trade-off when available. Do not use a stock template or mention algorithms, scores, rankings, internal data, or that you are an AI.',
    );
  }, [askAgent, params.id, runId]);

  if (!user || user.role !== 'player') {
    return null;
  }

  const stringId = stringItem?.id ?? params.id;
  const canBook = Boolean(
    stringItem && stringItem.availability !== 'out_of_stock',
  );

  if (!stringItem && !detailResult) {
    return (
      <AppScreen title="Explanation unavailable">
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            We could not find this recommendation.
          </HeroText>
          {detailError ? (
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">{detailError}</HeroText>
          ) : null}
          <AppButton label="Back to results" className="mt-6" onPress={() => router.replace('/player/results')} />
        </AppCard>
      </AppScreen>
    );
  }

  return (
    <AppScreen
      headerVariant="secondary"
      title="Recommendation detail"
      subtitle="A clear explanation of why this setup fits your game."
      showBackButton
      onBackPress={() => router.back()}
        contentContainerClassName="pt-2"
    >
      <AppCard variant="dark" className="rounded-[30px]" padding="lg">
        <View className="flex-row items-start justify-between gap-3">
          <View className="flex-1">
            <HeroText className="text-[11px] font-bold uppercase tracking-[0.22em] text-primary-100">
              {stringItem?.brand ?? detailResult?.brand ?? 'StringSense'}
            </HeroText>
            <HeroText className="mt-1.5 text-[25px] font-black leading-[30px] tracking-tight text-white">
              {stringItem?.model ?? detailResult?.model_name ?? detailResult?.string_name}
            </HeroText>
          </View>
          {matchScore != null ? (
            <View className="min-w-[68px] rounded-[14px] bg-white/14 px-2.5 py-2">
              <HeroText className="text-[10px] font-bold uppercase tracking-[0.16em] text-primary-100">
                Match
              </HeroText>
              <HeroText className="mt-1 text-xl font-black text-white">{matchScore}%</HeroText>
            </View>
          ) : null}
        </View>

        <View className="mt-3 flex-row flex-wrap gap-1.5">
          <AppChip label={rationale?.primary_fit_angle ?? liveResult?.fitAngle ?? 'Fit angle unavailable'} variant="accent" />
        </View>

        <View className="mt-3 rounded-[14px] border border-white/10 bg-white/10 px-3 py-3">
          <HeroText className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary-100">
            Best reason
          </HeroText>
          <HeroText className="mt-1 text-base font-bold leading-5 text-white">
            {bestReason}.
          </HeroText>
        </View>

        <View className="mt-4 gap-2.5">
          <AppButton
            label={canBook ? 'Book this string' : 'Currently out of stock'}
            className="border-white bg-white"
            textClassName="text-primary-700 font-bold"
            isDisabled={!canBook}
            onPress={() => stringId ? router.push(`/player/bookings/new?stringId=${stringId}`) : undefined}
          />
          <AppButton
            label="Back to shortlist"
            variant="ghost"
            className="border-white/20 bg-white/10"
            textClassName="text-white font-bold"
            onPress={() => router.replace('/player/results')}
          />
        </View>
      </AppCard>

      {detailError ? (
          <View className="mt-3 rounded-[14px] border border-warning-100 bg-warning-50 px-3 py-2.5">
          <HeroText className="text-xs leading-5 text-warning-700">
            Fresh recommendation details are unavailable, so this page is using the latest saved result.
          </HeroText>
        </View>
      ) : null}

      <AppSection title="Why it fits" variant="compact">
        <AppCard variant="subtle" padding="md" className="mt-3">
          <HeroText className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary-700">
            Current setup
          </HeroText>
          <View className="mt-2 gap-2">
            <View className="flex-row items-start justify-between gap-3">
              <HeroText className="text-sm text-neutral-500">Racket</HeroText>
              <HeroText selectable className="flex-1 text-right text-sm font-semibold text-neutral-900">
                {currentRacketLabel}
              </HeroText>
            </View>
            <View className="flex-row items-start justify-between gap-3 border-t border-separator pt-2">
              <HeroText className="text-sm text-neutral-500">Tension</HeroText>
              <HeroText selectable className="text-right text-sm font-semibold text-neutral-900">
                {targetTensionLabel}
              </HeroText>
            </View>
            <View className="flex-row items-start justify-between gap-3 border-t border-separator pt-2">
              <HeroText className="text-sm text-neutral-500">Playing context</HeroText>
              <HeroText selectable className="flex-1 text-right text-sm font-semibold text-neutral-900">
                {playingContextLabel}
              </HeroText>
            </View>
          </View>
        </AppCard>

        {personalHistoryUsed ? (
          <AppCard variant="highlighted" padding="md" className="mt-3">
            <HeroText className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary-700">
              Previous personal experience
            </HeroText>
            <View className="mt-2 flex-row flex-wrap gap-1.5">
              {personalSatisfaction ? (
                <AppChip label={`String satisfaction ${personalSatisfaction}`} variant="accent" size="sm" />
              ) : null}
              {personalWouldUseAgain ? (
                <AppChip label={`${personalWouldUseAgain} would use again`} variant="accent" size="sm" />
              ) : null}
              <AppChip
                label={formatExperienceScope(personalHistory?.evidence_scope)}
                variant="accent"
                size="sm"
              />
            </View>
          </AppCard>
        ) : null}

        {similarPlayersUsed ? (
          <AppCard variant="subtle" padding="md" className="mt-3">
            <HeroText className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary-700">
              Similar-player evidence
            </HeroText>
            <View className="mt-2 flex-row flex-wrap gap-1.5">
              <AppChip
                label={`${similarPlayerCount || 'Similar'} players`}
                variant="secondary"
                size="sm"
              />
            </View>
          </AppCard>
        ) : null}

        {agentResponse ? (
          <AgentAnswerCard
            response={agentResponse}
            onQuestion={(question) => void askAgent(question)}
            onAction={(action) => void handleAgentAction(action)}
          />
        ) : (
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-600">
              {isAgentLoading
                ? 'Retrieving this run’s saved rationale and evidence...'
                : agentError ?? 'This recommendation does not have an exact run ID to explain.'}
            </HeroText>
          </AppCard>
        )}

        {agentError && agentResponse ? (
          <View className="mt-3 rounded-[14px] border border-warning-100 bg-warning-50 px-3 py-2.5">
            <HeroText className="text-xs leading-5 text-warning-700">{agentError}</HeroText>
          </View>
        ) : null}

        {runId ? (
          <View className="mt-4">
            <AppInput
              className="mb-2"
              placeholder="Ask a follow-up about this result..."
              accessibilityLabel="Question about this recommendation"
              value={agentDraft}
              onChangeText={setAgentDraft}
              multiline
              isDisabled={isAgentLoading}
            />
            <AppButton
              label="Ask about this result"
              isLoading={isAgentLoading}
              isDisabled={!agentDraft.trim()}
              leadingIcon={<SendHorizontal size={16} color="white" />}
              onPress={() => void askAgent(agentDraft)}
            />
          </View>
        ) : null}
      </AppSection>

      <AppSection title="Booking setup" variant="compact">
        <AppCard variant="subtle" padding="md">
          <View className="gap-3">
            <View className="flex-row items-center justify-between gap-3">
              <HeroText className="text-sm text-neutral-500">Suggested tension</HeroText>
              <HeroText className="text-sm font-bold text-neutral-950">
                {suggestedTensionRange}
              </HeroText>
            </View>
            <View className="flex-row items-center justify-between gap-3 border-t border-separator pt-3">
              <HeroText className="text-sm text-neutral-500">String price</HeroText>
              <HeroText className="text-sm font-bold text-neutral-950">{priceLabel}</HeroText>
            </View>
            <View className="flex-row items-center justify-between gap-3 border-t border-separator pt-3">
              <HeroText className="text-sm text-neutral-500">Availability</HeroText>
              <HeroText
                className={`text-sm font-bold ${availabilityClassName}`}
              >
                {availabilityLabel}
              </HeroText>
            </View>
            <View className="flex-row items-start justify-between gap-3 border-t border-separator pt-3">
              <HeroText className="text-sm text-neutral-500">Best for</HeroText>
              <HeroText className="flex-1 text-right text-sm font-bold text-neutral-950">
                {bestForLabel}
              </HeroText>
            </View>
          </View>
        </AppCard>
      </AppSection>
      <AppSection title="Next step" variant="compact">
        <View className="rounded-[14px] border border-[#E5EDF7] bg-white px-3 py-3">
          <View className="flex-row items-start gap-3">
            <View className="h-10 w-10 items-center justify-center rounded-full bg-primary-50">
              <Target size={19} color="#2F64B6" strokeWidth={2.4} />
            </View>
            <View className="flex-1">
              <HeroText className="text-sm leading-6 text-neutral-600">
                Use this page as a quick decision check: if the fit reasons match your game, book it now.
              </HeroText>
            </View>
          </View>

          <View className="mt-3 gap-2.5">
            <AppButton
              label="Book this string"
              leadingIcon={<WalletCards size={17} color="#FFFFFF" strokeWidth={2.4} />}
              isDisabled={!canBook}
              onPress={() => stringId ? router.push(`/player/bookings/new?stringId=${stringId}`) : undefined}
            />
            <AppButton
              label="Back to shortlist"
              variant="outline"
              onPress={() => router.replace('/player/results')}
            />
          </View>
        </View>
      </AppSection>

      <View className="h-6" />
    </AppScreen>
  );
}
