import React, { useCallback, useState } from 'react';
import { View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import {
  ArrowRight,
  Boxes,
  CalendarRange,
  Clock3,
  CreditCard,
  BellRing,
  LogOut,
  ListTodo,
  ScanSearch,
  MessageSquareText,
  Settings2,
  Store,
  TimerReset,
  Undo2,
} from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { MetricStatCard } from '../../../components/analytics/MetricStatCard';
import { appChromeColors } from '../../../components/ui/theme';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
} from '../../../store/appStore';
import { backendApi } from '../../../services/backendApi';
import type { BackendAnalyticsSummary } from '../../../types/backend';

const PRIMARY_ACTIONS = [
  {
    title: 'Feedback',
    subtitle: 'Review satisfaction scores and low-rating cases.',
    route: '/admin/feedback',
    icon: MessageSquareText,
    variant: 'outline' as const,
  },
  {
    title: 'Notifications',
    subtitle: 'Inspect devices, delivery logs, and resend failures.',
    route: '/admin/notifications',
    icon: BellRing,
    variant: 'outline' as const,
  },
  {
    title: 'Check-in',
    subtitle: 'Confirm player racket drop-off at the counter.',
    route: '/admin/check-in',
    icon: Undo2,
    variant: 'dark' as const,
  },
  {
    title: 'Bookings',
    subtitle: 'Update service status and monitor the queue.',
    route: '/admin/bookings',
    icon: CalendarRange,
    variant: 'outline' as const,
  },
  {
    title: 'Service queue',
    subtitle: 'See active rackets grouped by service stage.',
    route: '/admin/service-queue',
    icon: ListTodo,
    variant: 'outline' as const,
  },
  {
    title: 'Payments',
    subtitle: 'Verify pending payments and wallet top-ups.',
    route: '/admin/payments',
    icon: CreditCard,
    variant: 'outline' as const,
  },
  {
    title: 'Inventory',
    subtitle: 'Review string stock and low-stock items.',
    route: '/admin/inventory',
    icon: Boxes,
    variant: 'outline' as const,
  },
  {
    title: 'Business hours',
    subtitle: 'Adjust slots and store availability windows.',
    route: '/admin/business-hours',
    icon: Clock3,
    variant: 'outline' as const,
  },
  {
    title: 'Store settings',
    subtitle: 'Edit store profile, notes, and policies.',
    route: '/admin/settings',
    icon: Settings2,
    variant: 'outline' as const,
  },
];

