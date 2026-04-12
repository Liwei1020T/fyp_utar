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

function humanizeFeature(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function ScoreTile({
  label,
  value,
  note,
}: {
  label: string;
  value?: number;
  note: string;
}) {
  const percent = value == null ? 0 : Math.max(0, Math.min(100, Math.round(value * 100)));

  return (
    <AppCard variant="elevated" padding="sm" className="flex-1 min-w-[120px]">
      <HeroText className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">
        {label}
      </HeroText>
      <HeroText className="mt-1 text-2xl font-black text-neutral-950">
        {formatScore(value)}
      </HeroText>
      <View className="mt-2 h-2 overflow-hidden rounded-full bg-neutral-100">
        <View className="h-full rounded-full bg-primary-600" style={{ width: `${percent}%` }} />
      </View>
      <HeroText className="mt-2 text-xs leading-5 text-neutral-500">
        {note}
      </HeroText>
    </AppCard>
  );
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
  const fitAngle =
    rationale?.primary_fit_angle ??
    liveResult?.fitAngle ??
    'Profile match';
  const tradeOff =
    rationale?.trade_off_summary ??
    liveResult?.tradeOffSummary ??
    'Balanced against your saved profile and current catalog signals.';
  const matchScore = liveResult?.matchScore ?? (detailResult ? Math.round(detailResult.score * 100) : undefined);
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
        <View className="flex-row items-center justify-between gap-3">
          <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
            {stringItem?.brand ?? detailResult?.brand ?? 'StringSense'}
          </HeroText>
          {matchScore != null ? (
            <View className="rounded-full bg-white/12 px-3 py-1.5">
              <HeroText className="text-xs font-black text-white">{matchScore}%</HeroText>
            </View>
          ) : null}
        </View>
        <HeroText className="mt-3 text-[30px] font-bold tracking-tight text-white">
          {stringItem?.model ?? detailResult?.model_name ?? detailResult?.string_name}
        </HeroText>
        <AppChip label={fitAngle} variant="accent" className="mt-4 self-start" />
        <HeroText className="mt-3 text-sm leading-6 text-primary-100">
          This recommendation is anchored on your {user.playingStyle.toLowerCase()} style, {user.skillLevel.toLowerCase()} level, and preference for {Object.entries(user.priorities).sort((a, b) => b[1] - a[1])[0]?.[0]}.
        </HeroText>
      </AppCard>

      <AppSection eyebrow="Verdict" title="Best reason">
        <AppCard variant="highlighted" padding="md">
          <HeroText className="text-base font-bold text-neutral-950">
            {liveResult?.reasons[0] ?? detailResult?.reasons?.[0] ?? `${fitAngle} for your saved profile.`}
          </HeroText>
          <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
            {tradeOff}
          </HeroText>
        </AppCard>
      </AppSection>

      {scoreBreakdown ? (
        <AppSection eyebrow="Score formula" title="Three-part breakdown">
          <View className="flex-row flex-wrap gap-3">
            <ScoreTile
              label="Preference"
              value={scoreBreakdown.preferenceMatch}
              note="Includes official and NLP review evidence."
            />
            <ScoreTile
              label="Rule"
              value={scoreBreakdown.ruleFit}
              note="Uses gauge, style, skill, and frequency rules."
            />
            <ScoreTile
              label="Budget"
              value={scoreBreakdown.budgetFit}
              note="Checks price against your saved range."
            />
          </View>
        </AppSection>
      ) : null}

      <AppSection eyebrow="What this means" title="Match logic">
        <View className="gap-3">
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
            {rationale.rule_events.slice(0, 3).map((event, index) => (
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
        <AppSection eyebrow="Evidence" title="Feature sources">
          <View className="flex-row flex-wrap gap-2">
            {Object.entries(rationale.feature_sources).slice(0, 4).map(([feature, source]) => (
              <AppChip
                key={feature}
                label={`${humanizeFeature(feature)} · ${source.replace(/_/g, ' ')}`}
                variant="neutral"
              />
            ))}
          </View>
          <HeroText className="mt-3 text-xs leading-5 text-neutral-500">
            NLP review signals are blended into Preference Match rather than shown as a separate score.
          </HeroText>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Next step" title="How to continue">
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
