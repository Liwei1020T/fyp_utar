import React from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft, Sparkles } from 'lucide-react-native';
import { HeroText } from '../../../../components/ui/heroui';
import { AppButton } from '../../../../components/ui/AppButton';
import { AppCard } from '../../../../components/ui/AppCard';
import { AppChip } from '../../../../components/ui/AppChip';
import { AppScreen } from '../../../../components/shared/AppScreen';
import { AppSection } from '../../../../components/shared/AppSection';
import {
  useCurrentUser,
  useLiveRecommendationResults,
} from '../../../../store/appStore';
import { getStringById } from '../../../../services/mockAppService';

export default function RecommendationExplanationScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const user = useCurrentUser();
  const liveResults = useLiveRecommendationResults();
  const stringItem = getStringById(params.id);
  const liveResult = liveResults.find(
    (item) => item.stringId === params.id || item.id === params.id,
  );

  if (!user || user.role !== 'player') {
    return null;
  }

  if (!stringItem) {
    return (
      <AppScreen title="Explanation unavailable">
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            We couldn&apos;t find this recommendation.
          </HeroText>
          <AppButton label="Back to results" className="mt-6" onPress={() => router.replace('/player/results')} />
        </AppCard>
      </AppScreen>
    );
  }

  return (
    <AppScreen
      headerVariant="secondary"
      title="Recommendation explanation"
      subtitle="Break down why this string fits your current player profile."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
          {stringItem.brand}
        </HeroText>
        <HeroText className="mt-3 text-[30px] font-bold tracking-tight text-white">
          {stringItem.model}
        </HeroText>
        <HeroText className="mt-3 text-sm leading-6 text-primary-100">
          This recommendation is anchored on your {user.playingStyle.toLowerCase()} style, {user.skillLevel.toLowerCase()} level, and preference for {Object.entries(user.priorities).sort((a, b) => b[1] - a[1])[0]?.[0]}.
        </HeroText>
      </AppCard>

      <AppSection eyebrow="Why it fits" title="Match logic">
        <View className="gap-3">
          <AppCard variant="elevated" padding="md">
            <HeroText className="text-base font-semibold text-neutral-950">
              Style fit
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              {liveResult?.reasons[0] ??
                `${stringItem.bestFor[0]} aligns with how you currently describe your game.`}{' '}
              The string stays lively without drifting too far from your preferred tension baseline.
            </HeroText>
          </AppCard>
          <AppCard variant="elevated" padding="md">
            <HeroText className="text-base font-semibold text-neutral-950">
              Priority fit
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              {liveResult?.reasons[1]
                ? `${liveResult.reasons[1]}. `
                : ''}Your strongest weighted priorities are {Object.entries(user.priorities)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 2)
                .map(([key]) => key)
                .join(' and ')}. This string performs well across those areas.
            </HeroText>
          </AppCard>
          <AppCard variant="elevated" padding="md">
            <HeroText className="text-base font-semibold text-neutral-950">
              Tension fit
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              Recommended tension range is {liveResult?.suggestedTensionRange ?? `${stringItem.recommendedTension[0]} to ${stringItem.recommendedTension[1]} lbs`}. Your saved {user.preferredTension} lbs setup sits comfortably inside that window.
            </HeroText>
          </AppCard>
        </View>
      </AppSection>

      <AppSection eyebrow="Strengths and trade-offs" title="What you gain and what you give up">
        <View className="gap-3">
          {stringItem.strengths.map((strength) => (
            <AppCard key={strength} variant="highlighted" padding="sm">
              <HeroText className="text-sm font-semibold text-neutral-900">{strength}</HeroText>
            </AppCard>
          ))}
          {stringItem.tradeOffs.map((tradeOff) => (
            <AppCard key={tradeOff} variant="subtle" padding="sm">
              <HeroText className="text-sm leading-6 text-neutral-600">{tradeOff}</HeroText>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="For the demo" title="How to continue">
        <View className="flex-row flex-wrap gap-2">
          <AppChip label="Compare with shortlist" variant="neutral" />
          <AppChip label="Book from here" variant="primary" />
        </View>
      </AppSection>

      <View className="mb-10 mt-8 gap-3">
        <AppButton label="Book this string" size="lg" onPress={() => router.push(`/player/bookings/new?stringId=${stringItem.id}`)} />
      </View>
    </AppScreen>
  );
}
