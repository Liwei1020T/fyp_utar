import React, { useCallback, useEffect, useState } from 'react';
import { View } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import QRCode from 'react-native-qrcode-svg';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import {
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
} from '../../store/appStore';
import { formatBookingOrderCode } from '../../lib/formatters';
import { BackendApiError, backendApi } from '../../services/backendApi';
import type { BackendCheckInToken } from '../../types/backend';

export default function PlayerCheckInScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ bookingId?: string }>();
  const user = useCurrentUser();
  const bookings = useBookings();
  const token = useBackendAccessToken();
  const [checkInToken, setCheckInToken] =
    useState<BackendCheckInToken | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());

  const eligibleBookings =
    user?.role === 'player'
      ? bookings.filter(
          (item) =>
            item.playerId === user.id &&
            (item.status === 'awaiting_dropoff' ||
              item.status === 'confirmed'),
        )
      : [];
  const checkInBooking = params.bookingId
    ? eligibleBookings.find((item) => item.id === params.bookingId)
    : eligibleBookings[0];
  const refreshToken = useCallback(async () => {
    if (!token || !checkInBooking) {
      setCheckInToken(null);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setCheckInToken(
        await backendApi.createCheckInToken(token, checkInBooking.id),
      );
      setNow(Date.now());
    } catch (loadError) {
      setCheckInToken(null);
      setError(
        loadError instanceof BackendApiError
          ? loadError.message
          : 'Failed to generate a secure check-in QR.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [checkInBooking, token]);

  useFocusEffect(
    useCallback(() => {
      void refreshToken();
    }, [refreshToken]),
  );

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  if (!user || user.role !== 'player') {
    return null;
  }

  const secondsRemaining = checkInToken
    ? Math.max(
        0,
        Math.floor(
          (new Date(checkInToken.expires_at).getTime() - now) / 1000,
        ),
      )
    : 0;
  const isExpired = checkInToken !== null && secondsRemaining === 0;

  return (
    <AppScreen
      headerVariant="flow"
      title="Counter check-in"
      subtitle="Show the secure, short-lived QR for your next racket drop-off."
      showBackButton
      onBackPress={() => router.back()}
    >
      {checkInBooking ? (
        <AppCard variant="dark" className="rounded-[32px]" padding="lg">
          <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
            Secure booking QR
          </HeroText>
          {checkInToken && !isExpired ? (
            <View className="mt-5 items-center rounded-[24px] bg-white p-5">
              <QRCode value={checkInToken.token} size={220} />
            </View>
          ) : null}
          <HeroText className="mt-2 text-sm leading-6 text-primary-100">
            Booking {checkInBooking.orderCode ?? formatBookingOrderCode(checkInBooking.id)} •{' '}
            {checkInBooking.dropOffDate} at {checkInBooking.dropOffTime}
          </HeroText>
          <HeroText className="mt-2 text-sm font-semibold text-white">
            {isLoading
              ? 'Generating secure QR…'
              : checkInToken
                ? isExpired
                  ? 'Expired — refresh before scanning'
                  : `Expires in ${Math.floor(secondsRemaining / 60)}:${String(
                      secondsRemaining % 60,
                    ).padStart(2, '0')}`
                : error ?? 'Secure QR unavailable'}
          </HeroText>
          <AppButton
            label={isExpired ? 'Refresh expired QR' : 'Refresh QR'}
            variant="outline"
            className="mt-5"
            isLoading={isLoading}
            onPress={() => void refreshToken()}
          />
        </AppCard>
      ) : (
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            No booking is ready for check-in.
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            A live reference appears here after a booking reaches the awaiting drop-off stage.
          </HeroText>
        </AppCard>
      )}

      <AppSection eyebrow="Instructions" title="What happens on arrival">
        <View className="gap-3">
          {[
            'Show the QR to the service desk; it expires after 10 minutes.',
            'Admin confirms racket model, string choice, and requested tension.',
            'Service status moves from awaiting drop-off to in progress once the admin accepts the racket.',
          ].map((item) => (
            <AppCard key={item} variant="subtle" padding="sm">
              <HeroText className="text-sm leading-6 text-neutral-600">{item}</HeroText>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppButton label="Back to bookings" size="lg" className="mt-8" onPress={() => router.push('/player/bookings')} />
    </AppScreen>
  );
}
