import React from 'react';
import { Redirect, Stack } from 'expo-router';
import { useCurrentUser } from '../../store/appStore';
import { getRoleHome } from '../../lib/navigation';

export default function AuthLayout() {
  const user = useCurrentUser();

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
