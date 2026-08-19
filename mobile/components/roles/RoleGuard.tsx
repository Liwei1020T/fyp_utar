import React from 'react';
import { Redirect, Stack } from 'expo-router';
import { View } from 'react-native';
import { appChromeColors } from '../ui/theme';
import { useAppStore, useCurrentUser } from '../../store/appStore';
import type { UserRole } from '../../types/domain';
import { getRoleHome } from '../../lib/navigation';

interface RoleGuardProps {
  role: UserRole;
}

export function RoleGuard({ role }: RoleGuardProps) {
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const user = useCurrentUser();

  if (!hasHydrated) {
    return <View style={{ flex: 1, backgroundColor: appChromeColors.page }} />;
  }

  if (!user) {
    return <Redirect href="/auth/login" />;
  }

  if (user.role !== role) {
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
