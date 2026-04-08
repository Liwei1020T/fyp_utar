import React, { useEffect } from 'react';
import { Redirect, useSegments } from 'expo-router';
import { RoleGuard } from '../../components/roles/RoleGuard';
import { useAppStore, useBackendAccessToken, useCurrentUser } from '../../store/appStore';
import { backendApi } from '../../services/backendApi';
import {
  mapBackendBookingToBooking,
  mapBackendInventoryStringToStringItem,
  mapBackendUserToAdminProfile,
} from '../../services/backendMappers';

const DEFERRED_ADMIN_SEGMENTS = new Set([
  'analytics',
  'chat',
  'check-in',
  'payments',
  'service-queue',
]);

export default function AdminLayout() {
  const segments = useSegments();
  const token = useBackendAccessToken();
  const user = useCurrentUser();
  const sessionSource = useAppStore((state) => state.sessionSource);
  const setBackendAdminSession = useAppStore(
    (state) => state.setBackendAdminSession,
  );
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);

  useEffect(() => {
    if (sessionSource !== 'backend' || !token || user?.role !== 'admin') {
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
        console.warn('Failed to hydrate live admin data', error);
      }
    };

    void hydrate();

    return () => {
      cancelled = true;
    };
  }, [
    sessionSource,
    setBackendAdminSession,
    setLiveBookings,
    setLiveStrings,
    token,
    user?.role,
  ]);

  if (segments.some((segment) => DEFERRED_ADMIN_SEGMENTS.has(segment))) {
    return <Redirect href="/admin" />;
  }

  return <RoleGuard role="admin" />;
}
