import React from 'react';
import { useEffect } from 'react';
import { Redirect, useSegments } from 'expo-router';
import { View } from 'react-native';
import { RoleGuard } from '../../components/roles/RoleGuard';
import { appChromeColors } from '../../components/ui/theme';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
} from '../../store/appStore';
import {
  backendApi,
  isBackendAuthError,
} from '../../services/backendApi';
import {
  mapBackendBookingToBooking,
  mapBackendStringToStringItem,
  mapBackendUserToPlayerProfile,
} from '../../services/backendMappers';

const DEFERRED_PLAYER_SEGMENTS = new Set([
  'chat',
  'chatbot',
  'check-in',
  'feedback',
  'notifications',
  'payments',
  'rackets',
  'wallet',
]);

export default function PlayerLayout() {
  const segments = useSegments();
  const user = useCurrentUser();
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const token = useBackendAccessToken();
  const sessionSource = useAppStore((state) => state.sessionSource);
  const logout = useAppStore((state) => state.logout);
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);

  useEffect(() => {
    if (!hasHydrated || sessionSource !== 'backend' || !token || user?.role !== 'player') {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      try {
        const [user, profile, stringsPage, bookingsPage] = await Promise.all([
          backendApi.fetchCurrentUser(token),
          backendApi.fetchProfile(token).catch(() => null),
          backendApi.listStrings(token),
          backendApi.listBookings(token),
        ]);

        if (cancelled) {
          return;
        }

        const liveStrings = stringsPage.items.map(mapBackendStringToStringItem);
        const priceByStringId = new Map(
          liveStrings.map((item) => [item.id, item.price]),
        );
        const liveBookings = bookingsPage.items.map((item) =>
          mapBackendBookingToBooking(item, priceByStringId),
        );

        setBackendPlayerSession({
          accessToken: token,
          player: mapBackendUserToPlayerProfile(user, profile),
        });
        setLiveStrings(liveStrings);
        setLiveBookings(liveBookings);
      } catch (error) {
        if (isBackendAuthError(error)) {
          logout();
          return;
        }
        console.warn('Failed to hydrate live player data', error);
      }
    };

    void hydrate();

    return () => {
      cancelled = true;
    };
  }, [
    hasHydrated,
    logout,
    sessionSource,
    setBackendPlayerSession,
    setLiveBookings,
    setLiveStrings,
    token,
    user?.role,
  ]);

  if (!hasHydrated) {
    return <View style={{ flex: 1, backgroundColor: appChromeColors.page }} />;
  }

  if (segments.some((segment) => DEFERRED_PLAYER_SEGMENTS.has(segment))) {
    return <Redirect href="/player" />;
  }

  return <RoleGuard role="player" />;
}
