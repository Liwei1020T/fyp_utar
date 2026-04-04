import React from 'react';
import { Redirect, Stack } from 'expo-router';
import { useCurrentUser } from '../../store/appStore';
import type { UserRole } from '../../types/domain';
import { getRoleHome } from '../../lib/navigation';

interface RoleGuardProps {
  role: UserRole;
}

export function RoleGuard({ role }: RoleGuardProps) {
  const user = useCurrentUser();

  if (!user) {
    return <Redirect href="/auth/welcome" />;
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
