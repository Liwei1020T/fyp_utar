import React, { useEffect, useMemo, useState } from 'react';
import { FlatList, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, Search, Sparkles } from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { useBackendAccessToken, useCurrentUser, useStrings } from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import type { BackendRecommendationRun } from '../../../types/backend';
import { formatDateTime } from '../../../lib/formatters';

function getStringLabel(
  strings: ReturnType<typeof useStrings>,
  catalogId: string | null | undefined,
) {
  if (!catalogId) {
    return 'Catalog item unavailable';
  }

  const match = strings.find((item) => item.id === catalogId);
  return match ? `${match.brand} ${match.model}` : catalogId;
}

export default function AdminRecommendationRunsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const bottomContentInset = useBottomContentInset(18);
  const [runs, setRuns] = useState<BackendRecommendationRun[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      return;
    }

    if (!token) {
      setRuns([]);
      setIsLoading(false);
      setError('Backend admin login is required to inspect saved recommendation runs.');
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await backendApi.adminListRecommendationRuns(token, {
          limit: 50,
          offset: 0,
        });
        if (!cancelled) {
          setRuns(response.items);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof BackendApiError
              ? loadError.message
              : 'Failed to load recommendation runs.',
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
  }, [token, user]);

  const filteredRuns = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    if (!normalizedSearch) {
      return runs;
    }

    return runs.filter((run) => {
      const topResult = run.items[0];
      const topLabel = getStringLabel(strings, topResult?.catalog_id);
      const haystack = [
        run.id,
        run.phone_number,
        run.username,
        run.algorithm_version,
        topLabel,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      return haystack.includes(normalizedSearch);
    });
  }, [runs, search, strings]);

  if (!user || user.role !== 'admin') {
    return null;
  }

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title="Recommendation runs"
      subtitle="Saved recommendation histories, score layers, and profile snapshots."
      showBackButton
      onBackPress={() => router.back()}
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={filteredRuns}
        keyExtractor={(item) => item.id}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="gap-3 pb-4">
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-start gap-3">
                <View className="mt-0.5 h-10 w-10 items-center justify-center rounded-[16px] bg-primary-50">
                  <Sparkles size={18} color="#2F64B6" />
                </View>
                <View className="flex-1">
                  <HeroText className="text-[15px] font-semibold tracking-tight text-neutral-900">
                    Audit recommendation output
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                    Each run preserves the request, resolved profile snapshot, and item-level
                    scoring used to produce the recommendation result.
                  </HeroText>
                </View>
              </View>
            </AppCard>

            <AppInput
              variant="minimal"
              className="mb-0"
              placeholder="Search runs, phone, or algorithm..."
              value={search}
              onChangeText={setSearch}
              leftAdornment={<Search size={18} color="#94A3B8" strokeWidth={2.5} />}
              inputClassName="text-[15px] font-medium"
            />
          </View>
        }
        renderItem={({ item }) => {
          const topResult = item.items[0];
          const topLabel = getStringLabel(strings, topResult?.catalog_id);

          return (
            <View className="mb-3.5">
              <AppCard
                variant="elevated"
                padding="md"
                onPress={() => router.push(`/admin/recommendations/${item.id}`)}
              >
                <View className="gap-3">
                  <View className="flex-row items-start justify-between gap-3">
                    <View className="flex-1">
                      <HeroText className="text-[11px] font-semibold uppercase tracking-[0.14em] text-neutral-400">
                        Recommendation run
                      </HeroText>
                      <HeroText className="mt-1 text-[17px] font-bold tracking-tight text-neutral-950">
                        {item.username || item.phone_number || 'Anonymous player'}
                      </HeroText>
                    </View>
                    <ArrowRight size={16} color="#94A3B8" />
                  </View>

                  <View className="flex-row flex-wrap gap-2">
                    <AppChip
                      label={item.algorithm_version}
                      variant="primary"
                      size="sm"
                      className="max-w-full"
                    />
                    <AppChip
                      label={`${item.items.length} result${item.items.length === 1 ? '' : 's'}`}
                      variant="neutral"
                      size="sm"
                    />
                  </View>

                  <View className="gap-1.5">
                    <HeroText className="text-[12px] font-semibold text-primary-700">
                      Top result
                    </HeroText>
                    <HeroText className="text-[14px] font-semibold leading-5 text-neutral-900">
                      {topLabel}
                    </HeroText>
                    <HeroText className="text-[12px] leading-5 text-neutral-500">
                      Generated {formatDateTime(item.generated_at ?? '')}
                    </HeroText>
                  </View>

                  <HeroText className="text-[12px] font-medium text-neutral-500">
                    Phone: {item.phone_number || 'Unavailable'}
                  </HeroText>
                </View>
              </AppCard>
            </View>
          );
        }}
        ListEmptyComponent={
          <AppCard variant="subtle" className="mt-4" padding="lg">
            <HeroText className="text-base font-semibold text-neutral-800">
              {isLoading ? 'Loading recommendation runs...' : 'No recommendation runs found'}
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              {error
                ? error
                : 'Generate recommendations from the player flow to build an audit history here.'}
            </HeroText>
          </AppCard>
        }
      />
    </AppScreen>
  );
}
