import React from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { useCurrentUser } from '../../../store/appStore';
import { getRacketsForPlayer, getStringById } from '../../../services/mockAppService';

export default function RacketPassportDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const user = useCurrentUser();

  if (!user || user.role !== 'player') {
    return null;
  }

  const racket = getRacketsForPlayer(user.id).find((item) => item.id === params.id);

  if (!racket) {
    return null;
  }

  return (
    <AppScreen
      headerVariant="secondary"
      title={racket.nickname}
      subtitle="Racket profile, string history, tensions used, and simple trend stats."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="dark" padding="lg">
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
          {racket.brand}
        </HeroText>
        <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-white">
          {racket.model}
        </HeroText>
        <View className="mt-4 flex-row flex-wrap gap-2">
          <AppChip label={racket.weightClass} variant="secondary" />
          <AppChip label={racket.balancePoint} variant="info" />
          <AppChip label={racket.gripSize} variant="neutral" />
        </View>
      </AppCard>

      <AppSection eyebrow="Current setup" title="Live stringing profile">
        <AppCard variant="elevated" padding="md">
          <HeroText className="text-base font-semibold text-neutral-900">
            {getStringById(racket.currentStringId)?.brand} {getStringById(racket.currentStringId)?.model}
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Current tension: {racket.currentTension} lbs • Preferred use: {racket.preferredUse}
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="History" title="String history and service notes">
        <View className="gap-3">
          {racket.stringHistory.map((entry) => (
            <AppCard key={entry.bookingId} variant="elevated" padding="sm">
              <HeroText className="text-sm font-semibold text-neutral-900">
                {getStringById(entry.stringId)?.brand} {getStringById(entry.stringId)?.model}
              </HeroText>
              <HeroText className="mt-1 text-sm text-neutral-500">
                {entry.tension} lbs • Installed {entry.installedAt}
              </HeroText>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Trends" title="Quick stats">
        <View className="flex-row gap-3">
          <AppCard variant="highlighted" className="flex-1" padding="md">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
              Services
            </HeroText>
            <HeroText className="mt-2 text-2xl font-bold tracking-tight text-neutral-950">
              {racket.serviceCount}
            </HeroText>
          </AppCard>
          <AppCard variant="highlighted" className="flex-1" padding="md">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
              Avg tension
            </HeroText>
            <HeroText className="mt-2 text-2xl font-bold tracking-tight text-neutral-950">
              {Math.round(racket.stringHistory.reduce((sum, item) => sum + item.tension, 0) / racket.stringHistory.length)} lbs
            </HeroText>
          </AppCard>
        </View>
      </AppSection>
    </AppScreen>
  );
}
