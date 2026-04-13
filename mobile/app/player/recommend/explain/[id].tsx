import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import {
  AlertTriangle,
  CheckCircle2,
  Gauge,
  ShieldCheck,
  Sparkles,
  Target,
  WalletCards,
  type LucideIcon,
} from 'lucide-react-native';
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

type ScoreTone = 'primary' | 'success' | 'warning' | 'neutral';

function formatScore(value?: number) {
  if (value == null) {
    return '-';
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

function compactSentence(value: string) {
  return value.trim().replace(/\.$/, '');
}

function clampPercent(value?: number | null) {
  return Math.max(0, Math.min(100, Math.round((value ?? 0) * 100)));
}

function toFeatureCopy(featureKey?: string, displayLabel?: string) {
  const label = displayLabel ?? humanizeFeature(featureKey ?? 'review support');
  const normalized = (featureKey ?? displayLabel ?? '').toLowerCase();

  if (normalized.includes('sound')) {
    return {
      title: 'Hitting sound support',
      body: 'Players mention a cleaner impact sound, which supports the feel profile behind this pick.',
    };
  }

  if (normalized.includes('tension')) {
    return {
      title: 'Tension retention support',
      body: 'Reviews support its ability to hold play feel across more sessions.',
    };
  }

  if (normalized.includes('durability')) {
    return {
      title: 'Durability support',
      body: 'Community signals point to reliable lifespan for frequent play.',
    };
  }

  return {
    title: `${label} support`,
    body: 'Community feedback strengthens confidence in this part of the recommendation.',
  };
}

function getBudgetCopy(
  rationale: BackendRecommendationRationale | null,
  fallbackPrice?: number | null,
) {
  const price = rationale?.budget?.price_rm ?? fallbackPrice;
  const minimum = rationale?.budget?.budget_min;
  const maximum = rationale?.budget?.budget_max;

  if (price == null || minimum == null || maximum == null) {
    return 'Price fit against your saved range.';
  }

  return `${formatCurrency(price)} fits your RM${minimum.toFixed(0)}-RM${maximum.toFixed(0)} range.`;
}

function buildRecommendationSummary({
  playingStyle,
  skillLevel,
  priorities,
}: {
  playingStyle: string;
  skillLevel: string;
  priorities: string[];
}) {
  const priorityCopy = priorities.length > 0
    ? priorities.slice(0, 2).join(' and ').toLowerCase()
    : 'your strongest preferences';

  return `A strong fit for your ${playingStyle.toLowerCase()} game and ${skillLevel.toLowerCase()} level, with the clearest advantage in ${priorityCopy}.`;
}

function buildMatchReasons({
  suggestedTensionRange,
  preferredTension,
  playFrequency,
  topPriorityLabels,
}: {
  suggestedTensionRange: string;
  preferredTension: number;
  playFrequency: string;
  topPriorityLabels: string[];
}) {
  const firstPriority = topPriorityLabels[0]?.toLowerCase() ?? 'feel';
  const playsOften = playFrequency === 'Tournament' || playFrequency === 'Weekly';

  return [
    {
      title: 'Matches your feel priority',
      body: `Its strongest profile supports ${firstPriority}, one of the main things you rated highly.`,
      Icon: Sparkles,
    },
    {
      title: 'Fits your tension setup',
      body: `${preferredTension} lbs sits comfortably inside the ${suggestedTensionRange} window.`,
      Icon: Gauge,
    },
    {
      title: 'Ready for your play rhythm',
      body: playsOften
        ? 'Durability support makes it a safer choice for frequent sessions.'
        : 'It gives you enough reliability without pushing you into an overly stiff setup.',
      Icon: ShieldCheck,
    },
  ];
}

function MatchReasonCard({
  title,
  body,
  Icon,
}: {
  title: string;
  body: string;
  Icon: LucideIcon;
}) {
  return (
    <View className="flex-row items-start gap-3 rounded-[22px] border border-[#E7EEF8] bg-white px-4 py-3.5">
      <View className="h-9 w-9 items-center justify-center rounded-full bg-primary-50">
        <Icon size={18} color="#2F64B6" strokeWidth={2.3} />
      </View>
      <View className="flex-1">
        <HeroText className="text-sm font-bold tracking-tight text-neutral-950">
          {title}
        </HeroText>
        <HeroText className="mt-1 text-[13px] leading-5 text-neutral-500">
          {body}
        </HeroText>
      </View>
    </View>
  );
}

function ScoreBlock({
  label,
  value,
  note,
  tone = 'primary',
}: {
  label: string;
  value?: number;
  note: string;
  tone?: ScoreTone;
}) {
  const badgeBackgrounds: Record<ScoreTone, string> = {
    primary: 'bg-primary-50',
    success: 'bg-success-50',
    warning: 'bg-warning-50',
    neutral: 'bg-neutral-100',
  };
  const badgeText: Record<ScoreTone, string> = {
    primary: 'text-primary-700',
    success: 'text-success-700',
    warning: 'text-warning-700',
    neutral: 'text-neutral-700',
  };

  return (
    <View className="min-w-[145px] flex-1 rounded-[22px] border border-[#E5EDF7] bg-white px-4 py-4">
      <View className="flex-row items-start justify-between gap-2">
        <HeroText className="text-[11px] font-bold uppercase tracking-[0.18em] text-neutral-400">
          {label}
        </HeroText>
        <View className={`rounded-full px-2.5 py-1 ${badgeBackgrounds[tone]}`}>
          <HeroText className={`text-xs font-black ${badgeText[tone]}`}>
            {formatScore(value)}
          </HeroText>
        </View>
      </View>
      <HeroText className="mt-3 text-[13px] leading-5 text-neutral-500">
        {note}
      </HeroText>
    </View>
  );
}

function ReviewStrength({
  title,
  body,
  score,
}: {
  title: string;
  body: string;
  score?: number | null;
}) {
  const percent = clampPercent(score);

  return (
    <View className="rounded-[20px] border border-[#E6EEF8] bg-white px-4 py-3.5">
      <View className="flex-row items-start justify-between gap-3">
        <View className="flex-1">
          <HeroText className="text-sm font-bold tracking-tight text-neutral-950">
            {title}
          </HeroText>
          <HeroText className="mt-1 text-[13px] leading-5 text-neutral-500">
            {body}
          </HeroText>
        </View>
        {score != null ? (
          <HeroText className="text-sm font-black text-primary-700">{percent}%</HeroText>
        ) : null}
      </View>
      {score != null ? (
        <View className="mt-3 h-1.5 overflow-hidden rounded-full bg-primary-50">
          <View className="h-full rounded-full bg-primary-600" style={{ width: `${percent}%` }} />
        </View>
      ) : null}
    </View>
  );
}

function getReviewStrengths(rationale: BackendRecommendationRationale | null) {
  const evidence = rationale?.feature_evidence ?? [];
  const preferredKeys = ['hitting_sound', 'tension_retention', 'durability'];

  const fromEvidence = preferredKeys
    .map((key) => evidence.find((entry) => entry.feature_key === key))
    .filter(Boolean)
    .map((entry) => {
      const copy = toFeatureCopy(entry?.feature_key, entry?.display_label);
      return {
        ...copy,
        score: entry?.nlp_review_score ?? entry?.effective_score ?? null,
      };
    });

  if (fromEvidence.length >= 3) {
    return fromEvidence.slice(0, 3);
  }

  const fallback = [
    {
      title: 'Hitting sound support',
      body: 'Community feedback supports a satisfying impact feel.',
      score: rationale?.nlp_review_scores?.hitting_sound ?? null,
    },
    {
      title: 'Tension retention support',
      body: 'Review signals help confirm the string can hold its feel longer.',
      score: rationale?.nlp_review_scores?.tension_retention ?? null,
    },
    {
      title: 'Durability support',
      body: 'Players give useful confidence that it can handle regular play.',
      score: rationale?.nlp_review_scores?.durability ?? null,
    },
  ];

  return [...fromEvidence, ...fallback].slice(0, 3);
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
  const topPriorityLabels = topPriorities.map(([key]) => humanizeFeature(key));
  const strongestReason =
    rationale?.top_reasons?.[0] ??
    liveResult?.reasons[0] ??
    detailResult?.reasons?.[0] ??
    'It lines up well with the way you play and the feel you prefer.';
  const bestReason = compactSentence(strongestReason);
  const tradeOff =
    rationale?.trade_off_summary ??
    liveResult?.tradeOffSummary ??
    'String movement control is the area to watch if you prefer a locked-in string bed.';
  const reviewStrengths = getReviewStrengths(rationale);

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
            : 'Unable to load recommendation details.',
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

  const preferredTension = user.preferredTension;
  const playFrequency = user.playFrequency;
  const matchReasons = buildMatchReasons({
    suggestedTensionRange,
    preferredTension,
    playFrequency,
    topPriorityLabels,
  });
  const recommendationSummary = buildRecommendationSummary({
    playingStyle: user.playingStyle,
    skillLevel: user.skillLevel,
    priorities: topPriorityLabels,
  });
  const stringId = stringItem?.id ?? params.id;
  const canBook = Boolean(stringItem);

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
      subtitle="A quick read on fit, confidence, and the main compromise."
      showBackButton
      onBackPress={() => router.back()}
      contentContainerClassName="pt-3"
    >
      <AppCard variant="dark" className="rounded-[30px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-bold uppercase tracking-[0.22em] text-primary-100">
              {stringItem?.brand ?? detailResult?.brand ?? 'StringSense'}
            </HeroText>
            <HeroText className="mt-2 text-[29px] font-black leading-[34px] tracking-tight text-white">
              {stringItem?.model ?? detailResult?.model_name ?? detailResult?.string_name}
            </HeroText>
          </View>
          {matchScore != null ? (
            <View className="min-w-[74px] rounded-[20px] bg-white/14 px-3 py-2.5">
              <HeroText className="text-[10px] font-bold uppercase tracking-[0.16em] text-primary-100">
                Score
              </HeroText>
              <HeroText className="mt-1 text-2xl font-black text-white">{matchScore}%</HeroText>
            </View>
          ) : null}
        </View>

        <View className="mt-4 flex-row flex-wrap gap-2">
          <AppChip label={rationale?.primary_fit_angle ?? liveResult?.fitAngle ?? 'Profile match'} variant="accent" />
          <AppChip label={suggestedTensionRange} variant="info" />
          <AppChip label={topPriorityLabels[0] ?? 'Balanced feel'} variant="secondary" />
        </View>

        <HeroText className="mt-4 text-sm leading-6 text-primary-100">
          {recommendationSummary}
        </HeroText>

        <View className="mt-4 rounded-[22px] border border-white/10 bg-white/10 px-4 py-3.5">
          <HeroText className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary-100">
            Best reason
          </HeroText>
          <HeroText className="mt-1.5 text-base font-bold leading-6 text-white">
            {bestReason}.
          </HeroText>
        </View>

        <View className="mt-5 flex-row gap-3">
          <AppButton
            label="Book this string"
            className="flex-1 border-white bg-white"
            textClassName="text-primary-700 font-bold"
            isDisabled={!canBook}
            onPress={() => stringId ? router.push(`/player/bookings/new?stringId=${stringId}`) : undefined}
          />
          <AppButton
            label="Back to shortlist"
            variant="ghost"
            className="flex-1 border-white/20 bg-white/10"
            textClassName="text-white font-bold"
            onPress={() => router.replace('/player/results')}
          />
        </View>
      </AppCard>

      {detailError ? (
        <View className="mt-4 rounded-[20px] border border-warning-100 bg-warning-50 px-4 py-3">
          <HeroText className="text-xs leading-5 text-warning-700">
            Fresh recommendation details are unavailable, so this page is using the latest saved result.
          </HeroText>
        </View>
      ) : null}

      <AppSection title="Why this matches you" variant="compact">
        <View className="gap-3">
          {matchReasons.map((reason) => (
            <MatchReasonCard
              key={reason.title}
              title={reason.title}
              body={reason.body}
              Icon={reason.Icon}
            />
          ))}
        </View>
      </AppSection>

      {scoreBreakdown ? (
        <AppSection title="Score breakdown" variant="compact">
          <View className="flex-row flex-wrap gap-3">
            <ScoreBlock
              label="Final"
              value={scoreBreakdown.finalScore ?? (matchScore != null ? matchScore / 100 : undefined)}
              note="Overall recommendation strength."
              tone="success"
            />
            <ScoreBlock
              label="Preference"
              value={scoreBreakdown.preferenceMatch}
              note="How well it fits your saved priorities."
            />
            <ScoreBlock
              label="Rule"
              value={scoreBreakdown.ruleFit}
              note="How well the setup fits your game."
              tone="warning"
            />
            <ScoreBlock
              label="Budget"
              value={scoreBreakdown.budgetFit}
              note={getBudgetCopy(rationale, detailResult?.price_rm ?? stringItem?.price)}
              tone="neutral"
            />
          </View>
        </AppSection>
      ) : null}

      <AppSection title="Review support" variant="compact">
        <View className="gap-3">
          <View className="rounded-[24px] border border-primary-100 bg-primary-50 px-4 py-4">
            <View className="flex-row items-start gap-3">
              <View className="h-9 w-9 items-center justify-center rounded-full bg-white">
                <CheckCircle2 size={18} color="#2F64B6" strokeWidth={2.3} />
              </View>
              <View className="flex-1">
                <HeroText className="text-sm font-bold tracking-tight text-neutral-950">
                  Community signals add confidence
                </HeroText>
                <HeroText className="mt-1 text-[13px] leading-5 text-neutral-600">
                  Reviews reinforce the strengths below, so the fit is not based only on specs.
                </HeroText>
              </View>
            </View>
          </View>

          {reviewStrengths.map((item) => (
            <ReviewStrength
              key={item.title}
              title={item.title}
              body={item.body}
              score={item.score}
            />
          ))}
        </View>
      </AppSection>

      <AppSection title="Trade-off" variant="compact">
        <View className="rounded-[24px] border border-warning-100 bg-warning-50 px-4 py-4">
          <View className="flex-row items-start gap-3">
            <View className="h-10 w-10 items-center justify-center rounded-full bg-white">
              <AlertTriangle size={19} color="#B67D21" strokeWidth={2.4} />
            </View>
            <View className="flex-1">
              <HeroText className="text-base font-bold tracking-tight text-neutral-950">
                Main compromise
              </HeroText>
              <HeroText className="mt-1.5 text-sm leading-6 text-neutral-700">
                {compactSentence(tradeOff)}.
              </HeroText>
              <HeroText className="mt-2 text-[13px] leading-5 text-neutral-500">
                Choose it if the strengths above matter more to you than this compromise.
              </HeroText>
            </View>
          </View>
        </View>
      </AppSection>

      <AppSection title="Next step" variant="compact">
        <View className="rounded-[26px] border border-[#E5EDF7] bg-white px-4 py-4">
          <View className="flex-row items-start gap-3">
            <View className="h-10 w-10 items-center justify-center rounded-full bg-primary-50">
              <Target size={19} color="#2F64B6" strokeWidth={2.4} />
            </View>
            <View className="flex-1">
              <HeroText className="text-sm leading-6 text-neutral-600">
                Use this page as a quick decision check: if the fit reasons match your game and the trade-off feels acceptable, book it now.
              </HeroText>
            </View>
          </View>

          <View className="mt-4 flex-row gap-3">
            <AppButton
              label="Book this string"
              className="flex-1"
              leadingIcon={<WalletCards size={17} color="#FFFFFF" strokeWidth={2.4} />}
              isDisabled={!canBook}
              onPress={() => stringId ? router.push(`/player/bookings/new?stringId=${stringId}`) : undefined}
            />
            <AppButton
              label="Back to shortlist"
              variant="outline"
              className="flex-1"
              onPress={() => router.replace('/player/results')}
            />
          </View>
        </View>
      </AppSection>

      <View className="h-6" />
    </AppScreen>
  );
}
