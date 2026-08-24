import { useFocusEffect, useRouter } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { Platform, Share, View } from 'react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { CommunityFeatureList } from '../../components/shared/CommunityFeatureList';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { AppSelect } from '../../components/ui/AppSelect';
import { HeroText } from '../../components/ui/heroui';
import { formatDateTime, formatLabel } from '../../lib/formatters';
import { BackendApiError, backendApi } from '../../services/backendApi';
import {
  useBackendAccessToken,
  useCurrentUser,
  useStrings,
} from '../../store/appStore';
import type {
  BackendAdminCommunitySummary,
  BackendAdminFeedback,
  BackendCommunitySummary,
} from '../../types/backend';

const PAGE_SIZE = 50;

export default function AdminFeedbackScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const [items, setItems] = useState<BackendAdminFeedback[]>([]);
  const [total, setTotal] = useState(0);
  const [rating, setRating] = useState<number | undefined>();
  const [stringId, setStringId] = useState<string | undefined>();
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [communitySummary, setCommunitySummary] = useState<
    BackendAdminCommunitySummary | null
  >(null);
  const [selectedCommunityScope, setSelectedCommunityScope] = useState('global');
  const [isCommunityLoading, setIsCommunityLoading] = useState(Boolean(token));
  const [communityError, setCommunityError] = useState<string | null>(null);

  const load = useCallback(async (offset = 0) => {
    if (!token || user?.role !== 'admin') return;
    setIsLoading(true);
    setMessage(null);
    try {
      const response = await backendApi.adminListFeedback(token, {
        rating,
        string_id: stringId,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit: PAGE_SIZE,
        offset,
      });
      setItems((current) =>
        offset === 0 ? response.items : [...current, ...response.items],
      );
      setTotal(response.total);
    } catch (error) {
      setMessage(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to load feedback.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [dateFrom, dateTo, rating, stringId, token, user?.role]);

  const loadCommunitySummary = useCallback(async () => {
    if (!token || user?.role !== 'admin') return;
    setIsCommunityLoading(true);
    setCommunityError(null);
    try {
      setCommunitySummary(await backendApi.adminFetchCommunitySummary(token));
    } catch (error) {
      setCommunityError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to load community calibration evidence.',
      );
    } finally {
      setIsCommunityLoading(false);
    }
  }, [token, user?.role]);

  useFocusEffect(
    useCallback(() => {
      void load();
      void loadCommunitySummary();
    }, [load, loadCommunitySummary]),
  );

  if (!user || user.role !== 'admin') return null;

  const exportFeedback = async () => {
    if (!token) return;
    setMessage(null);
    try {
      const csv = await backendApi.adminExportFeedback(token, {
        rating,
        string_id: stringId,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      if (Platform.OS === 'web') {
        const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
        const link = document.createElement('a');
        link.href = url;
        link.download = 'stringsense-feedback.csv';
        link.click();
        URL.revokeObjectURL(url);
      } else {
        await Share.share({ title: 'StringSense feedback CSV', message: csv });
      }
      setMessage('Feedback export prepared.');
    } catch (error) {
      setMessage(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to export feedback.',
      );
    }
  };

  const communityScopes: BackendCommunitySummary[] = communitySummary
    ? [communitySummary.global, ...communitySummary.racket_contexts]
    : [];
  const activeCommunityScope = communityScopes.find(
    (scope) => (scope.racket_model_key ?? 'global') === selectedCommunityScope,
  ) ?? communitySummary?.global ?? null;
  const visibleCommunityStrings = activeCommunityScope?.strings.filter(
    (item, index) => (stringId ? item.string_id === stringId : index === 0),
  ) ?? [];

  return (
    <AppScreen
      tone="admin"
      headerVariant="flow"
      title="Feedback management"
      subtitle="Review structured service feedback and low-satisfaction cases."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection
        eyebrow="Recommendation learning"
        title="Community calibration"
        subtitle="Read-only evidence used by V11. Exact racket-model ratings are shown separately from global fallback evidence."
      >
        <AppCard variant="elevated" padding="md">
          {isCommunityLoading ? (
            <HeroText className="text-sm text-neutral-600">
              Loading recommendation evidence...
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
          ) : communitySummary ? (
            <View className="gap-4">
              <AppSelect
                label="Evidence scope"
                value={selectedCommunityScope}
                options={communityScopes.map((scope) => {
                  const scopeKey = scope.racket_model_key ?? 'global';
                  return {
                    id: scopeKey,
                    label: scope.racket_model_key
                      ? scope.racket_model_key.split(':').map(formatLabel).join(' · ')
                      : 'Global strings',
                  };
                })}
                onChange={setSelectedCommunityScope}
              />

              <HeroText selectable className="text-xs leading-5 text-neutral-500">
                Policy {activeCommunityScope?.policy_version ?? '—'} · snapshot{' '}
                {activeCommunityScope?.snapshot_version.slice(0, 10) ?? '—'}
                {stringId
                  ? ' · follows the selected string filter'
                  : ' · showing one string; use the filter below to change it'}
              </HeroText>

              {visibleCommunityStrings.length > 0 ? (
                <View className="gap-3">
                  {visibleCommunityStrings.map((summary) => {
                    const string = strings.find(
                      (item) => item.id === summary.string_id,
                    );
                    return (
                      <View
                        key={summary.string_id}
                        className="rounded-2xl border border-neutral-100 px-4"
                      >
                        <HeroText className="pt-4 text-sm font-bold text-neutral-950">
                          {string
                            ? `${string.brand} ${string.model}`
                            : summary.string_id}
                        </HeroText>
                        <CommunityFeatureList
                          features={summary.features}
                          showScope
                        />
                      </View>
                    );
                  })}
                </View>
              ) : (
                <HeroText className="text-sm leading-6 text-neutral-600">
                  No eligible community ratings exist for this scope and string filter.
                </HeroText>
              )}
            </View>
          ) : (
            <HeroText className="text-sm leading-6 text-neutral-600">
              No community calibration snapshot is available.
            </HeroText>
          )}
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Filters" title="Narrow feedback">
        <AppSelect
          label="Rating"
          value={rating == null ? 'all' : String(rating)}
          options={[{ id: 'all', label: 'All ratings' }, ...[1, 2, 3, 4, 5].map((value) => ({
            id: String(value),
            label: `${value}/5`,
          }))]}
          onChange={(value) => setRating(value === 'all' ? undefined : Number(value))}
        />
        {strings.length ? (
          <AppSelect
            label="String"
            value={stringId ?? '__all_strings__'}
            placeholder="All strings"
            options={[
              { id: '__all_strings__', label: 'All strings' },
              ...strings.map((item) => ({
                id: item.id,
                label: `${item.brand} ${item.model}`,
              })),
            ]}
            onChange={(id) => setStringId(id === '__all_strings__' ? undefined : id)}
            className="mt-3"
          />
        ) : null}
        <View className="mt-3 flex-row gap-3">
          <View className="flex-1">
            <AppInput
              label="From date"
              placeholder="YYYY-MM-DD"
              value={dateFrom}
              onChangeText={setDateFrom}
            />
          </View>
          <View className="flex-1">
            <AppInput
              label="To date"
              placeholder="YYYY-MM-DD"
              value={dateTo}
              onChangeText={setDateTo}
            />
          </View>
        </View>
        <View className="mt-4 flex-row gap-3">
          <View className="flex-1">
            <AppButton
              label="Refresh"
              variant="outline"
              isLoading={isLoading || isCommunityLoading}
              onPress={() => {
                void load();
                void loadCommunitySummary();
              }}
            />
          </View>
          <View className="flex-1">
            <AppButton
              label="Export CSV"
              variant="outline"
              onPress={() => void exportFeedback()}
            />
          </View>
        </View>
      </AppSection>

      {message ? (
        <AppCard variant="subtle" className="mb-4" padding="sm">
          <HeroText className="text-sm text-neutral-700">{message}</HeroText>
        </AppCard>
      ) : null}

      <View className="gap-3">
        {items.map((item) => (
          <AppCard
            key={item.id}
            variant={item.rating <= 2 ? 'highlighted' : 'elevated'}
            padding="md"
            onPress={() => router.push(`/admin/bookings/${item.booking_id}`)}
          >
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1">
                <HeroText className="text-base font-bold text-neutral-950">
                  {item.string_name}
                </HeroText>
                <HeroText className="mt-1 text-sm text-neutral-600">
                  {item.customer_username} • {item.order_code}
                </HeroText>
              </View>
              <AppChip
                label={`${item.rating}/5`}
                variant={item.rating <= 2 ? 'warning' : 'success'}
              />
            </View>
            <HeroText className="mt-3 text-sm leading-6 text-neutral-700">
              {item.comment ??
                item.string_feedback ??
                item.service_feedback ??
                'No written comment.'}
            </HeroText>
            <HeroText className="mt-2 text-xs text-neutral-500">
              String {item.string_satisfaction ?? '—'}/5 • Tension{' '}
              {item.tension_satisfaction ?? '—'}/5 • Would use again:{' '}
              {item.would_use_again == null
                ? '—'
                : item.would_use_again
                  ? 'Yes'
                  : 'No'}{' '}
              • {formatDateTime(item.created_at)}
            </HeroText>
          </AppCard>
        ))}
        {!isLoading && items.length === 0 ? (
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm text-neutral-600">
              No feedback matches these filters.
            </HeroText>
          </AppCard>
        ) : null}
        {items.length < total ? (
          <AppButton
            label={`Load more (${items.length}/${total})`}
            variant="outline"
            isLoading={isLoading}
            onPress={() => void load(items.length)}
          />
        ) : null}
      </View>
    </AppScreen>
  );
}
