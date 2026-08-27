import Constants from 'expo-constants';
import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { View } from 'react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { BackendApiError, backendApi } from '../../services/backendApi';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
} from '../../store/appStore';
export default function PlayerSettingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const logout = useAppStore((state) => state.logout);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  if (!user || user.role !== 'player') {
    return null;
  }

  const changePassword = async () => {
    if (!token || !currentPassword || !newPassword) return;
    setBusyAction('password');
    setMessage(null);
    try {
      await backendApi.changePassword(token, {
        current_password: currentPassword,
        new_password: newPassword,
      });
      logout();
      router.replace('/auth/login');
    } catch (error) {
      setMessage(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to update password.',
      );
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Settings"
      subtitle="Keep your password current and manage your session."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection eyebrow="Account" title="Account information">
        <AppCard variant="elevated" padding="md">
          <HeroText className="text-base font-bold text-neutral-950">
            {user.name}
          </HeroText>
          <HeroText className="mt-1 text-sm text-neutral-600">
            {user.phone || user.email}
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Security" title="Update password">
        <View className="gap-3">
          <AppInput
            label="Current password"
            value={currentPassword}
            onChangeText={setCurrentPassword}
            secureTextEntry
          />
          <AppInput
            label="New password"
            value={newPassword}
            onChangeText={setNewPassword}
            secureTextEntry
          />
          <AppButton
            label="Update password"
            isLoading={busyAction === 'password'}
            isDisabled={!currentPassword || newPassword.length < 8}
            onPress={() => void changePassword()}
          />
        </View>
      </AppSection>

      {message ? (
        <AppCard variant="subtle" className="mt-6" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-700">
            {message}
          </HeroText>
        </AppCard>
      ) : null}

      <AppSection eyebrow="App" title="Application information">
        <AppCard variant="subtle" padding="md">
          <HeroText className="text-sm text-neutral-600">
            StringSense {Constants.expoConfig?.version ?? '1.0.0'}
          </HeroText>
        </AppCard>
      </AppSection>

      <AppButton
        label="Log out"
        variant="outline"
        className="mb-12 mt-8"
        onPress={() => {
          logout();
          router.replace('/auth/login');
        }}
      />
    </AppScreen>
  );
}
