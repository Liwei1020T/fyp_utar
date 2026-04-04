import React from 'react';
import { useEffect } from 'react';
import { RoleGuard } from '../../components/roles/RoleGuard';
import { useAppStore, useBackendAccessToken } from '../../store/appStore';
import { backendApi } from '../../services/backendApi';
import {
  mapBackendBookingToBooking,
  mapBackendStringToStringItem,
  mapBackendUserToPlayerProfile,
} from '../../services/backendMappers';

export default function PlayerLayout() {
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

  return <RoleGuard role="player" />;
}
