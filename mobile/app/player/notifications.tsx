import React, { useCallback, useState } from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import {
  BellRing,
  CalendarClock,
  ChevronRight,
  CircleDollarSign,
  MessageCircle,
  Sparkles,
  Wrench,
  type LucideIcon,
} from 'lucide-react-native';
import { AppCard } from '../../components/ui/AppCard';
import { AppButton } from '../../components/ui/AppButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../components/shared/AppScreen';
import { formatDateTime, formatLabel } from '../../lib/formatters';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useNotifications,
} from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendNotificationToNotification } from '../../services/backendMappers';
import type { NotificationItem } from '../../types/domain';

const notificationCategoryMeta: Record<
  NotificationItem['category'],
  { Icon: LucideIcon; color: string; surfaceClassName: string }
> = {
  booking: { Icon: CalendarClock, color: '#2563EB', surfaceClassName: 'bg-primary-100' },
  payment: { Icon: CircleDollarSign, color: '#047857', surfaceClassName: 'bg-emerald-100' },
  service: { Icon: Wrench, color: '#B45309', surfaceClassName: 'bg-amber-100' },
  chat: { Icon: MessageCircle, color: '#7C3AED', surfaceClassName: 'bg-violet-100' },
  recommendation: { Icon: Sparkles, color: '#2563EB', surfaceClassName: 'bg-primary-100' },
  system: { Icon: BellRing, color: '#475569', surfaceClassName: 'bg-slate-100' },
};

