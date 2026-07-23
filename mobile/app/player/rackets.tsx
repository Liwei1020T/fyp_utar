import React from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppCard } from '../../components/ui/AppCard';
import { HeroText } from '../../components/ui/heroui';
import { RacketPassportCard } from '../../components/rackets/RacketPassportCard';
import { useCurrentUser, useRackets, useStrings } from '../../store/appStore';
import { getStringById } from '../../services/mockAppService';

export default function RacketPassportListScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const rackets = useRackets();
  const strings = useStrings();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerRackets = rackets.filter((item) => item.playerId === user.id);

  return (
    <AppScreen
      headerVariant="primary"
      title="Racket passport"
      subtitle="Saved frames, string history, preferred tensions, and service notes."
    >
      <AppSection eyebrow="Saved rackets" title="Your current lineup">
        <View className="gap-4">
          {playerRackets.length === 0 ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-600">
                Your saved rackets will appear here after your first completed booking.
              </HeroText>
            </AppCard>
          ) : null}
          {playerRackets.map((racket) => {
            const currentString =
              strings.find((item) => item.id === racket.currentStringId) ??
              getStringById(racket.currentStringId);
            return (
              <RacketPassportCard
                key={racket.id}
                racket={racket}
                currentStringLabel={currentString ? `${currentString.brand} ${currentString.model}` : 'Unknown string'}
                onPress={() => router.push(`/player/rackets/${racket.id}`)}
              />
            );
          })}
        </View>
      </AppSection>
    </AppScreen>
  );
}
