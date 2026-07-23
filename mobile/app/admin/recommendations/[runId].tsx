import React, { useEffect, useMemo, useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { AppDetailList } from '../../../components/shared/AppDetailList';
import { useBackendAccessToken, useCurrentUser, useStrings } from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import type { BackendRecommendationRun, BackendRecommendationRunItem } from '../../../types/backend';
import { formatDateTime, formatLabel } from '../../../lib/formatters';

function formatScalarValue(value: unknown) {
  if (value == null) {
    return 'Unavailable';
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  if (typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value)) {
    return value.length > 0 ? value.join(', ') : 'None';
  }
  return JSON.stringify(value);
}

function getStringLabel(strings: ReturnType<typeof useStrings>, catalogId: string) {
  const match = strings.find((item) => item.id === catalogId);
  return match ? `${match.brand} ${match.model}` : catalogId;
}

function buildSnapshotItems(snapshot: Record<string, unknown>) {
  return Object.entries(snapshot).map(([key, value]) => ({
    label: formatLabel(key),
    value: formatScalarValue(value),
  }));
}

function buildRationaleSummary(rationale: Record<string, unknown>) {
  const summaryKeys = [
    'algorithm_family',
    'feature_source_generated_at',
    'review_count_snapshot',
    'primary_fit_angle',
    'trade_off_summary',
    'collaborative_filtering_used',
  ] as const;

  return summaryKeys
    .filter((key) => key in rationale && rationale[key] != null)
    .map((key) => ({
      label: formatLabel(key),
      value:
        key === 'feature_source_generated_at' && typeof rationale[key] === 'string'
          ? formatDateTime(rationale[key])
          : formatScalarValue(rationale[key]),
    }));
}

function ScoreBreakdownRows({ item }: { item: BackendRecommendationRunItem }) {
  return (
    <View className="gap-2.5">
      <View className="flex-row items-center justify-between">
        <HeroText className="text-[12px] font-semibold uppercase tracking-[0.12em] text-neutral-400">
          Score breakdown
        </HeroText>
        <HeroText className="text-[15px] font-bold tracking-tight text-neutral-950">
          {item.final_score.toFixed(2)}
        </HeroText>
      </View>

      <View className="gap-2">
        {[
          ['Preference match', item.preference_match_score],
          ['Rule fit', item.rule_fit_score],
          ['Budget fit', item.budget_fit_score],
          ['Confidence', item.confidence_score],
          ['NLP review', item.nlp_review_score],
        ].map(([label, value]) => (
          <View key={label} className="flex-row items-center justify-between">
            <HeroText className="text-sm text-neutral-500">{label}</HeroText>
            <HeroText className="text-sm font-semibold text-neutral-900">
              {value == null ? 'Unavailable' : Number(value).toFixed(2)}
            </HeroText>
          </View>
        ))}
      </View>
    </View>
  );
}

export default function AdminRecommendationRunDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ runId?: string }>();
  const runId = typeof params.runId === 'string' ? params.runId : null;
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const [run, setRun] = useState<BackendRecommendationRun | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(token && runId));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      return;
    }

    if (!token || !runId) {
      setRun(null);
      setIsLoading(false);
      setError('Backend admin login is required to inspect recommendation run details.');
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await backendApi.adminFetchRecommendationRun(token, runId);
        if (!cancelled) {
          setRun(response);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof BackendApiError
              ? loadError.message
              : 'Failed to load recommendation run detail.',
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void hydrate();

    return () => {
      cancelled = true;
    };
  }, [runId, token, user]);

  const requestItems = useMemo(
    () => (run ? buildSnapshotItems(run.request_snapshot) : []),
    [run],
  );
  const profileItems = useMemo(
    () => (run ? buildSnapshotItems(run.profile_snapshot) : []),
    [run],
  );

  if (!user || user.role !== 'admin') {
    return null;
  }

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title="Run detail"
      subtitle="Inspect the exact scoring inputs and ranked output for one saved recommendation run."
      showBackButton
      onBackPress={() => router.back()}
    >
      {error ? (
        <AppCard variant="subtle" className="mb-6 border border-red-100" padding="md">
          <HeroText className="text-sm font-medium text-red-600">{error}</HeroText>
        </AppCard>
      ) : null}

      {!run && isLoading ? (
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-base font-semibold text-neutral-800">
            Loading recommendation run...
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Pulling the request snapshot, profile snapshot, and ranked output from the backend.
          </HeroText>
        </AppCard>
      ) : null}

      {run ? (
        <View className="gap-6">
          <AppSection eyebrow="Summary" title="Run metadata">
            <AppDetailList
              items={[
                {
                  label: 'Player',
                  value: run.username || run.phone_number || 'Anonymous player',
                },
                {
                  label: 'Phone',
                  value: run.phone_number || 'Unavailable',
                },
                {
                  label: 'Generated at',
                  value: formatDateTime(run.generated_at ?? ''),
                },
                {
                  label: 'Algorithm version',
                  value: run.algorithm_version,
                },
                {
                  label: 'Matrix version',
                  value: run.matrix_version || 'Unavailable',
                },
                {
                  label: 'Feature source version',
                  value: run.feature_source_version || 'Unavailable',
                },
              ]}
            />
          </AppSection>

          <AppSection eyebrow="Request" title="Submitted recommendation request">
            <AppDetailList items={requestItems} />
          </AppSection>

          <AppSection eyebrow="Profile" title="Resolved profile snapshot">
            <AppDetailList items={profileItems} />
          </AppSection>

          <AppSection
            eyebrow="Ranked output"
            title="Saved recommendation items"
            subtitle="These are the exact rows written into recommendation run history."
          >
            <View className="gap-3">
              {run.items.map((item, index) => {
                const rationaleSummary = buildRationaleSummary(item.rationale);
                const stringLabel = getStringLabel(strings, item.catalog_id);

                return (
                  <AppCard key={item.id} variant="elevated" padding="md">
                    <View className="gap-4">
                      <View className="flex-row items-start justify-between gap-3">
                        <View className="flex-1">
                          <HeroText className="text-[11px] font-semibold uppercase tracking-[0.14em] text-neutral-400">
                            Rank #{item.rank_position || index + 1}
                          </HeroText>
                          <HeroText className="mt-1 text-[17px] font-bold tracking-tight text-neutral-950">
                            {stringLabel}
                          </HeroText>
                        </View>
                        <AppChip
                          label={`Score ${item.final_score.toFixed(2)}`}
                          variant="primary"
                          size="sm"
                        />
                      </View>

                      <ScoreBreakdownRows item={item} />

                      {rationaleSummary.length > 0 ? (
                        <View className="gap-2.5">
                          <HeroText className="text-[12px] font-semibold uppercase tracking-[0.12em] text-neutral-400">
                            Rationale summary
                          </HeroText>
                          {rationaleSummary.map((summaryItem) => (
                            <View
                              key={summaryItem.label}
                              className="flex-row items-start justify-between gap-4"
                            >
                              <HeroText className="max-w-[42%] text-sm text-neutral-500">
                                {summaryItem.label}
                              </HeroText>
                              <HeroText className="flex-1 text-right text-sm font-semibold leading-5 text-neutral-900">
                                {summaryItem.value}
                              </HeroText>
                            </View>
                          ))}
                        </View>
                      ) : null}
                    </View>
                  </AppCard>
                );
              })}
            </View>
          </AppSection>
        </View>
      ) : null}
    </AppScreen>
  );
}
