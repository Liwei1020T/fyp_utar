import React, { useCallback, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import {
  useBackendAccessToken,
  useCurrentUser,
} from '../../../store/appStore';
import type { NotificationPreferences } from '../../../types/domain';
import { formatLabel } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';

export default function NotificationPreferencesScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const [liveSettings, setLiveSettings] = useState<NotificationPreferences | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [savingKey, setSavingKey] = useState<string | null>(null);

  const loadPreferences = useCallback(async () => {
    if (!user || user.role !== 'player' || !token) {
      setError(null);
      return;
    }

    setLiveSettings(null);
    setError(null);
    try {
      const response = await backendApi.fetchNotificationPreferences(token);
      setLiveSettings({ userId: user.id, ...response });
    } catch (loadError) {
      setError(
        loadError instanceof BackendApiError
          ? loadError.message
          : 'Failed to load notification preferences.',
      );
    }
  }, [token, user]);

  useFocusEffect(
    useCallback(() => {
      void loadPreferences();
    }, [loadPreferences]),
  );

  if (!user || user.role !== 'player') {
    return null;
  }

  const settings = liveSettings;

  const togglePreference = async (
    key: Exclude<keyof NotificationPreferences, 'userId'>,
  ) => {
    if (!settings) {
      return;
    }

    const next = { ...settings, [key]: !settings[key] };
    if (!token) {
      setError('Your player session expired. Sign in again to save preferences.');
      return;
    }

    setLiveSettings(next);
    setSavingKey(key);
    setError(null);
    try {
      const { userId: _, ...payload } = next;
      const saved = await backendApi.updateNotificationPreferences(token, payload);
      setLiveSettings({ userId: user.id, ...saved });
    } catch (saveError) {
      setLiveSettings(settings);
      setError(
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to save notification preferences.',
      );
    } finally {
      setSavingKey(null);
    }
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Notification preferences"
      subtitle="Choose which in-app and WhatsApp updates you want to receive."
      showBackButton
      onBackPress={() => router.back()}
    >
      <View className="gap-3">
        {settings ? (
          Object.entries(settings)
            .filter(([key]) => key !== 'userId')
            .map(([key, value]) => (
              <Pressable
                key={key}
                accessibilityRole="switch"
                accessibilityLabel={`${formatLabel(key)} notifications`}
                accessibilityState={{
                  checked: Boolean(value),
                  disabled: savingKey !== null,
                }}
                disabled={savingKey !== null}
                onPress={() =>
                  void togglePreference(
                    key as Exclude<keyof NotificationPreferences, 'userId'>,
                  )
                }
              >
                <AppCard
                  variant={value ? 'highlighted' : 'elevated'}
                  padding="md"
                >
                  <View className="flex-row items-center justify-between gap-4">
                    <View className="flex-1">
                      <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                        {formatLabel(key)}
                      </HeroText>
                      <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                        {value ? 'Enabled for live updates.' : 'Disabled.'}
                      </HeroText>
                    </View>
                    <AppChip
                      label={value ? 'On' : 'Off'}
                      variant={value ? 'success' : 'neutral'}
                    />
                  </View>
                </AppCard>
              </Pressable>
            ))
        ) : (
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-600">
              {error ??
                (token
                  ? 'Loading notification preferences...'
                  : 'Your player session expired. Sign in again to load preferences.')}
            </HeroText>
            {error ? (
              <AppButton
                label="Retry"
                variant="outline"
                className="mt-4"
                onPress={() => void loadPreferences()}
              />
            ) : null}
          </AppCard>
        )}
      </View>

      {settings && error ? (
        <HeroText className="mt-6 text-sm font-medium text-red-600">
          {error}
        </HeroText>
      ) : null}
      <AppButton
        label="Done"
        size="lg"
        className="mt-8"
        onPress={() => router.back()}
      />
    </AppScreen>
  );
}
