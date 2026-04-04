import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppCard } from '../../components/ui/AppCard';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { HeroText } from '../../components/ui/heroui';
import { RacketPassportCard } from '../../components/rackets/RacketPassportCard';
import { useCurrentUser } from '../../store/appStore';
import { getRacketsForPlayer, getStringById } from '../../services/mockAppService';

export default function RacketPassportListScreen() {
  const router = useRouter();
  const user = useCurrentUser();

  if (!user || user.role !== 'player') {
    return null;
  }

  const rackets = getRacketsForPlayer(user.id);

  return (
    <AppScreen
      title="Racket passport"
      subtitle="Saved frames, string history, preferred tensions, and service notes."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      <AppSection eyebrow="Saved rackets" title="Your current lineup">
        <View className="gap-4">
          {rackets.map((racket) => {
            const currentString = getStringById(racket.currentStringId);
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
