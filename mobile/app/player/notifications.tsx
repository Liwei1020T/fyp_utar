import React, { useCallback, useState } from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { ChevronRight } from 'lucide-react-native';
import { AppCard } from '../../components/ui/AppCard';
import { AppButton } from '../../components/ui/AppButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../components/shared/AppScreen';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useNotifications,
} from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendNotificationToNotification } from '../../services/backendMappers';
import type { NotificationItem } from '../../types/domain';

export default function NotificationsScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const notifications = useNotifications();
  const setLiveNotifications = useAppStore((state) => state.setLiveNotifications);
  const [isRefreshing, setIsRefreshing] = useState(Boolean(token));
  const [markingId, setMarkingId] = useState<string | null>(null);
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

  return (
    <AppScreen
      headerVariant="primary"
      title="Notifications"
      subtitle="In-app alerts for bookings, payments, chat replies, and recommendation nudges."
      showBackButton
      onBackPress={() => router.back()}
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={playerNotifications}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        refreshing={isRefreshing}
        onRefresh={() => void refreshNotifications()}
        ListHeaderComponent={
          error ? (
            <AppCard
              variant="subtle"
              className="mb-4 border border-red-100"
              padding="md"
            >
              <HeroText className="text-sm font-medium leading-6 text-red-600">
                {error}
              </HeroText>
              {token ? (
                <AppButton
                  label="Retry"
                  variant="outline"
                  className="mt-4"
                  onPress={() => void refreshNotifications()}
                />
              ) : null}
            </AppCard>
          ) : null
        }
        renderItem={({ item }) => (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`${item.title}. ${item.body}`}
            accessibilityHint="Open this notification"
            accessibilityState={{ disabled: markingId !== null }}
            disabled={markingId !== null}
            onPress={() => void openNotification(item)}
          >
            <AppCard variant={item.read ? 'elevated' : 'highlighted'} className="mb-4" padding="md">
              <View className="flex-row items-start justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                    {item.title}
                  </HeroText>
                  <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
                    {item.body}
                  </HeroText>
                </View>
                <ChevronRight size={18} color="#94A3B8" />
              </View>
            </AppCard>
          </Pressable>
        )}
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
