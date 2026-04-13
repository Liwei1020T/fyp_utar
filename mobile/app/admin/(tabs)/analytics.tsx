import React, { useEffect, useMemo, useState } from 'react';
import { View } from 'react-native';
import { BarChart3, Clock3, Flame, Gauge } from 'lucide-react-native';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { MetricStatCard } from '../../../components/analytics/MetricStatCard';
import { AppCard } from '../../../components/ui/AppCard';
import { HeroText } from '../../../components/ui/heroui';
import { useBackendAccessToken, useCurrentUser, useStrings } from '../../../store/appStore';
import { formatCurrency } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import type { BackendAnalyticsSummary, BackendPopularString } from '../../../types/backend';

export default function AdminAnalyticsScreen() {
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const [analytics, setAnalytics] = useState<BackendAnalyticsSummary | null>(null);
  const [popularStrings, setPopularStrings] = useState<BackendPopularString[]>([]);
  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [hasLoadedAnalytics, setHasLoadedAnalytics] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) {
      setAnalytics(null);
      setPopularStrings([]);
      setIsLoading(false);
      setHasLoadedAnalytics(false);
      setError(null);
      return;
    }

    if (!token) {
      setAnalytics(null);
      setPopularStrings([]);
      setIsLoading(false);
      setHasLoadedAnalytics(false);
      setError('Backend login is required to view live analytics.');
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [summary, popular] = await Promise.all([
          backendApi.adminAnalyticsSummary(token),
          backendApi.adminPopularStrings(token),
        ]);
        if (cancelled) {
          return;
        }
        setAnalytics(summary);
        setPopularStrings(popular);
        setHasLoadedAnalytics(true);
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof BackendApiError
              ? loadError.message
              : 'Failed to load analytics.',
          );
          setHasLoadedAnalytics(true);
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
  }, [isAdmin, token]);

  const popularStringCards = useMemo(
    () =>
      popularStrings.map((item) => {
        const catalogString = strings.find((entry) => entry.id === item.string_id);
        return {
          id: item.string_id,
          label:
            catalogString != null
              ? `${catalogString.brand} ${catalogString.model}`
              : `${item.brand} ${item.model_name}`,
          bookingCount: item.booking_count,
        };
      }),
    [popularStrings, strings],
  );

  if (!isAdmin) {
    return null;
  }

  if (token && !hasLoadedAnalytics && isLoading) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="primary"
        title="Admin analytics"
        subtitle="Operations trends, busy slots, popular strings, and payment workload."
      >
        <AppCard variant="subtle" className="mt-6" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            Loading live analytics...
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Pulling bookings, revenue, and popular-string activity from the backend.
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  return (
    <AppScreen tone="admin" headerVariant="primary" title="Admin analytics" subtitle="Operations trends, busy slots, popular strings, and payment workload." >
      {error ? (
        <AppCard variant="subtle" className="mb-6 border border-red-100" padding="md">
          <HeroText className="text-sm font-medium text-red-600">
            {error}
          </HeroText>
        </AppCard>
      ) : null}

      <AppSection eyebrow="Metrics" title="Shop performance">
        <View className="flex-row flex-wrap gap-3">
          <MetricStatCard title="Weekly bookings" value={String(analytics?.weekly_bookings ?? 0)} icon={<BarChart3 size={20} color="#2F64B6" />} />
          <MetricStatCard title="Pending payment" value={String(analytics?.pending_payment_count ?? 0)} icon={<Clock3 size={20} color="#22766D" />} accentClassName="bg-[#E4F2F0]" />
          <MetricStatCard title="Ready pickup" value={String(analytics?.ready_for_collection_count ?? 0)} icon={<Gauge size={20} color="#6550B8" />} accentClassName="bg-[#ECE7FA]" />
          <MetricStatCard title="Revenue" value={formatCurrency(analytics?.today_revenue ?? 0)} icon={<BarChart3 size={20} color="#2F64B6" />} />
        </View>
      </AppSection>

      <AppSection eyebrow="Demand" title="Popular strings">
        <View className="gap-3">
          {popularStringCards.map((item) => (
            <AppCard key={item.id} variant="elevated" padding="sm">
              <HeroText className="text-sm font-semibold text-neutral-900">
                {item.label}
              </HeroText>
              <HeroText className="mt-1 text-xs font-medium text-neutral-500">
                {item.bookingCount} booking{item.bookingCount === 1 ? '' : 's'}
              </HeroText>
            </AppCard>
          ))}
          {!isLoading && popularStringCards.length === 0 ? (
            <AppCard variant="subtle" padding="sm">
              <HeroText className="text-sm text-neutral-600">
                No popular string data is available yet.
              </HeroText>
            </AppCard>
          ) : null}
        </View>
      </AppSection>

      <AppSection eyebrow="Busy slots" title="When the desk gets crowded">
        <View className="gap-3">
          {analytics?.busy_slots.map((slot) => (
            <AppCard key={slot} variant="highlighted" padding="sm">
              <View className="flex-row items-center gap-3">
                <Flame size={18} color="#C98A2E" />
                <HeroText className="text-sm font-semibold text-neutral-900">{slot}</HeroText>
              </View>
            </AppCard>
          ))}
          {!isLoading && (analytics?.busy_slots.length ?? 0) === 0 ? (
            <AppCard variant="subtle" padding="sm">
              <HeroText className="text-sm text-neutral-600">
                Busy-slot analytics will appear after more booking activity is recorded.
              </HeroText>
            </AppCard>
          ) : null}
        </View>
      </AppSection>
    </AppScreen>
  );
}
