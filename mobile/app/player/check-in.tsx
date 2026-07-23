import React from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { useBookings, useCurrentUser } from '../../store/appStore';
import { formatBookingOrderCode } from '../../lib/formatters';

export default function PlayerCheckInScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ bookingId?: string }>();
  const user = useCurrentUser();
  const bookings = useBookings();

  if (!user || user.role !== 'player') {
    return null;
  }

  const eligibleBookings = bookings.filter(
    (item) =>
      item.playerId === user.id &&
      (item.status === 'awaiting_dropoff' || item.status === 'confirmed'),
  );
  const checkInBooking = params.bookingId
    ? eligibleBookings.find((item) => item.id === params.bookingId)
    : eligibleBookings[0];

  return (
    <AppScreen
      headerVariant="flow"
      title="Counter check-in"
      subtitle="Show the live check-in reference for your next racket drop-off."
      showBackButton
      onBackPress={() => router.back()}
    >
      {checkInBooking ? (
        <AppCard variant="dark" className="rounded-[32px]" padding="lg">
          <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
            Live check-in reference
          </HeroText>
          <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-white">
            {checkInBooking.checkInReference}
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-primary-100">
            Booking {checkInBooking.orderCode ?? formatBookingOrderCode(checkInBooking.id)} •{' '}
            {checkInBooking.dropOffDate} at {checkInBooking.dropOffTime}
          </HeroText>
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
            'Show the live check-in reference to the service desk.',
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
