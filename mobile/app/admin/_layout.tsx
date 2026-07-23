import React, { useEffect } from 'react';
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
  mapBackendConversationToConversation,
  mapBackendInventoryStringToStringItem,
  mapBackendPaymentToPayment,
  mapBackendUserToAdminProfile,
} from '../../services/backendMappers';

export default function AdminLayout() {
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const token = useBackendAccessToken();
  const user = useCurrentUser();
  const logout = useAppStore((state) => state.logout);
  const setBackendAdminSession = useAppStore(
    (state) => state.setBackendAdminSession,
  );
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);
  const setLiveConversations = useAppStore((state) => state.setLiveConversations);
  const setLivePayments = useAppStore((state) => state.setLivePayments);
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);

  useEffect(() => {
    if (!hasHydrated || !token || user?.role !== 'admin') {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      try {
        const [
          currentUserResult,
          inventoryResult,
          bookingsResult,
          paymentsResult,
          conversationsResult,
        ] = await Promise.allSettled([
          backendApi.fetchCurrentUser(token),
          backendApi.adminListInventoryStrings(token),
          backendApi.adminListBookings(token),
          backendApi.adminListPayments(token),
          backendApi.adminListConversations(token),
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

        let liveBookings = useAppStore.getState().liveBookings;
        if (bookingsResult.status === 'fulfilled') {
          const priceByStringId = new Map(
            liveStrings.map((item) => [item.id, item.price]),
          );
          liveBookings = bookingsResult.value.items.map((item) =>
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

        if (paymentsResult.status === 'fulfilled') {
          setLivePayments(paymentsResult.value.map(mapBackendPaymentToPayment));
        } else {
          console.warn('Failed to hydrate live payments', paymentsResult.reason);
        }

        if (conversationsResult.status === 'fulfilled') {
          setLiveConversations(
            conversationsResult.value.map((item) =>
              mapBackendConversationToConversation(
                item,
                liveBookings.find((booking) => booking.id === item.booking_id),
                admin.id,
              ),
            ),
          );
        } else {
          console.warn(
            'Failed to hydrate live conversations',
            conversationsResult.reason,
          );
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
    setBackendAdminSession,
    setLiveBookings,
    setLiveConversations,
    setLivePayments,
    setLiveStrings,
    token,
    user?.role,
  ]);

  if (!hasHydrated) {
    return <View style={{ flex: 1, backgroundColor: appChromeColors.page }} />;
  }

  return <RoleGuard role="admin" />;
}
