import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { BarChart3, Clock3, Gauge } from 'lucide-react-native';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { MetricStatCard } from '../../../components/analytics/MetricStatCard';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { useBackendAccessToken, useCurrentUser } from '../../../store/appStore';
import { formatCurrency } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import type { BackendAnalyticsSummary } from '../../../types/backend';

export default function AdminAnalyticsScreen() {
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const [analytics, setAnalytics] = useState<BackendAnalyticsSummary | null>(null);
  const [periodDays, setPeriodDays] = useState<7 | 30>(7);
  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [error, setError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) {
      setAnalytics(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    if (!token) {
      setAnalytics(null);
      setIsLoading(false);
      setError('Backend login is required to view live analytics.');
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      setAnalytics(null);
      setIsLoading(true);
      setError(null);
      try {
        const summary = await backendApi.adminAnalyticsSummary(token, periodDays);
        if (cancelled) {
          return;
        }
        setAnalytics(summary);
      } catch (loadError) {
        if (!cancelled) {
          const statusCode = loadError instanceof BackendApiError
            ? loadError.statusCode
            : undefined;
          setError(
            statusCode === 401
              ? 'Your admin session has expired. Sign in again to view live analytics.'
              : statusCode !== undefined && statusCode >= 500
                ? 'Analytics is temporarily unavailable. Try again in a moment.'
                : 'We could not load analytics right now. Check your connection and try again.',
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
  }, [isAdmin, loadAttempt, periodDays, token]);

  if (!isAdmin) {
    return null;
  }

  if (isLoading && analytics === null) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="primary"
        title="Admin analytics"
        subtitle="Bookings, revenue, feedback, and payment workload."
      >
        <AppCard variant="subtle" className="mt-6" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            Loading live analytics...
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Pulling booking, revenue, feedback, and payment activity from the backend.
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  if (analytics === null) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="primary"
        title="Admin analytics"
        subtitle="Bookings, revenue, feedback, and payment workload."
      >
        <AppCard variant="subtle" className="mt-6 border border-red-100" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            Analytics unavailable
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-red-600">
            {error ?? 'The live analytics summary could not be loaded.'}
          </HeroText>
          {token ? (
            <AppButton
              className="mt-4"
              label="Retry"
              variant="outline"
              onPress={() => setLoadAttempt((current) => current + 1)}
            />
          ) : null}
        </AppCard>
      </AppScreen>
    );
  }

  return (
    <AppScreen
      tone="admin"
      headerVariant="primary"
      title="Admin analytics"
      subtitle="Bookings, revenue, feedback, and payment workload."
    >
      <AppSection
        eyebrow="Performance"
        title={`${periodDays}-day comparison`}
        rightAction={
          <View className="flex-row gap-2">
            {([7, 30] as const).map((days) => (
              <AppChip
                key={days}
                label={`${days} days`}
                variant={periodDays === days ? 'primary' : 'neutral'}
                accessibilityState={{ selected: periodDays === days }}
                onPress={() => setPeriodDays(days)}
              />
            ))}
          </View>
        }
      >
        <View className="flex-row flex-wrap gap-3">
          <MetricStatCard
            title="Bookings"
            value={String(analytics.period_bookings)}
            subtitle={`Previous ${periodDays} days: ${analytics.previous_period_bookings}`}
            icon={<BarChart3 size={20} color="#2F64B6" />}
          />
          <MetricStatCard
            title="Revenue"
            value={formatCurrency(analytics.period_revenue)}
            subtitle={`Previous: ${formatCurrency(analytics.previous_period_revenue)}`}
            icon={<BarChart3 size={20} color="#2F64B6" />}
          />
        </View>
      </AppSection>

      <AppSection eyebrow="Current" title="Operational snapshot">
        <View className="flex-row flex-wrap gap-3">
          <MetricStatCard
            title="Pending payment"
            value={String(analytics.pending_payment_count)}
            icon={<Clock3 size={20} color="#22766D" />}
            accentClassName="bg-[#E4F2F0]"
          />
          <MetricStatCard
            title="Ready pickup"
            value={String(analytics.ready_for_collection_count)}
            icon={<Gauge size={20} color="#6550B8" />}
            accentClassName="bg-[#ECE7FA]"
          />
          <MetricStatCard
            title="Repeat customers"
            value={String(analytics.repeat_customer_count)}
            icon={<BarChart3 size={20} color="#2F64B6" />}
          />
          <MetricStatCard
            title="Feedback score"
            value={
              analytics.average_feedback_score == null
                ? '—'
                : `${analytics.average_feedback_score}/5`
            }
            icon={<Gauge size={20} color="#6550B8" />}
          />
          <MetricStatCard
            title="Pending feedback"
            value={String(analytics.pending_feedback_count)}
            icon={<Clock3 size={20} color="#C98A2E" />}
          />
          <MetricStatCard
            title="Avg completion"
            value={
              analytics.average_completion_hours == null
                ? '—'
                : `${analytics.average_completion_hours}h`
            }
            icon={<Clock3 size={20} color="#22766D" />}
          />
        </View>
      </AppSection>
    </AppScreen>
  );
}
