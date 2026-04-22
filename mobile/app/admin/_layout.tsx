import React, { useEffect } from 'react';
import { Redirect, useSegments } from 'expo-router';
import { View } from 'react-native';
import { RoleGuard } from '../../components/roles/RoleGuard';
import { useAppStore, useBackendAccessToken, useCurrentUser } from '../../store/appStore';
import { appChromeColors } from '../../components/ui/theme';
import {
  backendApi,
  isBackendAuthError,
} from '../../services/backendApi';
import {
  mapBackendBookingToBooking,
  mapBackendInventoryStringToStringItem,
  mapBackendUserToAdminProfile,
} from '../../services/backendMappers';

const DEFERRED_ADMIN_SEGMENTS = new Set([
  'analytics',
  'chat',
  'payments',
  'service-queue',
]);

export default function AdminLayout() {
  const segments = useSegments();
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const token = useBackendAccessToken();
  const user = useCurrentUser();
  const sessionSource = useAppStore((state) => state.sessionSource);
  const logout = useAppStore((state) => state.logout);
  const setBackendAdminSession = useAppStore(
    (state) => state.setBackendAdminSession,
  );
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);

  useEffect(() => {
    if (!hasHydrated || sessionSource !== 'backend' || !token || user?.role !== 'admin') {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      try {
        const [currentUserResult, inventoryResult, bookingsResult] = await Promise.allSettled([
          backendApi.fetchCurrentUser(token),
          backendApi.adminListInventoryStrings(token),
          backendApi.adminListBookings(token),
        ]);

        if (cancelled) {
          return;
        }

        if (currentUserResult.status === 'rejected') {
          if (isBackendAuthError(currentUserResult.reason)) {
            logout();
            return;
          }
          console.warn('Failed to hydrate live admin profile', currentUserResult.reason);
          return;
        }

        const admin = mapBackendUserToAdminProfile(currentUserResult.value);
        setBackendAdminSession({
          accessToken: token,
          admin,
        });

        let liveStrings = useAppStore.getState().liveStrings;
        if (inventoryResult.status === 'fulfilled') {
          liveStrings = inventoryResult.value.items.map(mapBackendInventoryStringToStringItem);
          setLiveStrings(liveStrings);
        } else {
          console.warn('Failed to hydrate live admin inventory', inventoryResult.reason);
        }

        if (bookingsResult.status === 'fulfilled') {
          const priceByStringId = new Map(
            liveStrings.map((item) => [item.id, item.price]),
          );
          const liveBookings = bookingsResult.value.items.map((item) =>
            mapBackendBookingToBooking(item, priceByStringId, admin.id),
          );
          setLiveBookings(liveBookings);
        } else {
          if (isBackendAuthError(bookingsResult.reason)) {
            logout();
            return;
          }
          console.warn('Failed to hydrate live admin bookings', bookingsResult.reason);
        }
      } catch (error) {
        if (isBackendAuthError(error)) {
          logout();
          return;
        }
        console.warn('Failed to hydrate live admin data', error);
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
    setBackendAdminSession,
    setLiveBookings,
    setLiveStrings,
    token,
    user?.role,
  ]);

  if (!hasHydrated) {
    return <View style={{ flex: 1, backgroundColor: appChromeColors.page }} />;
  }

  if (segments.some((segment) => DEFERRED_ADMIN_SEGMENTS.has(segment))) {
    return <Redirect href="/admin" />;
  }

  return <RoleGuard role="admin" />;
}
