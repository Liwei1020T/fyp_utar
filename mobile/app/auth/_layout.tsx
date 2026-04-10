import React from 'react';
import { Redirect, Stack } from 'expo-router';
import { View } from 'react-native';
import { appChromeColors } from '../../components/ui/theme';
import { useAppStore, useCurrentUser } from '../../store/appStore';
import { getRoleHome } from '../../lib/navigation';

export default function AuthLayout() {
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const user = useCurrentUser();

  if (!hasHydrated) {
    return <View style={{ flex: 1, backgroundColor: appChromeColors.page }} />;
  }

  if (user) {
    return <Redirect href={getRoleHome(user.role) as never} />;
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    />
  );
}
