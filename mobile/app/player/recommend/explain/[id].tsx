import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { HeroText } from '../../../../components/ui/heroui';
import { AppButton } from '../../../../components/ui/AppButton';
import { AppCard } from '../../../../components/ui/AppCard';
import { AppChip } from '../../../../components/ui/AppChip';
import { AppScreen } from '../../../../components/shared/AppScreen';
import { AppSection } from '../../../../components/shared/AppSection';
import {
  useCurrentUser,
  useBackendAccessToken,
  useLiveRecommendationResults,
  useStrings,
} from '../../../../store/appStore';
import { getStringById } from '../../../../services/mockAppService';
import { BackendApiError, backendApi } from '../../../../services/backendApi';
import type { BackendRecommendationResult } from '../../../../types/backend';

function formatScore(value?: number) {
  if (value == null) {
    return '—';
  }
  return `${Math.round(value * 100)}%`;
}

export default function RecommendationExplanationScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const liveResults = useLiveRecommendationResults();
  const [backendDetail, setBackendDetail] = useState<BackendRecommendationResult | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const stringItem =
    strings.find((item) => item.id === params.id) ?? getStringById(params.id);
  const liveResult = liveResults.find(
    (item) => item.catalogId === params.id || item.stringId === params.id || item.id === params.id,
  );
  const detailResult = backendDetail ?? null;
  const rationale = detailResult?.rationale_payload ?? liveResult?.rationalePayload ?? null;
  const suggestedTensionRange =
    liveResult?.suggestedTensionRange ??
    (stringItem
      ? `${stringItem.recommendedTension[0]} to ${stringItem.recommendedTension[1]} lbs`
      : 'your saved setup range');
  const scoreBreakdown = liveResult?.scoreBreakdown ??
    (detailResult?.score_breakdown
      ? {
          preferenceMatch: detailResult.score_breakdown.preference_match,
          ruleFit: detailResult.score_breakdown.rule_fit,
          budgetFit: detailResult.score_breakdown.budget_fit,
          nlpReviewScore: detailResult.score_breakdown.nlp_review_score,
          finalScore: detailResult.score_breakdown.final_score,
        }
      : undefined);

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
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setDetailError(
          error instanceof BackendApiError
            ? error.message
            : 'Unable to load backend recommendation explanation.',
        );
      }
    }

    void loadRecommendationDetail();

    return () => {
      isMounted = false;
    };
  }, [params.id, token]);

  if (!user || user.role !== 'player') {
    return null;
  }

  if (!stringItem && !detailResult) {
    return (
      <AppScreen title="Explanation unavailable">
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">We couldn&apos;t find this recommendation.</HeroText>
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
      title="Recommendation explanation"
      subtitle="Break down why this string fits your current player profile."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
          {stringItem?.brand ?? detailResult?.brand ?? 'StringSense'}
        </HeroText>
        <HeroText className="mt-3 text-[30px] font-bold tracking-tight text-white">
          {stringItem?.model ?? detailResult?.model_name ?? detailResult?.string_name}
        </HeroText>
        <HeroText className="mt-3 text-sm leading-6 text-primary-100">
          This recommendation is anchored on your {user.playingStyle.toLowerCase()} style, {user.skillLevel.toLowerCase()} level, and preference for {Object.entries(user.priorities).sort((a, b) => b[1] - a[1])[0]?.[0]}.
        </HeroText>
      </AppCard>

      {scoreBreakdown ? (
        <AppSection eyebrow="Score formula" title="Hybrid score breakdown">
          <AppCard variant="highlighted" padding="md">
            <View className="flex-row flex-wrap gap-2">
              <AppChip label={`Preference ${formatScore(scoreBreakdown.preferenceMatch)}`} variant="primary" />
              <AppChip label={`Rule ${formatScore(scoreBreakdown.ruleFit)}`} variant="secondary" />
              <AppChip label={`Budget ${formatScore(scoreBreakdown.budgetFit)}`} variant="neutral" />
              <AppChip label={`NLP ${formatScore(scoreBreakdown.nlpReviewScore)}`} variant="neutral" />
            </View>
            <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
              Final score combines your saved preference vector, badminton fit rules, budget alignment, and review-derived NLP signals.
            </HeroText>
          </AppCard>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Why it fits" title="Match logic">
        <View className="gap-3">
          <AppCard variant="elevated" padding="md">
            <HeroText className="text-base font-semibold text-neutral-950">
              Style fit
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              {liveResult?.reasons[0] ??
                `${stringItem?.bestFor[0] ?? 'This string'} aligns with how you currently describe your game.`}{' '}
              The string stays lively without drifting too far from your preferred tension baseline.
            </HeroText>
          </AppCard>
          <AppCard variant="elevated" padding="md">
            <HeroText className="text-base font-semibold text-neutral-950">
              Priority fit
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              {liveResult?.reasons[1]
                ? `${liveResult.reasons[1]}. `
                : ''}Your strongest weighted priorities are {Object.entries(user.priorities)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 2)
                .map(([key]) => key)
                .join(' and ')}. This string performs well across those areas.
            </HeroText>
          </AppCard>
          <AppCard variant="elevated" padding="md">
            <HeroText className="text-base font-semibold text-neutral-950">
              Tension fit
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              Recommended tension range is {suggestedTensionRange}. Your saved {user.preferredTension} lbs setup sits comfortably inside that window.
            </HeroText>
          </AppCard>
        </View>
      </AppSection>

      {rationale?.rule_events?.length ? (
        <AppSection eyebrow="Rules" title="Badminton rule events">
          <View className="gap-3">
            {rationale.rule_events.map((event, index) => (
              <AppCard key={`${event.rule ?? 'rule'}-${index}`} variant="elevated" padding="sm">
                <HeroText className="text-sm font-semibold text-neutral-900">
                  {event.reason ?? event.rule ?? 'Rule adjustment'}
                </HeroText>
                {event.delta != null ? (
                  <HeroText className="mt-1 text-xs font-bold text-primary-600">
                    Delta {event.delta > 0 ? '+' : ''}{event.delta.toFixed(2)}
                  </HeroText>
                ) : null}
              </AppCard>
            ))}
          </View>
        </AppSection>
      ) : null}

      {rationale?.feature_sources ? (
        <AppSection eyebrow="Provenance" title="Feature sources">
          <View className="flex-row flex-wrap gap-2">
            {Object.entries(rationale.feature_sources).slice(0, 8).map(([feature, source]) => (
              <AppChip
                key={feature}
                label={`${feature.replace(/_/g, ' ')} · ${source.replace(/_/g, ' ')}`}
                variant="neutral"
              />
            ))}
          </View>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Strengths and trade-offs" title="What you gain and what you give up">
        <View className="gap-3">
          {(stringItem?.strengths ?? liveResult?.reasons ?? detailResult?.reasons ?? []).map((strength) => (
            <AppCard key={strength} variant="highlighted" padding="sm">
              <HeroText className="text-sm font-semibold text-neutral-900">{strength}</HeroText>
            </AppCard>
          ))}
          {(stringItem?.tradeOffs ?? []).map((tradeOff) => (
            <AppCard key={tradeOff} variant="subtle" padding="sm">
              <HeroText className="text-sm leading-6 text-neutral-600">{tradeOff}</HeroText>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="For the demo" title="How to continue">
        <View className="flex-row flex-wrap gap-2">
          <AppChip label="Compare with shortlist" variant="neutral" />
          <AppChip label="Book from here" variant="primary" />
        </View>
      </AppSection>

      <View className="mb-10 mt-8 gap-3">
        <AppButton
          label="Book this string"
          size="lg"
          isDisabled={!stringItem}
          onPress={() => stringItem ? router.push(`/player/bookings/new?stringId=${stringItem.id}`) : undefined}
        />
      </View>
    </AppScreen>
  );
}
