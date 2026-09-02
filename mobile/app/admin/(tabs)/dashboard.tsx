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
  Bot,
  CircleDot,
  LogOut,
  ListTodo,
  ScanSearch,
  Search,
  MessageSquareText,
  Settings2,
  TimerReset,
  Undo2,
  Users,
} from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
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
    title: 'Admin AI',
    subtitle: 'Review live operations.',
    route: '/admin/assistant',
    icon: Bot,
  },
  {
    title: 'Check-in',
    subtitle: 'Receive a racket.',
    route: '/admin/check-in',
    icon: Undo2,
  },
  {
    title: 'Service queue',
    subtitle: 'Move jobs through stages.',
    route: '/admin/service-queue',
    icon: ListTodo,
  },
  {
    title: 'Bookings',
    subtitle: 'Update orders.',
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
    subtitle: 'Manage stock.',
    route: '/admin/inventory',
    icon: Boxes,
  },
  {
    title: 'Racket models',
    subtitle: 'Choose models for players.',
    route: '/admin/racket-models',
    icon: CircleDot,
  },
  {
    title: 'Feedback',
    subtitle: 'Review ratings.',
    route: '/admin/feedback',
    icon: MessageSquareText,
  },
  {
    title: 'Notifications',
    subtitle: 'Send updates.',
    route: '/admin/notifications',
    icon: BellRing,
  },
  {
    title: 'Recommendation runs',
    subtitle: 'Audit saved results.',
    route: '/admin/recommendations',
    icon: ScanSearch,
  },
  {
    title: 'Business hours',
    subtitle: 'Set shop availability.',
    route: '/admin/business-hours',
    icon: Clock3,
  },
  {
    title: 'Store settings',
    subtitle: 'Edit store details.',
    route: '/admin/settings',
    icon: Settings2,
  },
  {
    title: 'Users',
    subtitle: 'See registered users.',
    route: '/admin/users',
    icon: Users,
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
  const [toolQuery, setToolQuery] = useState('');

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
  const filteredActions = PRIMARY_ACTIONS.filter((action) => {
    const query = toolQuery.trim().toLowerCase();
    return !query || `${action.title} ${action.subtitle}`.toLowerCase().includes(query);
  });
  const hasImmediateWork = Boolean(
    analytics &&
      ((awaitingDropOffCount ?? 0) > 0 ||
        (readyForCollectionCount ?? 0) > 0 ||
        analytics.pending_payment_count > 0 ||
        analytics.low_stock_count > 0 ||
        analytics.unread_chats > 0),
  );

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
            router.replace('/auth/login');
          }}
        />
      }
    >
      <View className="gap-4">
        {analyticsError ? (
          <AppCard variant="subtle" padding="sm">
            <HeroText className="text-sm text-neutral-700">
              {analyticsError}
            </HeroText>
          </AppCard>
        ) : null}
        <AppCard
          variant="dark"
          padding="lg"
          className="overflow-hidden rounded-[24px]"
          onPress={() => router.push('/admin/service-queue')}
          accessibilityLabel="Open the service queue"
          accessibilityHint="Review jobs by service stage"
        >
          <View
            style={{ pointerEvents: 'none' }}
            className="absolute -right-12 -top-16 h-40 w-40 rounded-full bg-primary-500/25"
          />
          <View className="flex-row items-start justify-between gap-4">
            <View className="flex-1">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-secondary-100">
                Today’s work
              </HeroText>
              <HeroText className="mt-2 text-[24px] font-bold leading-[29px] tracking-tight text-white">
                {analytics ? `${inProgressCount} jobs on bench` : 'Live service status'}
              </HeroText>
              <HeroText className="mt-1 text-[13px] leading-[18px] text-secondary-100">
                Move work through each stage.
              </HeroText>
            </View>
            <View className="h-11 w-11 items-center justify-center rounded-[16px] bg-white/10">
              <TimerReset size={20} color="#FFFFFF" />
            </View>
          </View>

          <View className="mt-4 flex-row gap-2">
            <View className="flex-1 rounded-[12px] bg-white/10 px-3 py-2">
              <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-secondary-100">
                Awaiting
              </HeroText>
              <HeroText className="mt-1 text-[18px] font-bold text-white">
                {analytics ? awaitingDropOffCount : '—'}
              </HeroText>
            </View>
            <View className="flex-1 rounded-[12px] bg-white/10 px-3 py-2">
              <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-secondary-100">
                Ready
              </HeroText>
              <HeroText className="mt-1 text-[18px] font-bold text-white">
                {analytics ? readyForCollectionCount : '—'}
              </HeroText>
            </View>
            <View className="flex-1 items-end justify-center px-1">
              <HeroText className="text-[12px] font-semibold text-white">Open queue</HeroText>
              <ArrowRight size={18} color="#FFFFFF" />
            </View>
          </View>
        </AppCard>

        <AppSection
          eyebrow="NOW"
          title="Today’s operations"
          subtitle="Review live work before opening the full tool set."
          variant="compact"
        >
          <View className="gap-3">
            {(awaitingDropOffCount ?? 0) > 0 ? (
              <AppCard
                variant="highlighted"
                padding="md"
                onPress={() => router.push('/admin/check-in')}
              >
                <View className="flex-row items-center gap-2.5">
                  <View className="h-10 w-10 items-center justify-center rounded-[12px] bg-primary-600">
                    <Undo2 size={18} color="#FFFFFF" />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-sm font-semibold text-slate-900">
                      Receive {awaitingDropOffCount} waiting racket{awaitingDropOffCount === 1 ? '' : 's'}
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                      Move waiting jobs to the service bench.
                    </HeroText>
                  </View>
                  <ArrowRight size={17} color={appChromeColors.primary} />
                </View>
              </AppCard>
            ) : null}

            {(readyForCollectionCount ?? 0) > 0 ? (
              <AppCard
                variant="elevated"
                padding="md"
                onPress={() => router.push('/admin/service-queue')}
              >
                <View className="flex-row items-center gap-2.5">
                  <View className="h-10 w-10 items-center justify-center rounded-[12px] border border-primary-200 bg-primary-50">
                    <TimerReset size={18} color={appChromeColors.primary} />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-sm font-semibold text-slate-900">
                      {readyForCollectionCount} order{readyForCollectionCount === 1 ? '' : 's'} ready for collection
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                      Confirm the handover.
                    </HeroText>
                  </View>
                  <ArrowRight size={17} color={appChromeColors.textMuted} />
                </View>
              </AppCard>
            ) : null}

            {analytics ? (
              <AppCard
                variant="elevated"
                padding="md"
                onPress={() => router.push('/admin/bookings')}
              >
                <View className="flex-row items-center gap-2.5">
                  <View className="h-10 w-10 items-center justify-center rounded-[12px] border border-primary-200 bg-primary-50">
                    <CalendarRange size={18} color={appChromeColors.primary} />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-sm font-semibold text-slate-900">
                      {analytics.today_bookings} booking{analytics.today_bookings === 1 ? '' : 's'} scheduled today
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                      {analytics.completed_today} completed today.
                    </HeroText>
                  </View>
                  <ArrowRight size={17} color={appChromeColors.textMuted} />
                </View>
              </AppCard>
            ) : null}

            {(analytics?.pending_payment_count ?? 0) > 0 ? (
              <AppCard
                variant="elevated"
                padding="md"
                onPress={() => router.push('/admin/payments')}
              >
                <View className="flex-row items-center gap-2.5">
                  <View className="h-10 w-10 items-center justify-center rounded-[12px] bg-warning-50">
                    <CreditCard size={18} color={appChromeColors.warning} />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-sm font-semibold text-slate-900">
                      Verify {analytics?.pending_payment_count} pending payment{analytics?.pending_payment_count === 1 ? '' : 's'}
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                      Verify the pending request.
                    </HeroText>
                  </View>
                  <ArrowRight size={17} color={appChromeColors.textMuted} />
                </View>
              </AppCard>
            ) : null}

            {(analytics?.low_stock_count ?? 0) > 0 ? (
              <AppCard
                variant="elevated"
                padding="md"
                onPress={() => router.push('/admin/inventory')}
              >
                <View className="flex-row items-center gap-2.5">
                  <View className="h-10 w-10 items-center justify-center rounded-[12px] bg-warning-50">
                    <Boxes size={18} color={appChromeColors.warning} />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-sm font-semibold text-slate-900">
                      {analytics?.low_stock_count} string{analytics?.low_stock_count === 1 ? '' : 's'} below the reorder level
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                      Review low stock.
                    </HeroText>
                  </View>
                  <ArrowRight size={17} color={appChromeColors.textMuted} />
                </View>
              </AppCard>
            ) : null}

            {(analytics?.unread_chats ?? 0) > 0 ? (
              <AppCard
                variant="elevated"
                padding="md"
                onPress={() => router.push('/admin/chat')}
              >
                <View className="flex-row items-center gap-2.5">
                  <View className="h-10 w-10 items-center justify-center rounded-[12px] bg-primary-50">
                    <MessageSquareText size={18} color={appChromeColors.primary} />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-sm font-semibold text-slate-900">
                      Reply to {analytics?.unread_chats} unread conversation{analytics?.unread_chats === 1 ? '' : 's'}
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                      Reply to waiting players.
                    </HeroText>
                  </View>
                  <ArrowRight size={17} color={appChromeColors.textMuted} />
                </View>
              </AppCard>
            ) : null}

            {analytics && !hasImmediateWork ? (
              <AppCard variant="subtle" padding="md">
                <HeroText className="text-sm font-semibold text-slate-900">
                  The counter is clear.
                </HeroText>
                <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                  No drop-offs, collections, payments, stock alerts, feedback follow-ups, or unread conversations need action.
                </HeroText>
              </AppCard>
            ) : null}
          </View>
        </AppSection>

        <AppSection
          eyebrow="ALL TOOLS"
          title="All tools"
          subtitle="Search every operation."
          rightAction={
            <AppChip
              label={`${filteredActions.length} tools`}
              variant="secondary"
              className="mt-1"
            />
          }
          variant="compact"
        >
          <View className="gap-3">
            <AppInput
              variant="minimal"
              className="mb-0"
              label="Search tools"
              placeholder="Search tools, inventory, or hours"
              value={toolQuery}
              onChangeText={setToolQuery}
              leftAdornment={<Search size={18} color={appChromeColors.textMuted} />}
            />
            <View className="gap-2">
            {filteredActions.map((action) => {
              const Icon = action.icon;

              return (
                <AppCard
                  key={action.title}
                  variant={action.title === 'Check-in' ? 'highlighted' : 'elevated'}
                  padding="sm"
                  className="w-full"
                  contentClassName="min-h-[64px] flex-row items-center gap-2.5"
                  onPress={() => router.push(action.route as never)}
                >
                  <View
                    className={
                      action.title === 'Check-in'
                        ? 'h-10 w-10 items-center justify-center rounded-[12px] bg-primary-600'
                        : 'h-10 w-10 items-center justify-center rounded-[12px] border border-primary-200 bg-primary-50'
                    }
                  >
                    <Icon
                      size={18}
                      color={action.title === 'Check-in' ? '#FFFFFF' : appChromeColors.primary}
                    />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-sm font-semibold leading-5 tracking-tight text-slate-900">
                      {action.title}
                    </HeroText>
                    <HeroText className="mt-1 text-[12px] leading-[17px] text-slate-600" numberOfLines={2}>
                      {action.subtitle}
                    </HeroText>
                  </View>
                </AppCard>
              );
            })}
            {filteredActions.length === 0 ? (
              <AppCard variant="subtle" padding="md" className="w-full">
                <HeroText className="text-sm font-semibold text-slate-900">
                  No matching tool
                </HeroText>
                <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                  Try a broader name such as booking, stock, or settings.
                </HeroText>
              </AppCard>
            ) : null}
            </View>
          </View>
        </AppSection>
      </View>
    </AppScreen>
  );
}
