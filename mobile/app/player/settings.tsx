import Constants from 'expo-constants';
import { useFocusEffect, useRouter } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { Alert, Platform, Pressable, View } from 'react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { BackendApiError, backendApi } from '../../services/backendApi';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
} from '../../store/appStore';
import type { BackendPrivacySettings } from '../../types/backend';

const PRIVACY_LABELS: Record<keyof BackendPrivacySettings, string> = {
  analytics_consent: 'Anonymous usage analytics',
  personalization_consent: 'Profile personalization',
  marketing_consent: 'Marketing messages',
};

export default function PlayerSettingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const logout = useAppStore((state) => state.logout);
  const [privacy, setPrivacy] = useState<BackendPrivacySettings | null>(null);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [deletionReason, setDeletionReason] = useState('');
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      if (!token) return;
      void backendApi
        .fetchPrivacySettings(token)
        .then(setPrivacy)
        .catch((error: unknown) =>
          setMessage(
            error instanceof BackendApiError
              ? error.message
              : 'Failed to load privacy settings.',
          ),
        );
    }, [token]),
  );

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

  const togglePrivacy = async (key: keyof BackendPrivacySettings) => {
    if (!token || !privacy) return;
    const previous = privacy;
    const next = { ...privacy, [key]: !privacy[key] };
    setPrivacy(next);
    setMessage(null);
    try {
      setPrivacy(await backendApi.updatePrivacySettings(token, next));
    } catch (error) {
      setPrivacy(previous);
      setMessage(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to save privacy settings.',
      );
    }
  };

  const submitDeletionRequest = () => {
    if (!token) return;
    const submit = () => {
      setBusyAction('delete');
      setMessage(null);
      void backendApi
        .requestAccountDeletion(token, deletionReason)
        .then(() => setMessage('Account deletion request submitted for review.'))
        .catch((error: unknown) =>
          setMessage(
            error instanceof BackendApiError
              ? error.message
              : 'Failed to submit deletion request.',
          ),
        )
        .finally(() => setBusyAction(null));
    };
    if (Platform.OS === 'web') {
      if (
        globalThis.confirm?.(
          'Request account deletion?\n\nThe admin will review this request. Your account is not deleted immediately.',
        )
      ) {
        submit();
      }
      return;
    }
    Alert.alert(
      'Request account deletion?',
      'The admin will review this request. Your account is not deleted immediately.',
      [
        { text: 'Keep account', style: 'cancel' },
        {
          text: 'Submit request',
          style: 'destructive',
          onPress: submit,
        },
      ],
    );
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Settings"
      subtitle="Manage your account, privacy, notifications, and app session."
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

      <AppSection eyebrow="Notifications" title="Delivery preferences">
        <AppButton
          label="Open notification preferences"
          variant="outline"
          onPress={() => router.push('/player/notifications/preferences')}
        />
      </AppSection>

      <AppSection eyebrow="Privacy" title="Data choices">
        <View className="gap-3">
          {privacy
            ? Object.entries(privacy).map(([rawKey, enabled]) => {
                const key = rawKey as keyof BackendPrivacySettings;
                return (
                  <Pressable
                    key={key}
                    accessibilityRole="switch"
                    accessibilityLabel={PRIVACY_LABELS[key]}
                    accessibilityState={{ checked: enabled }}
                    onPress={() => void togglePrivacy(key)}
                  >
                    <AppCard
                      variant={enabled ? 'highlighted' : 'elevated'}
                      padding="md"
                    >
                      <View className="flex-row items-center justify-between gap-3">
                        <HeroText className="flex-1 text-sm font-semibold text-neutral-900">
                          {PRIVACY_LABELS[key]}
                        </HeroText>
                        <AppChip
                          label={enabled ? 'On' : 'Off'}
                          variant={enabled ? 'success' : 'neutral'}
                        />
                      </View>
                    </AppCard>
                  </Pressable>
                );
              })
            : null}
        </View>
      </AppSection>

      <AppSection eyebrow="Account removal" title="Delete account request">
        <AppInput
          label="Reason (optional)"
          value={deletionReason}
          onChangeText={setDeletionReason}
          multiline
          inputClassName="min-h-20"
        />
        <AppButton
          label="Request account deletion"
          variant="outline"
          isLoading={busyAction === 'delete'}
          onPress={submitDeletionRequest}
        />
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
