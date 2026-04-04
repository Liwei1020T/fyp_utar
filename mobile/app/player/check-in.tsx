import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { useBookings, useCurrentUser } from '../../store/appStore';

export default function PlayerCheckInScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();

  if (!user || user.role !== 'player') {
    return null;
  }

  const latestBooking = bookings.find((item) => item.playerId === user.id);

  return (
    <AppScreen
      title="QR check-in"
      subtitle="Show your booking token and drop-off instructions at the counter."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
          Booking token
        </HeroText>
        <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-white">
          {latestBooking?.bookingToken ?? 'DROP-OFF-DEMO'}
        </HeroText>
        <HeroText className="mt-2 text-sm leading-6 text-primary-100">
          Counter staff can use this token or the booking reference during manual or QR-based check-in.
        </HeroText>
      </AppCard>

      <AppSection eyebrow="Visual token" title="Demo QR placeholder">
        <AppCard variant="elevated" padding="lg">
          <View className="flex-row flex-wrap justify-center gap-2">
            {Array.from({ length: 36 }).map((_, index) => (
              <View
                key={index}
                className={`h-6 w-6 rounded-sm ${index % 3 === 0 || index % 5 === 0 ? 'bg-neutral-950' : 'bg-neutral-100'}`}
              />
            ))}
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Instructions" title="What happens on arrival">
        <View className="gap-3">
          {[
            'Show the booking token or QR placeholder to the service desk.',
            'Vendor confirms racket model, string choice, and requested tension.',
            'Service status moves from awaiting drop-off to in progress once the vendor accepts the racket.',
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
