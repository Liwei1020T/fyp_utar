import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { useBookings, useCurrentUser } from '../../store/appStore';

export default function VendorCheckInScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const [reference, setReference] = useState('SS-BK-2401-VICT');
  const [submittedReference, setSubmittedReference] = useState('SS-BK-2401-VICT');

  if (!user || user.role !== 'vendor') {
    return null;
  }

  const match = bookings.find(
    (item) =>
      item.vendorId === user.id
      && (
        item.checkInReference.includes(submittedReference)
        || item.id.includes(submittedReference)
      )
  );
  const suggestedReference = bookings.find(
    (item) => item.vendorId === user.id && item.status === 'awaiting_dropoff'
  )?.checkInReference ?? bookings.find((item) => item.vendorId === user.id)?.checkInReference ?? reference;

  return (
    <AppScreen
      tone="vendor"
      title="Check-in"
      subtitle="Manual booking reference entry and fake QR scan flow for vendor use."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      <AppInput label="Booking reference" value={reference} onChangeText={setReference} />
      <View className="flex-row gap-3">
        <AppButton
          label="Fake scan QR"
          className="flex-1"
          onPress={() => {
            setReference(suggestedReference);
            setSubmittedReference(suggestedReference);
          }}
        />
        <AppButton
          label="Lookup"
          variant="outline"
          className="flex-1"
          onPress={() => setSubmittedReference(reference.trim())}
        />
      </View>
      {match ? (
        <AppCard variant="highlighted" className="mt-6" padding="lg">
          <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
            {match.id} matched
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            {match.racketBrand} {match.racketModel} scheduled for {match.dropOffDate} at {match.dropOffTime}
          </HeroText>
        </AppCard>
      ) : submittedReference ? (
        <AppCard variant="subtle" className="mt-6" padding="lg">
          <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
            No booking matched
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Try a booking ID or scan a mock QR reference to load the next drop-off.
          </HeroText>
        </AppCard>
      ) : null}
    </AppScreen>
  );
}
