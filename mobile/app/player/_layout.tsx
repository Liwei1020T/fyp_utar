import React, { useEffect } from 'react';
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
  mapBackendConversationToConversation,
  mapBackendNotificationToNotification,
  mapBackendPaymentToPayment,
  mapBackendRacketToRacketPassport,
  mapBackendStringToStringItem,
  mapBackendUserToPlayerProfile,
  mapBackendWallet,
} from '../../services/backendMappers';

export default function PlayerLayout() {
  const user = useCurrentUser();
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const token = useBackendAccessToken();
  const logout = useAppStore((state) => state.logout);
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);
  const setLiveConversations = useAppStore((state) => state.setLiveConversations);
  const setLiveNotifications = useAppStore((state) => state.setLiveNotifications);
  const setLivePayments = useAppStore((state) => state.setLivePayments);
  const setLiveRackets = useAppStore((state) => state.setLiveRackets);
  const setLiveWallet = useAppStore((state) => state.setLiveWallet);
  const updateStoreSettings = useAppStore((state) => state.updateStoreSettings);

  useEffect(() => {
    if (!hasHydrated || !token || user?.role !== 'player') {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      try {
        const [
          userResult,
          profileResult,
          stringsResult,
          bookingsResult,
          storeSettingsResult,
          paymentsResult,
          walletResult,
          notificationsResult,
          conversationsResult,
          racketsResult,
        ] = await Promise.allSettled([
          backendApi.fetchCurrentUser(token),
          backendApi.fetchProfile(token),
          backendApi.listStrings(token),
          backendApi.listBookings(token),
          backendApi.fetchStoreSettings(token),
          backendApi.listPayments(token),
          backendApi.fetchWallet(token),
          backendApi.listNotifications(token),
          backendApi.listPlayerConversations(token),
          backendApi.listRackets(token),
        ]);

        if (
          cancelled ||
          useAppStore.getState().backendAccessToken !== token
        ) {
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

        if (profileResult.status === 'rejected') {
          console.warn('Failed to hydrate live player profile details', profileResult.reason);
        } else {
          setBackendPlayerSession({
            accessToken: token,
            player: mapBackendUserToPlayerProfile(
              userResult.value,
              profileResult.value,
            ),
          });
        }

        if (stringsResult.status === 'fulfilled') {
          setLiveStrings(
            stringsResult.value.items.map(mapBackendStringToStringItem),
          );
        } else {
          console.warn('Failed to hydrate live player strings', stringsResult.reason);
        }

        let liveBookings = useAppStore.getState().liveBookings;
        if (bookingsResult.status === 'fulfilled') {
          liveBookings = bookingsResult.value.items.map((item) =>
            mapBackendBookingToBooking(item),
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
          updateStoreSettings({
            storeName: storeSettings.store_name,
            storeContact: storeSettings.store_contact,
            address: storeSettings.address,
            supportText: storeSettings.support_text,
            paymentNotes: storeSettings.payment_notes,
            bookingNotes: storeSettings.booking_notes,
            storePolicyText: storeSettings.store_policy_text,
            trendingStringIds: storeSettings.trending_string_ids ?? [],
            defaultServicePrice: storeSettings.default_service_price,
            notificationSettings: storeSettings.notification_settings,
          });
        } else if (storeSettingsResult.status === 'rejected') {
          console.warn('Failed to hydrate live store settings', storeSettingsResult.reason);
        }

        if (paymentsResult.status === 'fulfilled') {
          setLivePayments(paymentsResult.value.map(mapBackendPaymentToPayment));
        } else {
          console.warn('Failed to hydrate live payments', paymentsResult.reason);
        }

        if (walletResult.status === 'fulfilled') {
          const wallet = mapBackendWallet(walletResult.value);
          setLiveWallet(wallet.balance, wallet.transactions);
        } else {
          console.warn('Failed to hydrate live wallet', walletResult.reason);
        }

        if (notificationsResult.status === 'fulfilled') {
          setLiveNotifications(
            notificationsResult.value.map(mapBackendNotificationToNotification),
          );
        } else {
          console.warn(
            'Failed to hydrate live notifications',
            notificationsResult.reason,
          );
        }

        if (conversationsResult.status === 'fulfilled') {
          setLiveConversations(
            conversationsResult.value.map((item) =>
              mapBackendConversationToConversation(
                item,
                liveBookings.find((booking) => booking.id === item.booking_id),
              ),
            ),
          );
        } else {
          console.warn(
            'Failed to hydrate live conversations',
            conversationsResult.reason,
          );
        }

        if (racketsResult.status === 'fulfilled') {
          setLiveRackets(
            racketsResult.value.map(mapBackendRacketToRacketPassport),
          );
        } else {
          console.warn('Failed to hydrate live rackets', racketsResult.reason);
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
    setBackendPlayerSession,
    setLiveBookings,
    setLiveConversations,
    setLiveNotifications,
    setLivePayments,
    setLiveRackets,
    setLiveStrings,
    setLiveWallet,
    token,
    updateStoreSettings,
    user?.role,
  ]);

  if (!hasHydrated) {
    return <View style={{ flex: 1, backgroundColor: appChromeColors.page }} />;
  }

  return <RoleGuard role="player" />;
}
