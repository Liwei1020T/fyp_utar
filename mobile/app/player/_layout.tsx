import React, { useEffect } from 'react';
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
  const updateAdminSettings = useAppStore((state) => state.updateAdminSettings);

  useEffect(() => {
    if (!hasHydrated || sessionSource !== 'backend' || !token || user?.role !== 'player') {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      try {
        const [userResult, profileResult, stringsResult, bookingsResult, storeSettingsResult] = await Promise.allSettled([
          backendApi.fetchCurrentUser(token),
          backendApi.fetchProfile(token),
          backendApi.listStrings(token),
          backendApi.listBookings(token),
          backendApi.fetchStoreSettings(token),
        ]);

        if (cancelled) {
          return;
        }

        if (userResult.status === 'rejected') {
          if (isBackendAuthError(userResult.reason)) {
            logout();
            return;
          }
          console.warn('Failed to hydrate live player identity', userResult.reason);
          return;
        }

        const profile =
          profileResult.status === 'fulfilled' ? profileResult.value : null;
        if (profileResult.status === 'rejected') {
          console.warn('Failed to hydrate live player profile details', profileResult.reason);
        }

        setBackendPlayerSession({
          accessToken: token,
          player: mapBackendUserToPlayerProfile(userResult.value, profile),
        });

        let liveStrings = useAppStore.getState().liveStrings;
        if (stringsResult.status === 'fulfilled') {
          liveStrings = stringsResult.value.items.map(mapBackendStringToStringItem);
          setLiveStrings(liveStrings);
        } else {
          console.warn('Failed to hydrate live player strings', stringsResult.reason);
        }

        if (bookingsResult.status === 'fulfilled') {
          const priceByStringId = new Map(
            liveStrings.map((item) => [item.id, item.price]),
          );
          const liveBookings = bookingsResult.value.items.map((item) =>
            mapBackendBookingToBooking(item, priceByStringId),
          );
          setLiveBookings(liveBookings);
        } else {
          if (isBackendAuthError(bookingsResult.reason)) {
            logout();
            return;
          }
          console.warn('Failed to hydrate live player bookings', bookingsResult.reason);
        }

        if (storeSettingsResult.status === 'fulfilled' && storeSettingsResult.value) {
          const storeSettings = storeSettingsResult.value;
          updateAdminSettings('main', {
            storeName: storeSettings.store_name,
            storeContact: storeSettings.store_contact,
            address: storeSettings.address,
            supportText: storeSettings.support_text,
            paymentNotes: storeSettings.payment_notes,
            bookingNotes: storeSettings.booking_notes,
            storePolicyText: storeSettings.store_policy_text,
            trendingStringIds: storeSettings.trending_string_ids ?? [],
          });
        } else if (storeSettingsResult.status === 'rejected') {
          console.warn('Failed to hydrate live store settings', storeSettingsResult.reason);
        }
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
    updateAdminSettings,
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
