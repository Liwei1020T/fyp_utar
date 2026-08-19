import React, { useCallback, useState } from 'react';
import { View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { HeroText } from '../../components/ui/heroui';
import { RacketPassportCard } from '../../components/rackets/RacketPassportCard';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useRackets,
  useStrings,
} from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendRacketToRacketPassport } from '../../services/backendMappers';

export default function RacketPassportListScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const rackets = useRackets();
  const strings = useStrings();
  const setLiveRackets = useAppStore((state) => state.setLiveRackets);
  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [loadError, setLoadError] = useState<string | null>(null);

  const refreshRackets = useCallback(async () => {
    if (!token) {
      setIsLoading(false);
      setLoadError(null);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      const response = await backendApi.listRackets(token);
      setLiveRackets(response.map(mapBackendRacketToRacketPassport));
    } catch (error) {
      setLoadError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to load saved rackets.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [setLiveRackets, token]);

  useFocusEffect(
    useCallback(() => {
      void refreshRackets();
    }, [refreshRackets]),
  );

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerRackets = rackets.filter((item) => item.playerId === user.id);

  return (
    <AppScreen
      headerVariant="primary"
      title="Racket passport"
      subtitle="Saved frames, string history, preferred tensions, and service notes."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppButton
        label="Register a racket"
        size="lg"
        onPress={() => router.push('/player/rackets/new')}
      />

      {!token ? (
        <AppCard variant="subtle" className="mt-4" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Your player session expired. Sign in again to load or edit racket
            passports.
          </HeroText>
        </AppCard>
      ) : null}

      <AppSection eyebrow="Saved rackets" title="Your current lineup">
        <View className="gap-4">
          {isLoading && playerRackets.length === 0 ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-600">
                Loading your saved rackets...
              </HeroText>
            </AppCard>
          ) : null}
          {loadError ? (
            <AppCard
              variant="subtle"
              className="border border-red-100"
              padding="md"
            >
              <HeroText className="text-sm font-medium text-red-600">
                {loadError}
              </HeroText>
              <AppButton
                label="Retry"
                variant="outline"
                className="mt-4"
                isLoading={isLoading}
                onPress={() => void refreshRackets()}
              />
            </AppCard>
          ) : null}
          {!isLoading && !loadError && playerRackets.length === 0 ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-base font-semibold text-neutral-900">
                No racket passports yet
              </HeroText>
              <HeroText className="mt-1 text-sm leading-6 text-neutral-600">
                Register a frame now. Completed bookings linked to it will build
                its service history automatically.
              </HeroText>
            </AppCard>
          ) : null}
          {playerRackets.map((racket) => {
            const currentString = strings.find(
              (item) => item.id === racket.currentStringId,
            );
            return (
              <RacketPassportCard
                key={racket.id}
                racket={racket}
                currentStringLabel={
                  currentString
                    ? `${currentString.brand} ${currentString.model}`
                    : racket.stringHistory[0]?.stringName ??
                      'No completed services yet'
                }
                onPress={() => router.push(`/player/rackets/${racket.id}`)}
              />
            );
          })}
        </View>
      </AppSection>
    </AppScreen>
  );
}
