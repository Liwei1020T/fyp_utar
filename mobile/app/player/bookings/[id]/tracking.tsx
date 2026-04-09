import React from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppCard } from '../../../../components/ui/AppCard';
import { AppIconButton } from '../../../../components/ui/AppIconButton';
import { HeroText } from '../../../../components/ui/heroui';
import { AppScreen } from '../../../../components/shared/AppScreen';
import { AppSection } from '../../../../components/shared/AppSection';
import { TrackingTimeline } from '../../../../components/tracking/TrackingTimeline';
import { formatBookingOrderCode } from '../../../../lib/formatters';
import { useBookings } from '../../../../store/appStore';

export default function BookingTrackingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const bookings = useBookings();
  const booking = bookings.find((item) => item.id === params.id);

  if (!booking) {
    return (
      <AppScreen title="Tracking unavailable">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            This booking is no longer available.
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);

  return (
    <AppScreen
      headerVariant="secondary"
      title="Service tracking"
      subtitle="Follow the drop-off journey from booking confirmation to collection."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection eyebrow="Timeline" title={`Booking ${orderCode}`}>
        <TrackingTimeline timeline={booking.timeline} currentStatus={booking.status} />
      </AppSection>
    </AppScreen>
  );
}