export default function NotificationsScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const notifications = useNotifications();
  const setLiveNotifications = useAppStore((state) => state.setLiveNotifications);
  const [isRefreshing, setIsRefreshing] = useState(Boolean(token));
  const [markingId, setMarkingId] = useState<string | null>(null);
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshNotifications = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsRefreshing(true);
    setError(null);
    try {
      const response = await backendApi.listNotifications(token);
      setLiveNotifications(response.map(mapBackendNotificationToNotification));
    } catch (loadError) {
      setError(
        loadError instanceof BackendApiError
          ? loadError.message
          : 'Failed to load notifications.',
      );
    } finally {
      setIsRefreshing(false);
    }
  }, [setLiveNotifications, token]);

  useFocusEffect(
    useCallback(() => {
      void refreshNotifications();
    }, [refreshNotifications]),
  );

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerNotifications = notifications.filter((item) => item.userId === user.id);
  const unreadCount = playerNotifications.filter((item) => !item.read).length;
  const orderedNotifications = [...playerNotifications].sort(
    (left, right) => Number(left.read) - Number(right.read),
  );

  const openNotification = async (item: NotificationItem) => {
    if (!token) {
      setError('Your player session expired. Sign in again to open notifications.');
      return;
    }

    if (!item.read) {
      setMarkingId(item.id);
      setError(null);
      try {
        await backendApi.markNotificationsRead(token, { event_ids: [item.id] });
        setLiveNotifications(
          useAppStore
            .getState()
            .liveNotifications.map((notification) =>
              notification.id === item.id
                ? { ...notification, read: true }
                : notification,
            ),
        );
      } catch (readError) {
        setError(
          readError instanceof BackendApiError
            ? readError.message
            : 'Failed to mark the notification as read.',
        );
      } finally {
        setMarkingId(null);
      }
    }

    router.push(item.route as never);
  };

  const markAllAsRead = async () => {
    if (unreadCount === 0 || markingId !== null || isMarkingAll) {
      return;
    }

    if (!token) {
      setError('Your player session expired. Sign in again to mark notifications as read.');
      return;
    }

    const unreadIds = playerNotifications
      .filter((item) => !item.read)
      .map((item) => item.id);

    setIsMarkingAll(true);
    setError(null);
    try {
      const response = await backendApi.markNotificationsRead(token, {
        event_ids: unreadIds,
      });
      const markedIds = new Set(response.marked_read_ids);
      setLiveNotifications(
        useAppStore
          .getState()
          .liveNotifications.map((notification) =>
            markedIds.has(notification.id)
              ? { ...notification, read: true }
              : notification,
          ),
      );
    } catch (readError) {
      setError(
        readError instanceof BackendApiError
          ? readError.message
          : 'Failed to mark all notifications as read.',
      );
    } finally {
      setIsMarkingAll(false);
    }
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Notifications"
      subtitle="Bookings, payments, messages, and recommendation updates."
      showBackButton
      onBackPress={() => router.back()}
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={orderedNotifications}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        refreshing={isRefreshing}
        onRefresh={() => void refreshNotifications()}
        ListHeaderComponent={
          <View className="pb-3">
            <View className="mb-3 flex-row items-center justify-between gap-3">
              <View className="flex-1">
                <HeroText className="text-base font-semibold tracking-tight text-neutral-950">
                  Latest updates
                </HeroText>
                <HeroText className="mt-0.5 text-sm leading-5 text-neutral-500">
                  {unreadCount > 0
                    ? `${unreadCount} unread ${unreadCount === 1 ? 'update' : 'updates'} need your attention.`
                    : 'You are all caught up.'}
                </HeroText>
              </View>
              {unreadCount > 0 ? (
                <View className="items-end gap-1">
                  <View className="rounded-full bg-primary-100 px-3 py-1.5">
                    <HeroText className="text-xs font-semibold text-primary-700">
                      {unreadCount} new
                    </HeroText>
                  </View>
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel="Mark all notifications as read"
                    accessibilityHint="Mark all unread notifications as read"
                    accessibilityState={{ busy: isMarkingAll, disabled: isMarkingAll || markingId !== null }}
                    className="min-h-11 justify-center px-2"
                    disabled={isMarkingAll || markingId !== null}
                    onPress={() => void markAllAsRead()}
                  >
                    <HeroText className="text-xs font-semibold text-primary-700">
                      {isMarkingAll ? 'Marking…' : 'Mark all read'}
                    </HeroText>
                  </Pressable>
                </View>
              ) : null}
            </View>

            {error ? (
              <AppCard
                variant="subtle"
                className="border border-red-100"
                padding="md"
              >
                <HeroText className="text-sm font-medium leading-6 text-red-600">
                  {error}
                </HeroText>
                {token ? (
                  <AppButton
                    label="Retry"
                    variant="outline"
                    className="mt-3"
                    onPress={() => void refreshNotifications()}
                  />
                ) : null}
              </AppCard>
            ) : null}
          </View>
        }
        renderItem={({ item }) => {
          const meta = notificationCategoryMeta[item.category];
          const CategoryIcon = meta.Icon;

          return (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${item.read ? 'Read' : 'Unread'} ${formatLabel(item.category)} notification. ${item.title}. ${item.body}`}
              accessibilityHint="Open this notification"
              accessibilityState={{ busy: markingId === item.id, disabled: markingId !== null }}
              className="mb-2"
              disabled={markingId !== null}
              onPress={() => void openNotification(item)}
            >
              <AppCard variant={item.read ? 'default' : 'highlighted'} padding="none">
                <View className="flex-row items-center gap-3 px-3 py-3">
                  <View className={`h-10 w-10 items-center justify-center rounded-[12px] ${meta.surfaceClassName}`}>
                    <CategoryIcon size={19} color={meta.color} strokeWidth={2.25} />
                  </View>
                  <View className="min-w-0 flex-1">
                    <View className="flex-row items-center gap-2">
                      <HeroText
                        className="min-w-0 flex-1 text-[15px] font-semibold tracking-tight text-neutral-950"
                        numberOfLines={1}
                      >
                        {item.title}
                      </HeroText>
                      {!item.read ? <View className="h-2 w-2 rounded-full bg-primary-600" /> : null}
                    </View>
                    <HeroText
                      className="mt-0.5 text-[13px] leading-5 text-neutral-600"
                      numberOfLines={2}
                    >
                      {item.body}
                    </HeroText>
                    <HeroText className="mt-1 text-[11px] font-medium text-neutral-500">
                      {formatLabel(item.category)} · {formatDateTime(item.createdAt)}
                    </HeroText>
                  </View>
                  <ChevronRight size={18} color="#94A3B8" />
                </View>
              </AppCard>
            </Pressable>
          );
        }}
        ListEmptyComponent={
          <AppCard variant="subtle" className="mb-4" padding="md">
            <HeroText className="text-base font-semibold text-neutral-900">
              {isRefreshing ? 'Loading notifications...' : 'No notifications yet'}
            </HeroText>
            <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
              {error
                ? 'Retry to load the latest notification activity.'
                : 'Booking, payment, chat, and recommendation updates will appear here.'}
            </HeroText>
          </AppCard>
        }
      />
    </AppScreen>
  );
}
