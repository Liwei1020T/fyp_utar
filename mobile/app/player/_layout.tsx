import React from 'react';
import { useEffect } from 'react';
import { Redirect, useSegments } from 'expo-router';
import { RoleGuard } from '../../components/roles/RoleGuard';
import { useAppStore, useBackendAccessToken } from '../../store/appStore';
import { backendApi } from '../../services/backendApi';
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
  const token = useBackendAccessToken();
  const sessionSource = useAppStore((state) => state.sessionSource);
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);

  useEffect(() => {
    if (sessionSource !== 'backend' || !token) {
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
        console.warn('Failed to hydrate live player data', error);
      }
    };

    void hydrate();

    return () => {
      cancelled = true;
    };
  }, [
    sessionSource,
    setBackendPlayerSession,
    setLiveBookings,
    setLiveStrings,
    token,
  ]);

  if (segments.some((segment) => DEFERRED_PLAYER_SEGMENTS.has(segment))) {
    return <Redirect href="/player" />;
  }

  return <RoleGuard role="player" />;
}
