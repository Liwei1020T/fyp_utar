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
        const [currentUser, inventoryPage, bookingsPage] = await Promise.all([
          backendApi.fetchCurrentUser(token),
          backendApi.adminListInventoryStrings(token),
          backendApi.adminListBookings(token),
        ]);

        if (cancelled) {
          return;
        }

        const admin = mapBackendUserToAdminProfile(currentUser);
        const liveStrings = inventoryPage.items.map(mapBackendInventoryStringToStringItem);
        const priceByStringId = new Map(
          liveStrings.map((item) => [item.id, item.price]),
        );
        const liveBookings = bookingsPage.items.map((item) =>
          mapBackendBookingToBooking(item, priceByStringId, admin.id),
        );

        setBackendAdminSession({
          accessToken: token,
          admin,
        });
        setLiveStrings(liveStrings);
        setLiveBookings(liveBookings);
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