export default function AdminDashboardScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const logout = useAppStore((state) => state.logout);
  const settings = useAppStore((state) => state.storeSettings);
  const storeName = settings?.storeName.trim();
  const [analytics, setAnalytics] = useState<BackendAnalyticsSummary | null>(
    null,
  );
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      if (!token || user?.role !== 'admin') return;
      let cancelled = false;
      setAnalytics(null);
      setAnalyticsError(null);
      void backendApi
        .adminAnalyticsSummary(token)
        .then((response) => {
          if (!cancelled) setAnalytics(response);
        })
        .catch(() => {
          if (!cancelled) {
            setAnalytics(null);
            setAnalyticsError(
              'Live operational metrics are temporarily unavailable.',
            );
          }
        });
      return () => {
        cancelled = true;
      };
    }, [token, user?.role]),
  );

  if (!user || user.role !== 'admin') {
    return null;
  }

  const awaitingDropOffCount = analytics?.awaiting_dropoff_count;
  const inProgressCount = analytics?.in_progress_count;
  const readyForCollectionCount = analytics?.ready_for_collection_count;
  const lowStockCount = analytics?.low_stock_count;

  return (
    <AppScreen
      tone="admin"
      headerVariant="primary"
      title="Admin overview"
      subtitle={
        storeName ? `${storeName} counter operations.` : 'Store counter operations.'
      }
      headerRight={
        <AppIconButton
          icon={<LogOut size={20} color={appChromeColors.danger} />}
          accessibilityLabel="Log out"
          onPress={() => {
            logout();
            router.replace('/auth/welcome');
          }}
        />
      }
    >
      <View className="gap-5">
        {analyticsError ? (
          <AppCard variant="subtle" padding="sm">
            <HeroText className="text-sm text-neutral-700">
              {analyticsError}
            </HeroText>
          </AppCard>
        ) : null}
        <AppSection eyebrow="Today" title="Operational snapshot" variant="compact">
          <View className="flex-row flex-wrap gap-3">
            <MetricStatCard
              title="Today bookings"
              value={analytics ? String(analytics.today_bookings) : '—'}
              icon={<CalendarRange size={20} color={appChromeColors.primary} />}
            />
            <MetricStatCard
              title="Pending feedback"
              value={analytics ? String(analytics.pending_feedback_count) : '—'}
              icon={<MessageSquareText size={20} color={appChromeColors.warning} />}
              accentClassName="bg-warning-50"
            />
            <MetricStatCard
              title="Awaiting drop-off"
              value={analytics ? String(awaitingDropOffCount) : '—'}
              icon={<Undo2 size={20} color={appChromeColors.warning} />}
              accentClassName="bg-warning-50"
            />
            <MetricStatCard
              title="In progress"
              value={analytics ? String(inProgressCount) : '—'}
              icon={<TimerReset size={20} color={appChromeColors.primary} />}
              accentClassName="bg-primary-50"
            />
            <MetricStatCard
              title="Ready pickup"
              value={analytics ? String(readyForCollectionCount) : '—'}
              icon={<Store size={20} color={appChromeColors.success} />}
              accentClassName="bg-success-50"
            />
          </View>
        </AppSection>

        <AppSection
          eyebrow="Primary actions"
          title="Start with the counter flow"
          subtitle="Keep the work queue, counter flow, and store setup close at hand."
          rightAction={
            <AppChip
              label={analytics ? `${awaitingDropOffCount} awaiting` : '— awaiting'}
              variant="warning"
              className="mt-1"
            />
          }
          variant="compact"
        >
          <View className="gap-3">
            {analytics?.pending_feedback_count ? (
              <AppCard
                variant="highlighted"
                padding="md"
                onPress={() => router.push('/admin/feedback')}
              >
                <View className="flex-row items-center gap-3">
                  <View className="h-10 w-10 items-center justify-center rounded-[16px] bg-warning-50">
                    <MessageSquareText size={18} color={appChromeColors.warning} />
                  </View>
                  <View className="flex-1">
                    <HeroText className="text-[14px] font-semibold tracking-tight text-slate-900">
                      {analytics.pending_feedback_count} feedback items to review
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                      Open the feedback queue and start with low-satisfaction cases.
                    </HeroText>
                  </View>
                  <ArrowRight size={16} color={appChromeColors.textMuted} />
                </View>
              </AppCard>
            ) : null}
            {PRIMARY_ACTIONS.map((action) => {
              const Icon = action.icon;

              return (
                <AppCard
                  key={action.title}
                  variant={action.title === 'Check-in' ? 'highlighted' : 'elevated'}
                  padding="md"
                  onPress={() => router.push(action.route as never)}
                >
                  <View className="flex-row items-center justify-between gap-4">
                    <View className="flex-row items-center gap-3 flex-1">
                      <View
                        className={
                          action.title === 'Check-in'
                            ? 'h-12 w-12 items-center justify-center rounded-[18px] bg-primary-600'
                            : 'h-12 w-12 items-center justify-center rounded-[18px] border border-primary-200 bg-primary-50'
                        }
                      >
                        <Icon
                          size={20}
                          color={action.title === 'Check-in' ? '#FFFFFF' : appChromeColors.primary}
                        />
                      </View>
                      <View className="flex-1">
                        <HeroText className="text-[16px] font-semibold tracking-tight text-slate-900">
                          {action.title}
                        </HeroText>
                        <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                          {action.subtitle}
                        </HeroText>
                      </View>
                    </View>
                    <ArrowRight size={16} color={appChromeColors.textMuted} />
                  </View>
                </AppCard>
              );
            })}
          </View>
        </AppSection>

        <AppSection eyebrow="Highlights" title="What needs attention?" className="mb-12" variant="compact">
          <View className="gap-3">
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center gap-3">
                <Undo2 size={18} color={appChromeColors.warning} />
                <HeroText className="flex-1 text-sm leading-6 text-slate-600">
                  {analytics
                    ? `${awaitingDropOffCount} booking${awaitingDropOffCount === 1 ? '' : 's'} waiting for racket drop-off.`
                    : 'Live booking metrics are unavailable.'}
                </HeroText>
              </View>
            </AppCard>
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center gap-3">
                <Clock3 size={18} color={appChromeColors.primary} />
                <HeroText className="flex-1 text-sm leading-6 text-slate-600">
                  {analytics
                    ? `${inProgressCount} job${inProgressCount === 1 ? '' : 's'} currently on the stringing bench.`
                    : 'Live service metrics are unavailable.'}
                </HeroText>
              </View>
            </AppCard>
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center gap-3">
                <Boxes size={18} color={appChromeColors.warning} />
                <HeroText className="flex-1 text-sm leading-6 text-slate-600">
                  {analytics
                    ? `${lowStockCount} string SKU${lowStockCount === 1 ? '' : 's'} flagged for stock review.`
                    : 'Live inventory metrics are unavailable.'}
                </HeroText>
              </View>
            </AppCard>
            <AppCard variant="elevated" padding="md" onPress={() => router.push('/admin/recommendations')}>
              <View className="flex-row items-center gap-3">
                <View className="h-10 w-10 items-center justify-center rounded-[16px] bg-primary-50">
                  <ScanSearch size={18} color={appChromeColors.primary} />
                </View>
                <View className="flex-1">
                  <HeroText className="text-[14px] font-semibold tracking-tight text-slate-900">
                    Recommendation runs
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                    Review saved recommendation histories, profile snapshots, and score breakdowns.
                  </HeroText>
                </View>
                <ArrowRight size={16} color={appChromeColors.textMuted} />
              </View>
            </AppCard>
          </View>
        </AppSection>
      </View>
    </AppScreen>
  );
}
