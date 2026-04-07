import React from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, ChevronLeft, Scale, Sparkles } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useLiveRecommendationResults,
} from '../../../store/appStore';
import { MOCK_STRINGS } from '../../../mocks/strings';
import { formatCurrency } from '../../../lib/formatters';

export default function RecommendationResultsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const liveResults = useLiveRecommendationResults();
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);
  const compareSelection = useAppStore((state) => state.compareSelection);

  if (!user || user.role !== 'player') {
    return null;
  }

  const ranked = [...MOCK_STRINGS]
    .map((item) => ({
      item,
      matchScore:
        item.ratings.power * user.priorities.power +
        item.ratings.control * user.priorities.control +
        item.ratings.durability * user.priorities.durability +
        item.ratings.comfort * user.priorities.comfort +
        item.ratings.sound * user.priorities.sound,
    }))
    .sort((left, right) => right.matchScore - left.matchScore)
    .slice(0, 3);

  const isLive = Boolean(token);

  return (
    <AppScreen
      title="Recommendation results"
      subtitle="Each result explains fit, strengths, and what you trade off."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      {isLive && liveResults.length === 0 ? (
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            No live recommendation results yet.
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Generate a shortlist from the recommendation lab to see backend-ranked results here.
          </HeroText>
          <AppButton
            label="Back to recommendation lab"
            className="mt-6"
            onPress={() => router.replace('/player/recommend')}
          />
        </AppCard>
      ) : null}

      {!isLive ? (
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <View className="items-center">
          <View className="h-20 w-20 items-center justify-center rounded-full bg-white/10">
            <Sparkles size={34} color="white" strokeWidth={1.7} />
          </View>
          <HeroText className="mt-5 text-center text-[28px] font-bold tracking-tight text-white">
            Found {ranked.length} strong matches
          </HeroText>
          <HeroText className="mt-2 text-center text-sm leading-6 text-primary-100">
            Ranked from your current {user.playingStyle.toLowerCase()} profile, {user.preferredTension} lbs baseline, and five weighted priorities.
          </HeroText>
        </View>
      </AppCard>
      ) : (
        <AppCard variant="dark" className="rounded-[32px]" padding="lg">
          <View className="items-center">
            <View className="h-20 w-20 items-center justify-center rounded-full bg-white/10">
              <Sparkles size={34} color="white" strokeWidth={1.7} />
            </View>
            <HeroText className="mt-5 text-center text-[28px] font-bold tracking-tight text-white">
              Found {liveResults.length} backend matches
            </HeroText>
            <HeroText className="mt-2 text-center text-sm leading-6 text-primary-100">
              Ranked from your live player context using the current rules-based recommendation engine.
            </HeroText>
          </View>
        </AppCard>
      )}

      <AppSection eyebrow="Ranked shortlist" title="Top strings for this session">
        <View className="gap-5">
          {!isLive &&
            ranked.map(({ item, matchScore }, index) => {
            const normalizedScore = Math.max(82, Math.min(98, Math.round(matchScore / 3.5)));
            const isSelected = compareSelection.includes(item.id);

            return (
              <AppCard key={item.id} variant={index === 0 ? 'highlighted' : 'elevated'} padding="lg">
                <View className="flex-row items-start justify-between gap-4">
                  <View className="flex-1">
                    <View className="flex-row items-center gap-2">
                      <AppChip label={index === 0 ? 'Best match' : `Option ${index + 1}`} variant={index === 0 ? 'primary' : 'neutral'} />
                      <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
                        {item.brand}
                      </HeroText>
                    </View>
                    <HeroText className="mt-3 text-[24px] font-bold tracking-tight text-neutral-950">
                      {item.model}
                    </HeroText>
                    <HeroText className="mt-2 text-sm font-semibold text-primary-700">
                      {normalizedScore}% match
                    </HeroText>
                    <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
                      Best for {item.bestFor[0]?.toLowerCase()} because it fits your emphasis on {Object.entries(user.priorities).sort((a, b) => b[1] - a[1])[0]?.[0]} and a {user.playingStyle.toLowerCase()} response profile.
                    </HeroText>
                  </View>
                  <View className="rounded-[22px] bg-primary-600 px-4 py-3">
                    <HeroText className="text-lg font-bold text-white">
                      {formatCurrency(item.price)}
                    </HeroText>
                  </View>
                </View>

                <View className="mt-5 flex-row flex-wrap gap-2">
                  {item.strengths.map((strength) => (
                    <AppChip key={strength} label={strength} variant="secondary" />
                  ))}
                </View>

                <AppCard variant="subtle" className="mt-4" padding="sm">
                  <HeroText className="text-sm leading-6 text-neutral-600">
                    Trade-off: {item.tradeOffs[0]}
                  </HeroText>
                </AppCard>

                <View className="mt-6 gap-3">
                  <AppButton
                    label="Book this string"
                    size="md"
                    trailingIcon={<ArrowRight size={16} color="white" />}
                    onPress={() => router.push(`/player/bookings/new?stringId=${item.id}`)}
                  />
                  <View className="flex-row gap-3">
                    <AppButton
                      label="Explain fit"
                      variant="outline"
                      size="md"
                      className="flex-1"
                      onPress={() => router.push(`/player/recommend/explain/${item.id}`)}
                    />
                    <AppButton
                      label={isSelected ? 'Selected' : 'Compare'}
                      variant={isSelected ? 'secondary' : 'outline'}
                      size="md"
                      className="flex-1"
                      leadingIcon={<Scale size={16} color={isSelected ? '#78350F' : '#475569'} />}
                      onPress={() => toggleCompareSelection(item.id)}
                    />
                  </View>
                </View>
              </AppCard>
            );
          })}

          {isLive &&
            liveResults.map((item, index) => {
              const isSelected = item.stringId
                ? compareSelection.includes(item.stringId)
                : false;
              const topAspectLabels = Object.entries(item.aspectScores)
                .sort((left, right) => right[1] - left[1])
                .slice(0, 3)
                .map(([label, value]) => `${label.replace(/_/g, ' ')} ${Math.round(value * 10)}/10`);

              return (
                <AppCard
                  key={item.id}
                  variant={index === 0 ? 'highlighted' : 'elevated'}
                  padding="lg"
                >
                  <View className="flex-row items-start justify-between gap-4">
                    <View className="flex-1">
                      <View className="flex-row items-center gap-2">
                        <AppChip
                          label={index === 0 ? 'Best match' : `Option ${index + 1}`}
                          variant={index === 0 ? 'primary' : 'neutral'}
                        />
                        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
                          {item.brand}
                        </HeroText>
                      </View>
                      <HeroText className="mt-3 text-[24px] font-bold tracking-tight text-neutral-950">
                        {item.modelName}
                      </HeroText>
                      <HeroText className="mt-2 text-sm font-semibold text-primary-700">
                        {item.matchScore}% match
                      </HeroText>
                      <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
                        {item.reasons[0] ?? 'Ranked highly by the current rules-based matcher.'}
                      </HeroText>
                    </View>
                    <View className="rounded-[22px] bg-primary-600 px-4 py-3">
                      <HeroText className="text-lg font-bold text-white">
                        {formatCurrency(item.price)}
                      </HeroText>
                    </View>
                  </View>

                  <View className="mt-5 flex-row flex-wrap gap-2">
                    {topAspectLabels.map((label) => (
                      <AppChip key={label} label={label} variant="secondary" />
                    ))}
                  </View>

                  <AppCard variant="subtle" className="mt-4" padding="sm">
                    <HeroText className="text-sm leading-6 text-neutral-600">
                      Suggested tension: {item.suggestedTensionRange}
                    </HeroText>
                  </AppCard>

                  <View className="mt-6 gap-3">
                    <AppButton
                      label="Book this string"
                      size="md"
                      trailingIcon={<ArrowRight size={16} color="white" />}
                      isDisabled={!item.stringId}
                      onPress={() =>
                        item.stringId
                          ? router.push(`/player/bookings/new?stringId=${item.stringId}`)
                          : undefined
                      }
                    />
                    <View className="flex-row gap-3">
                      <AppButton
                        label="Explain fit"
                        variant="outline"
                        size="md"
                        className="flex-1"
                        isDisabled={!item.stringId}
                        onPress={() =>
                          item.stringId
                            ? router.push(`/player/recommend/explain/${item.stringId}`)
                            : undefined
                        }
                      />
                      <AppButton
                        label={isSelected ? 'Selected' : 'Compare'}
                        variant={isSelected ? 'secondary' : 'outline'}
                        size="md"
                        className="flex-1"
                        leadingIcon={
                          <Scale
                            size={16}
                            color={isSelected ? '#78350F' : '#475569'}
                          />
                        }
                        isDisabled={!item.stringId}
                        onPress={() => {
                          if (item.stringId) {
                            toggleCompareSelection(item.stringId);
                          }
                        }}
                      />
                    </View>
                  </View>
                </AppCard>
              );
            })}
        </View>
      </AppSection>

      {compareSelection.length >= 2 ? (
        <AppButton
          label="Open compare view"
          variant="dark"
          size="lg"
          onPress={() => router.push('/player/strings/compare')}
          className="mt-4"
        />
      ) : null}
    </AppScreen>
  );
}
