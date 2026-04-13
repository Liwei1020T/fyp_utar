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
  useBackendAccessToken,
  useCurrentUser,
  useLiveRecommendationResults,
  useStrings,
} from '../../../../store/appStore';
import { BackendApiError, backendApi } from '../../../../services/backendApi';
import { getStringById } from '../../../../services/mockAppService';
import type {
  BackendRecommendationRationale,
  BackendRecommendationResult,
} from '../../../../types/backend';

function formatScore(value?: number) {
  if (value == null) {
    return '—';
  }
  return `${Math.round(value * 100)}%`;
}

function formatCurrency(value?: number | null) {
  if (value == null) {
    return 'Price pending';
  }
  return `RM${value.toFixed(0)}`;
}

function humanizeFeature(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function humanizeSource(value?: string) {
  if (!value) {
    return 'Unknown source';
  }
  if (value === 'official_performance+nlp_review') {
    return 'Official + NLP review';
  }
  return humanizeFeature(value);
}

function ScoreTile({
  label,
  value,
  note,
  tone = 'primary',
}: {
  label: string;
  value?: number;
  note: string;
  tone?: 'primary' | 'accent' | 'neutral' | 'success';
}) {
  const percent = value == null ? 0 : Math.max(0, Math.min(100, Math.round(value * 100)));
  const fillClassName =
    tone === 'accent'
      ? 'bg-accent-500'
      : tone === 'neutral'
        ? 'bg-neutral-500'
        : tone === 'success'
          ? 'bg-success-500'
          : 'bg-primary-600';

  return (
    <AppCard variant="elevated" padding="sm" className="min-w-[138px] flex-1 rounded-[24px]">
      <HeroText className="text-[10px] font-bold uppercase tracking-[0.2em] text-neutral-400">
        {label}
      </HeroText>
      <HeroText className="mt-2 text-[28px] font-black tracking-tight text-neutral-950">
        {formatScore(value)}
      </HeroText>
      <View className="mt-3 h-2 overflow-hidden rounded-full bg-neutral-100">
        <View className={`h-full rounded-full ${fillClassName}`} style={{ width: `${percent}%` }} />
      </View>
      <HeroText className="mt-3 text-xs leading-5 text-neutral-500">
        {note}
      </HeroText>
    </AppCard>
  );
}

function EvidenceRow({
  label,
  source,
  effectiveScore,
  preferenceWeight,
  nlpReviewScore,
  officialScore,
}: {
  label: string;
  source?: string;
  effectiveScore?: number | null;
  preferenceWeight?: number | null;
  nlpReviewScore?: number | null;
  officialScore?: number | null;
}) {
  const effectiveWidth = Math.round(Math.max(0, Math.min(1, effectiveScore ?? 0)) * 100);
  const nlpWidth = Math.round(Math.max(0, Math.min(1, nlpReviewScore ?? 0)) * 100);
  const officialWidth = Math.round(Math.max(0, Math.min(1, officialScore ?? 0)) * 100);

  return (
    <AppCard variant="elevated" padding="sm" className="rounded-[24px]">
      <View className="flex-row items-start justify-between gap-3">
        <View className="flex-1">
          <HeroText className="text-sm font-bold text-neutral-950">{label}</HeroText>
          <HeroText className="mt-1 text-xs leading-5 text-neutral-500">
            {humanizeSource(source)}
          </HeroText>
        </View>
        {preferenceWeight != null ? (
          <View className="rounded-full bg-primary-50 px-3 py-1.5">
            <HeroText className="text-[10px] font-bold uppercase tracking-[0.18em] text-primary-700">
              Weight {formatScore(preferenceWeight)}
            </HeroText>
          </View>
        ) : null}
      </View>

      <View className="mt-4 gap-3">
        <View>
          <View className="flex-row items-center justify-between">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
              Effective
            </HeroText>
            <HeroText className="text-xs font-black text-neutral-900">
              {formatScore(effectiveScore ?? undefined)}
            </HeroText>
          </View>
          <View className="mt-2 h-2 overflow-hidden rounded-full bg-neutral-100">
            <View className="h-full rounded-full bg-primary-600" style={{ width: `${effectiveWidth}%` }} />
          </View>
        </View>

        {nlpReviewScore != null ? (
          <View>
            <View className="flex-row items-center justify-between">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
                NLP Review
              </HeroText>
              <HeroText className="text-xs font-black text-neutral-900">
                {formatScore(nlpReviewScore)}
              </HeroText>
            </View>
            <View className="mt-2 h-2 overflow-hidden rounded-full bg-neutral-100">
              <View className="h-full rounded-full bg-accent-500" style={{ width: `${nlpWidth}%` }} />
            </View>
          </View>
        ) : null}

        {officialScore != null ? (
          <View>
            <View className="flex-row items-center justify-between">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
                Official
              </HeroText>
              <HeroText className="text-xs font-black text-neutral-900">
                {formatScore(officialScore)}
              </HeroText>
            </View>
            <View className="mt-2 h-2 overflow-hidden rounded-full bg-neutral-100">
              <View className="h-full rounded-full bg-neutral-500" style={{ width: `${officialWidth}%` }} />
            </View>
          </View>
        ) : null}
      </View>
    </AppCard>
  );
}

function budgetLabel(
  rationale: BackendRecommendationRationale | null,
  fallbackPrice?: number | null,
) {
  const price = rationale?.budget?.price_rm ?? fallbackPrice;
  const minimum = rationale?.budget?.budget_min;
  const maximum = rationale?.budget?.budget_max;

  if (price == null || minimum == null || maximum == null) {
    return 'Budget fit is based on your saved range and current shelf price.';
  }

  return `${formatCurrency(price)} against your RM${minimum.toFixed(0)}–RM${maximum.toFixed(0)} target range.`;
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
  const fitAngle = rationale?.primary_fit_angle ?? liveResult?.fitAngle ?? 'Profile match';
  const tradeOff =
    rationale?.trade_off_summary ??
    liveResult?.tradeOffSummary ??
    'Balanced against your saved profile, badminton rules, and current price range.';
  const scoreBreakdown =
    liveResult?.scoreBreakdown ??
    (detailResult?.score_breakdown
      ? {
          preferenceMatch: detailResult.score_breakdown.preference_match,
          ruleFit: detailResult.score_breakdown.rule_fit,
          budgetFit: detailResult.score_breakdown.budget_fit,
          nlpReviewScore: detailResult.score_breakdown.nlp_review_score,
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
  const priorityLine =
    topPriorities.length > 0
      ? topPriorities.map(([key]) => humanizeFeature(key)).join(', ')
      : 'your saved priorities';
  const featureEvidence = (rationale?.feature_evidence ?? []).slice(0, 4);
  const nlpEvidence = featureEvidence.filter((entry) => (entry.nlp_influence ?? 0) > 0);
  const strongestReason =
    liveResult?.reasons[0] ??
    detailResult?.reasons?.[0] ??
    `${fitAngle} for your current player profile.`;
  const followUpReason =
    liveResult?.reasons[1] ??
    detailResult?.reasons?.[1] ??
    'The strongest weighted parts of your profile are carrying this recommendation.';

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
          <HeroText className="text-lg font-bold text-neutral-900">
            We couldn&apos;t find this recommendation.
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
      title="Recommendation explanation"
      subtitle="See the exact fit logic, review evidence, and trade-offs behind this pick."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="dark" className="rounded-[34px]" padding="lg">
        <View className="flex-row items-start justify-between gap-3">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
              {stringItem?.brand ?? detailResult?.brand ?? 'StringSense'}
            </HeroText>
            <HeroText className="mt-3 text-[30px] font-black tracking-tight text-white">
              {stringItem?.model ?? detailResult?.model_name ?? detailResult?.string_name}
            </HeroText>
          </View>
          {matchScore != null ? (
            <View className="rounded-[22px] bg-white/12 px-4 py-3">
              <HeroText className="text-[10px] font-bold uppercase tracking-[0.18em] text-primary-100">
                Final
              </HeroText>
              <HeroText className="mt-1 text-2xl font-black text-white">{matchScore}%</HeroText>
            </View>
          ) : null}
        </View>

        <View className="mt-5 flex-row flex-wrap gap-2">
          <AppChip label={fitAngle} variant="accent" />
          <AppChip
            label={rationale?.nlp_review_signal_count ? `${rationale.nlp_review_signal_count} review signals` : 'Rules + profile'}
            variant="info"
          />
          <AppChip label={suggestedTensionRange} variant="secondary" />
        </View>

        <HeroText className="mt-4 text-sm leading-6 text-primary-100">
          This pick is anchored on your {user.playingStyle.toLowerCase()} style, {user.skillLevel.toLowerCase()} level, and strongest priorities in {priorityLine.toLowerCase()}.
        </HeroText>

        <View className="mt-5 rounded-[24px] bg-white/10 px-4 py-4">
          <HeroText className="text-[10px] font-bold uppercase tracking-[0.18em] text-primary-100">
            Best reason
          </HeroText>
          <HeroText className="mt-2 text-base font-bold leading-6 text-white">{strongestReason}</HeroText>
        </View>
      </AppCard>

      {detailError ? (
        <AppCard variant="subtle" className="mt-4 rounded-[24px] border border-warning-100 bg-warning-50/70" padding="sm">
          <HeroText className="text-xs leading-5 text-warning-700">
            Backend detail refresh failed, so some sections below are using the latest cached app data. {detailError}
          </HeroText>
        </AppCard>
      ) : null}

      <AppSection eyebrow="Verdict" title="Why it landed here">
        <View className="gap-3">
          <AppCard variant="highlighted" padding="md" className="rounded-[28px]">
            <HeroText className="text-base font-bold text-neutral-950">{strongestReason}</HeroText>
            <HeroText className="mt-3 text-sm leading-6 text-neutral-600">{tradeOff}</HeroText>
          </AppCard>
          <AppCard variant="elevated" padding="md" className="rounded-[28px]">
            <HeroText className="text-[11px] font-bold uppercase tracking-[0.18em] text-neutral-400">
              Profile read
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-600">
              {followUpReason}. Your current setup leans most heavily on {priorityLine.toLowerCase()}, so this string is being rewarded where those priorities overlap.
            </HeroText>
          </AppCard>
        </View>
      </AppSection>

      {scoreBreakdown ? (
        <AppSection eyebrow="Score formula" title="Recommendation breakdown">
          <View className="flex-row flex-wrap gap-3">
            <ScoreTile
              label="Final"
              value={scoreBreakdown.finalScore ?? (matchScore != null ? matchScore / 100 : undefined)}
              note="The final rank after profile, rule, and budget checks are blended."
              tone="success"
            />
            <ScoreTile
              label="Preference"
              value={scoreBreakdown.preferenceMatch}
              note="Your weighted priorities matched against effective string features."
            />
            <ScoreTile
              label="Rule"
              value={scoreBreakdown.ruleFit}
              note="Badminton-specific logic like style, gauge, tension, and play frequency."
              tone="accent"
            />
            <ScoreTile
              label="Budget"
              value={scoreBreakdown.budgetFit}
              note={budgetLabel(rationale, detailResult?.price_rm ?? stringItem?.price)}
              tone="neutral"
            />
            {scoreBreakdown.nlpReviewScore != null ? (
              <ScoreTile
                label="NLP Review"
                value={scoreBreakdown.nlpReviewScore}
                note="How strongly review-derived signals back up the parts of your profile that matter most."
              />
            ) : null}
          </View>
        </AppSection>
      ) : null}

      <AppSection eyebrow="What this means" title="Match logic">
        <View className="gap-3">
          <AppCard variant="elevated" padding="md" className="rounded-[28px]">
            <HeroText className="text-base font-semibold text-neutral-950">Priority fit</HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              Your top weighted priorities are {priorityLine.toLowerCase()}. This string stays competitive across those areas, which is why it survives both the profile score and the badminton rule pass.
            </HeroText>
          </AppCard>

          <AppCard variant="elevated" padding="md" className="rounded-[28px]">
            <HeroText className="text-base font-semibold text-neutral-950">Tension fit</HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              Suggested tension range is {suggestedTensionRange}. Your saved {user.preferredTension} lbs setup sits inside that window, so this option should feel coherent with your current hitting setup.
            </HeroText>
          </AppCard>

          <AppCard variant="elevated" padding="md" className="rounded-[28px]">
            <HeroText className="text-base font-semibold text-neutral-950">Trade-off watch</HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">{tradeOff}</HeroText>
          </AppCard>
        </View>
      </AppSection>

      {nlpEvidence.length > 0 ? (
        <AppSection eyebrow="NLP evidence" title="Review-derived support">
          <View className="gap-3">
            <AppCard variant="highlighted" padding="md" className="rounded-[28px]">
              <HeroText className="text-base font-bold text-neutral-950">
                {rationale?.nlp_review_summary ?? 'Review-derived signals are reinforcing this recommendation.'}
              </HeroText>
              <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
                The NLP layer is not replacing your profile. It acts as extra evidence for the features most likely to matter for your current style and feel preference.
              </HeroText>
            </AppCard>

            {nlpEvidence.map((entry, index) => (
              <EvidenceRow
                key={`${entry.feature_key ?? 'feature'}-${index}`}
                label={entry.display_label ?? humanizeFeature(entry.feature_key ?? 'Feature')}
                source={entry.source}
                effectiveScore={entry.effective_score}
                preferenceWeight={entry.preference_weight}
                nlpReviewScore={entry.nlp_review_score}
                officialScore={entry.official_score}
              />
            ))}
          </View>
        </AppSection>
      ) : null}

      {rationale?.rule_events?.length ? (
        <AppSection eyebrow="Rules" title="Badminton rule events">
          <View className="gap-3">
            {rationale.rule_events.slice(0, 4).map((event, index) => (
              <AppCard key={`${event.rule ?? 'rule'}-${index}`} variant="elevated" padding="sm" className="rounded-[24px]">
                <View className="flex-row items-start justify-between gap-3">
                  <View className="flex-1">
                    <HeroText className="text-sm font-semibold text-neutral-900">
                      {event.reason ?? event.rule ?? 'Rule adjustment'}
                    </HeroText>
                    {event.rule ? (
                      <HeroText className="mt-1 text-xs leading-5 text-neutral-500">
                        {humanizeFeature(event.rule)}
                      </HeroText>
                    ) : null}
                  </View>
                  {event.delta != null ? (
                    <View className="rounded-full bg-primary-50 px-3 py-1.5">
                      <HeroText className="text-xs font-black text-primary-700">
                        {event.delta > 0 ? '+' : ''}
                        {event.delta.toFixed(2)}
                      </HeroText>
                    </View>
                  ) : null}
                </View>
              </AppCard>
            ))}
          </View>
        </AppSection>
      ) : null}

      {featureEvidence.length > 0 ? (
        <AppSection eyebrow="Source blend" title="Where the scores came from">
          <View className="flex-row flex-wrap gap-2">
            {featureEvidence.map((entry, index) => (
              <AppChip
                key={`${entry.feature_key ?? 'source'}-${index}`}
                label={`${entry.display_label ?? humanizeFeature(entry.feature_key ?? 'Feature')} · ${humanizeSource(entry.source)}`}
                variant="neutral"
              />
            ))}
          </View>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Next step" title="How to continue">
        <View className="gap-3">
          <View className="flex-row flex-wrap gap-2">
            <AppChip label="Compare with shortlist" variant="neutral" />
            <AppChip label="Open string detail" variant="secondary" />
            <AppChip label="Book from here" variant="primary" />
          </View>

          <AppCard variant="subtle" padding="md" className="rounded-[28px]">
            <HeroText className="text-sm leading-6 text-neutral-600">
              Use this page when you need confidence, not just ranking. If the fit story looks right and the trade-off feels acceptable, go straight to booking. If not, bounce back to results and compare one more option side by side.
            </HeroText>
          </AppCard>
        </View>
      </AppSection>

      <View className="mb-10 mt-8 gap-3">
        <AppButton
          label="Book this string"
          size="lg"
          isDisabled={!stringItem}
          onPress={() => stringItem ? router.push(`/player/bookings/new?stringId=${stringItem.id}`) : undefined}
        />
        <AppButton
          label="Back to shortlist"
          variant="outline"
          onPress={() => router.replace('/player/results')}
        />
      </View>
    </AppScreen>
  );
}
