import React from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, ChevronRight, Settings2 } from 'lucide-react-native';
import { AppCard } from '../../components/ui/AppCard';
import { AppButton } from '../../components/ui/AppButton';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../components/shared/AppScreen';
import { useAppStore, useCurrentUser, useNotifications } from '../../store/appStore';

export default function NotificationsScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const user = useCurrentUser();
  const notifications = useNotifications();
  const markNotificationRead = useAppStore((state) => state.markNotificationRead);

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerNotifications = notifications.filter((item) => item.userId === user.id);

  return (
    <AppScreen
      headerVariant="primary"
      title="Notifications"
      subtitle="In-app alerts for bookings, payments, chat replies, and recommendation nudges."
      headerRight={
        <AppIconButton
          icon={<Settings2 size={20} color="#475569" />}
          accessibilityLabel="Open notification preferences"
          onPress={() => router.push('/player/notifications/preferences')}
        />
      }
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={playerNotifications}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        renderItem={({ item }) => (
          <Pressable
            onPress={() => {
              markNotificationRead(item.id);
              router.push(item.route as never);
            }}
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
        ListFooterComponent={
          <AppButton
            label="Notification preferences"
            variant="outline"
            size="lg"
            onPress={() => router.push('/player/notifications/preferences')}
          />
        }
      />
    </AppScreen>
  );
}
