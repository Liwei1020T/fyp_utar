import { useFocusEffect, useRouter } from 'expo-router';
import React, { useCallback, useState } from 'react';
import {
  Activity,
  ChevronRight,
  Download,
  RefreshCw,
  SlidersHorizontal,
  X,
} from 'lucide-react-native';
import {
  Modal,
  Platform,
  Pressable,
  ScrollView,
  Share,
  useWindowDimensions,
  View,
} from 'react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { FeedbackFeatureList } from '../../components/shared/FeedbackFeatureList';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppDatePicker } from '../../components/ui/AppDatePicker';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppSelect } from '../../components/ui/AppSelect';
import { appChromeColors } from '../../components/ui/theme';
import { HeroText } from '../../components/ui/heroui';
import { formatDateTime, formatLabel } from '../../lib/formatters';
import { BackendApiError, backendApi } from '../../services/backendApi';
import {
  useBackendAccessToken,
  useCurrentUser,
  useStrings,
} from '../../store/appStore';
import type {
  BackendAdminFeedbackSummary,
  BackendAdminFeedback,
  BackendFeedbackSummary,
} from '../../types/backend';

const PAGE_SIZE = 50;

function formatFeedbackScope(scope: BackendFeedbackSummary | null) {
  return scope?.racket_model_key
    ? scope.racket_model_key.split(':').map(formatLabel).join(' · ')
    : 'Global strings';
}

