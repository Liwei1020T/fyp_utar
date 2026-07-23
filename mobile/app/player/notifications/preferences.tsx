import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { useAppStore, useCurrentUser } from '../../../store/appStore';
import type { NotificationPreferences } from '../../../types/domain';
import { formatLabel } from '../../../lib/formatters';

export default function NotificationPreferencesScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const settings = useAppStore((state) =>
    state.notificationPreferences.find((item) => item.userId === user?.id)
  );
  const updateNotificationPreferences = useAppStore(
    (state) => state.updateNotificationPreferences
  );

  if (!user || user.role !== 'player' || !settings) {
    return null;
  }

  return (
    <AppScreen
      headerVariant="flow"
      title="Notification preferences"
      subtitle="Frontend-only toggles that preview how notification controls could feel later."
      showBackButton
      onBackPress={() => router.back()}
    >
      <View className="gap-3">
        {Object.entries(settings)
          .filter(([key]) => key !== 'userId')
          .map(([key, value]) => (
          <Pressable
            key={key}
            onPress={() =>
              updateNotificationPreferences(user.id, {
                [key]: !value,
              } as Partial<NotificationPreferences>)
            }
          >
            <AppCard variant={value ? 'highlighted' : 'elevated'} padding="md">
              <View className="flex-row items-center justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                    {formatLabel(key)}
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                    {value ? 'Enabled for the prototype demo.' : 'Disabled in the current prototype state.'}
                  </HeroText>
                </View>
                <AppChip label={value ? 'On' : 'Off'} variant={value ? 'success' : 'neutral'} />
              </View>
            </AppCard>
          </Pressable>
        ))}
      </View>

      <AppButton label="Done" size="lg" className="mt-8" onPress={() => router.back()} />
    </AppScreen>
  );
}
