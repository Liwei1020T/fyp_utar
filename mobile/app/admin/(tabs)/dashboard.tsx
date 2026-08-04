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
    title: 'Check-in',
    subtitle: 'Receive a racket at the counter.',
    route: '/admin/check-in',
    icon: Undo2,
  },
  {
    title: 'Service queue',
    subtitle: 'View jobs by service stage.',
    route: '/admin/service-queue',
    icon: ListTodo,
  },
  {
    title: 'Bookings',
    subtitle: 'Update orders and status.',
    route: '/admin/bookings',
    icon: CalendarRange,
  },
  {
    title: 'Payments',
    subtitle: 'Verify payment requests.',
    route: '/admin/payments',
    icon: CreditCard,
  },
  {
    title: 'Inventory',
    subtitle: 'Manage strings and stock.',
    route: '/admin/inventory',
    icon: Boxes,
  },
  {
    title: 'Feedback',
    subtitle: 'Review player ratings.',
    route: '/admin/feedback',
    icon: MessageSquareText,
  },
  {
    title: 'Notifications',
    subtitle: 'Send player updates.',
    route: '/admin/notifications',
    icon: BellRing,
  },
  {
    title: 'Recommendation runs',
    subtitle: 'Audit saved AI results.',
    route: '/admin/recommendations',
    icon: ScanSearch,
  },
  {
    title: 'Business hours',
    subtitle: 'Adjust shop availability.',
    route: '/admin/business-hours',
    icon: Clock3,
  },
  {
    title: 'Store settings',
    subtitle: 'Edit details and policies.',
    route: '/admin/settings',
    icon: Settings2,
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
        <AppSection
          eyebrow="All features"
          title="Choose a counter task"
          subtitle="Every admin tool starts here; daily counter work comes first."
          rightAction={
            <AppChip
              label={analytics ? `${awaitingDropOffCount} awaiting` : '— awaiting'}
              variant="warning"
              className="mt-1"
            />
          }
          variant="compact"
        >
          <View className="flex-row flex-wrap gap-3">
            {analytics?.pending_feedback_count ? (
              <AppCard
                variant="highlighted"
                padding="md"
                className="w-full"
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
                  padding="sm"
                  className="w-[48%]"
                  contentClassName="min-h-[128px] justify-between"
                  onPress={() => router.push(action.route as never)}
                >
                  <View
                    className={
                      action.title === 'Check-in'
                        ? 'h-11 w-11 items-center justify-center rounded-[16px] bg-primary-600'
                        : 'h-11 w-11 items-center justify-center rounded-[16px] border border-primary-200 bg-primary-50'
                    }
                  >
                    <Icon
                      size={19}
                      color={action.title === 'Check-in' ? '#FFFFFF' : appChromeColors.primary}
                    />
                  </View>
                  <View className="mt-3">
                    <HeroText className="text-[15px] font-semibold leading-5 tracking-tight text-slate-900">
                      {action.title}
                    </HeroText>
                    <HeroText className="mt-1 text-[12px] leading-[17px] text-slate-600" numberOfLines={2}>
                      {action.subtitle}
                    </HeroText>
                  </View>
                </AppCard>
              );
            })}
          </View>
        </AppSection>

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
          </View>
        </AppSection>
      </View>
    </AppScreen>
  );
}