export default function AdminFeedbackScreen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
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
  const [feedbackSummary, setFeedbackSummary] = useState<
    BackendAdminFeedbackSummary | null
  >(null);
  const [selectedFeedbackScope, setSelectedFeedbackScope] = useState('global');
  const [isFeedbackLoading, setIsFeedbackLoading] = useState(Boolean(token));
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showCalibration, setShowCalibration] = useState(false);

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

  const loadFeedbackSummary = useCallback(async () => {
    if (!token || user?.role !== 'admin') return;
    setIsFeedbackLoading(true);
    setFeedbackError(null);
    try {
      setFeedbackSummary(await backendApi.adminFetchFeedbackSummary(token));
    } catch (error) {
      setFeedbackError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to load feedback calibration evidence.',
      );
    } finally {
      setIsFeedbackLoading(false);
    }
  }, [token, user?.role]);

  useFocusEffect(
    useCallback(() => {
      void load();
      void loadFeedbackSummary();
    }, [load, loadFeedbackSummary]),
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

  const feedbackScopes: BackendFeedbackSummary[] = feedbackSummary
    ? [feedbackSummary.global, ...feedbackSummary.racket_contexts]
    : [];
  const activeFeedbackScope = feedbackScopes.find(
    (scope) => (scope.racket_model_key ?? 'global') === selectedFeedbackScope,
  ) ?? feedbackSummary?.global ?? null;
  const visibleFeedbackStrings = activeFeedbackScope?.strings.filter(
    (item) => !stringId || item.string_id === stringId,
  ) ?? [];
  const activeFilterCount = [
    rating !== undefined,
    stringId !== undefined,
    dateFrom.length > 0,
    dateTo.length > 0,
  ].filter(Boolean).length;
  const activeFeatureCount = visibleFeedbackStrings.reduce(
    (count, summary) => count + Object.keys(summary.features).length,
    0,
  );
  const establishedSignalCount = visibleFeedbackStrings.reduce(
    (count, summary) =>
      count
      + Object.values(summary.features).filter(
        (feature) => feature.distinct_users >= 10,
      ).length,
    0,
  );
  const isNarrow = width < 520;
  const listTitle = isLoading && total === 0
    ? 'Feedback inbox'
    : `${total} feedback record${total === 1 ? '' : 's'}`;
  const shownCountLabel = isLoading && items.length === 0
    ? 'Loading'
    : `${items.length}/${total} shown`;

  return (
    <AppScreen
      tone="admin"
      headerVariant="flow"
      title="Feedback management"
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection
        eyebrow="Feedback inbox"
        title={listTitle}
        subtitle="Filter player responses, then open a record to review its booking."
        variant="hero"
      >
        <View className="gap-3">
          <View className="flex-row items-center gap-3">
            <View className="min-w-0 flex-1">
              <HeroText className="text-sm font-semibold text-neutral-900">
                {activeFilterCount > 0
                  ? `${activeFilterCount} filter${activeFilterCount === 1 ? '' : 's'} active`
                  : 'All feedback records'}
              </HeroText>
              <HeroText className="mt-0.5 text-xs leading-5 text-neutral-500">
                {isLoading ? 'Refreshing the latest responses...' : shownCountLabel}
              </HeroText>
            </View>
            <AppButton
              label={showFilters
                ? 'Hide filters'
                : activeFilterCount > 0
                  ? `Filters · ${activeFilterCount}`
                  : 'Filters'}
              variant={showFilters || activeFilterCount > 0 ? 'secondary' : 'outline'}
              size="sm"
              leadingIcon={
                <SlidersHorizontal
                  size={16}
                  color={showFilters || activeFilterCount > 0
                    ? appChromeColors.primary
                    : appChromeColors.textSecondary}
                />
              }
              accessibilityState={{ expanded: showFilters, selected: activeFilterCount > 0 }}
              onPress={() => setShowFilters((current) => !current)}
            />
          </View>

          <AppButton
            label="View calibration evidence"
            variant="secondary"
            leadingIcon={<Activity size={17} color={appChromeColors.primary} />}
            className="w-full"
            onPress={() => setShowCalibration(true)}
            accessibilityHint="Open recommendation learning evidence"
          />

          {showFilters ? (
            <AppCard variant="default" padding="md">
              <View className="gap-3">
                <AppSelect
                  label="Rating"
                  value={rating == null ? 'all' : String(rating)}
                  options={[
                    { id: 'all', label: 'All ratings' },
                    ...[1, 2, 3, 4, 5].map((value) => ({
                      id: String(value),
                      label: `${value}/5`,
                    })),
                  ]}
                  onChange={(value) =>
                    setRating(value === 'all' ? undefined : Number(value))
                  }
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
                    onChange={(id) =>
                      setStringId(id === '__all_strings__' ? undefined : id)
                    }
                  />
                ) : null}
                <View className={isNarrow ? 'gap-3' : 'flex-row gap-3'}>
                  <View className={isNarrow ? undefined : 'flex-1'}>
                    <AppDatePicker
                      label="From date"
                      value={dateFrom}
                      onChange={setDateFrom}
                    />
                  </View>
                  <View className={isNarrow ? undefined : 'flex-1'}>
                    <AppDatePicker
                      label="To date"
                      value={dateTo}
                      onChange={setDateTo}
                    />
                  </View>
                </View>
                <View className="flex-row gap-3">
                  <View className="flex-1">
                    <AppButton
                      label="Refresh"
                      variant="outline"
                      isLoading={isLoading || isFeedbackLoading}
                      leadingIcon={
                        <RefreshCw size={16} color={appChromeColors.primary} />
                      }
                      onPress={() => {
                        void load();
                        void loadFeedbackSummary();
                      }}
                    />
                  </View>
                  <View className="flex-1">
                    <AppButton
                      label="Export CSV"
                      variant="outline"
                      leadingIcon={
                        <Download size={16} color={appChromeColors.textSecondary} />
                      }
                      onPress={() => void exportFeedback()}
                    />
                  </View>
                </View>
              </View>
            </AppCard>
          ) : null}
        </View>
      </AppSection>

      {message ? (
        <AppCard variant="subtle" className="mt-4" padding="sm">
          <HeroText className="text-sm text-neutral-700">{message}</HeroText>
        </AppCard>
      ) : null}

      <AppSection
        eyebrow="Responses"
        title="Feedback records"
        subtitle="Tap a record to open the linked booking and review the full context."
        rightAction={<AppChip label={shownCountLabel} variant="neutral" />}
      >
        <View className="gap-3">
          {isLoading && items.length === 0 ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm text-neutral-600">
                Loading feedback records...
              </HeroText>
            </AppCard>
          ) : null}
          {items.map((item) => (
            <AppCard
              key={item.id}
              variant={item.rating <= 2 ? 'highlighted' : 'elevated'}
              padding="md"
              onPress={() => router.push(`/admin/bookings/${item.booking_id}`)}
              accessibilityLabel={`${item.string_name} feedback from ${item.customer_username}, ${item.rating} out of 5`}
              accessibilityHint="Open the related booking"
            >
              <View className="flex-row items-start justify-between gap-3">
                <View className="min-w-0 flex-1">
                  <HeroText className="text-base font-bold text-neutral-950">
                    {item.string_name}
                  </HeroText>
                  <HeroText className="mt-1 text-sm text-neutral-600">
                    {item.customer_username} • {item.order_code}
                  </HeroText>
                </View>
                <View className="items-end gap-1">
                  <AppChip
                    label={`${item.rating}/5`}
                    variant={item.rating <= 2 ? 'warning' : 'success'}
                  />
                  <ChevronRight
                    size={17}
                    color={appChromeColors.textMuted}
                    strokeWidth={2.2}
                  />
                </View>
              </View>
              <HeroText className="mt-3 text-sm leading-6 text-neutral-700">
                {item.comment ??
                  item.string_feedback ??
                  item.service_feedback ??
                  'No written comment.'}
              </HeroText>
              <HeroText className="mt-2 text-xs leading-5 text-neutral-500">
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
              <HeroText className="text-sm font-semibold text-neutral-900">
                No feedback matches these filters.
              </HeroText>
              <HeroText className="mt-1 text-sm leading-6 text-neutral-600">
                Open Filters to broaden the rating, string, or date range.
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
      </AppSection>

      <Modal
        visible={showCalibration}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCalibration(false)}
      >
        <View className="flex-1 justify-end bg-black/40">
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Close calibration evidence"
            onPress={() => setShowCalibration(false)}
            className="absolute inset-0"
          />
          <View className="max-h-[88%] rounded-t-[24px] bg-white px-4 pb-5 pt-4">
            <View className="flex-row items-start justify-between gap-4">
              <View className="min-w-0 flex-1">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                  Recommendation learning
                </HeroText>
                <HeroText className="mt-1 text-xl font-bold tracking-tight text-neutral-950">
                  Calibration evidence
                </HeroText>
                <HeroText className="mt-1 text-sm leading-6 text-neutral-600">
                  See which completed-booking signals are strong enough to inform recommendations.
                </HeroText>
              </View>
              <AppIconButton
                icon={<X size={18} color={appChromeColors.textSecondary} />}
                accessibilityLabel="Close calibration evidence"
                onPress={() => setShowCalibration(false)}
              />
            </View>

            <ScrollView
              className="mt-4"
              keyboardShouldPersistTaps="handled"
              showsVerticalScrollIndicator={false}
              contentContainerStyle={{ paddingBottom: 12 }}
            >
              {isFeedbackLoading ? (
                <HeroText className="text-sm text-neutral-600">
                  Loading recommendation evidence...
                </HeroText>
              ) : feedbackError ? (
                <View className="gap-3">
                  <HeroText
                    selectable
                    accessibilityLiveRegion="polite"
                    className="text-sm leading-6 text-red-700"
                  >
                    {feedbackError}
                  </HeroText>
                  <AppButton
                    label="Try again"
                    variant="outline"
                    size="sm"
                    onPress={() => void loadFeedbackSummary()}
                  />
                </View>
              ) : feedbackSummary ? (
                <View className="gap-4">
                  <AppSelect
                    label="Evidence scope"
                    value={selectedFeedbackScope}
                    options={feedbackScopes.map((scope) => ({
                      id: scope.racket_model_key ?? 'global',
                      label: formatFeedbackScope(scope),
                    }))}
                    onChange={setSelectedFeedbackScope}
                  />

                  <View className="flex-row flex-wrap gap-2">
                    <AppChip
                      label={formatFeedbackScope(activeFeedbackScope)}
                      variant="info"
                    />
                    <AppChip
                      label={`${activeFeedbackScope?.strings.length ?? 0} string${activeFeedbackScope?.strings.length === 1 ? '' : 's'} with evidence`}
                      variant="neutral"
                    />
                    <AppChip
                      label={`${activeFeatureCount} signal${activeFeatureCount === 1 ? '' : 's'} shown`}
                      variant="neutral"
                    />
                    <AppChip
                      label={`${establishedSignalCount} established`}
                      variant="success"
                    />
                  </View>

                  {visibleFeedbackStrings.length > 0 ? (
                    <View>
                      {visibleFeedbackStrings.map((summary, index) => {
                        const string = strings.find(
                          (item) => item.id === summary.string_id,
                        );
                        const featureCount = Object.keys(summary.features).length;
                        const establishedFeatureCount = Object.values(summary.features)
                          .filter((feature) => feature.distinct_users >= 10)
                          .length;
                        return (
                          <View
                            key={summary.string_id}
                            className={index > 0 ? 'border-t border-neutral-200 pt-4' : undefined}
                          >
                            <View className="flex-row items-start justify-between gap-3">
                              <View className="min-w-0 flex-1">
                                <HeroText className="text-base font-bold text-neutral-950">
                                  {string
                                    ? `${string.brand} ${string.model}`
                                    : summary.string_id}
                                </HeroText>
                                <HeroText className="mt-1 text-xs leading-5 text-neutral-500">
                                  {featureCount} calibrated signal{featureCount === 1 ? '' : 's'}
                                </HeroText>
                              </View>
                              {establishedFeatureCount > 0 ? (
                                <AppChip
                                  label={`${establishedFeatureCount} established`}
                                  variant="success"
                                />
                              ) : null}
                            </View>
                            <FeedbackFeatureList
                              features={summary.features}
                              showScope
                            />
                          </View>
                        );
                      })}
                    </View>
                  ) : (
                    <HeroText className="text-sm leading-6 text-neutral-600">
                      No eligible feedback ratings exist for this scope and string filter.
                    </HeroText>
                  )}
                </View>
              ) : (
                <HeroText className="text-sm leading-6 text-neutral-600">
                  No feedback calibration snapshot is available.
                </HeroText>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </AppScreen>
  );
}
