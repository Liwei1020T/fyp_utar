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
import { FloatingCompareTray } from '../../../components/shared/FloatingCompareTray';
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

  const topPriority = Object.entries(user.priorities).sort((a, b) => b[1] - a[1])[0]?.[0];
  const recapLine = `Based on: ${user.playingStyle} · ${user.skillLevel} · ${user.preferredTension} lbs · ${topPriority} priority`;

  return (
    <View className="flex-1">
      <AppScreen
        title="Shortlist"
        subtitle="Ranked matches explaining fit and trade-offs."
        headerLeft={
          <AppIconButton
            icon={<ChevronLeft size={20} color="#111827" />}
            accessibilityLabel="Go back"
            onPress={() => router.back()}
          />
        }
      >
        {isLive && liveResults.length === 0 ? (
          <AppCard variant="subtle" className="mt-6" padding="lg">
            <HeroText className="text-lg font-bold text-neutral-900">
              No backend results yet.
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              Generate a shortlist from the recommendation lab to see ranked results here.
            </HeroText>
            <AppButton
              label="Back to recommendation lab"
              className="mt-6"
              onPress={() => router.replace('/player/recommend')}
            />
          </AppCard>
        ) : (
          <AppCard variant="subtle" className="mb-6 rounded-2xl border border-primary-100" padding="md">
            <View className="flex-row items-center gap-3">
              <View className="h-10 w-10 items-center justify-center rounded-full bg-primary-100">
                <Sparkles size={20} color="#0284c7" />
              </View>
              <View className="flex-1">
                <HeroText className="text-base font-bold text-neutral-900">
                  Found {isLive ? liveResults.length : ranked.length} matches
                </HeroText>
                <HeroText className="text-xs text-neutral-500" numberOfLines={1}>
                  {recapLine}
                </HeroText>
              </View>
            </View>
          </AppCard>
        )}

        <AppSection eyebrow="Ranked shortlist" title="Decision cards">
          <View className="gap-5 pb-10">
            {!isLive &&
              ranked.map(({ item, matchScore }, index) => {
              const normalizedScore = Math.max(82, Math.min(98, Math.round(matchScore / 3.5)));
              const isSelected = compareSelection.includes(item.id);
              const isTop = index === 0;

              return (
                <AppCard key={item.id} variant={isTop ? 'highlighted' : 'elevated'} padding="md">
                  <View className="flex-row items-start justify-between">
                    <View className="flex-1">
                      <View className="flex-row items-center gap-2">
                        <AppChip 
                          label={isTop ? 'Best match' : `Option ${index + 1}`} 
                          variant={isTop ? 'primary' : 'neutral'} 
                          size="sm"
                        />
                        <HeroText className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                          {item.brand}
                        </HeroText>
                      </View>
                      <HeroText className="mt-2 text-xl font-bold tracking-tight text-neutral-950">
                        {item.model}
                      </HeroText>
                      <HeroText className="mt-1 text-sm font-semibold text-primary-700">
                        {normalizedScore}% match
                      </HeroText>
                    </View>
                    <View className="items-end">
                      <HeroText className="text-xs font-medium text-neutral-400">
                        Price at shop
                      </HeroText>
                    </View>
                  </View>

                  <View className="mt-4 gap-2">
                    <View className="flex-row items-start gap-2">
                      <View className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary-500" />
                      <HeroText className="flex-1 text-sm leading-5 text-neutral-700">
                        <HeroText className="font-bold">Fit:</HeroText> Best for {item.bestFor[0]?.toLowerCase()} emphasizing {topPriority}.
                      </HeroText>
                    </View>
                    <View className="flex-row items-start gap-2">
                      <View className="mt-1.5 h-1.5 w-1.5 rounded-full bg-orange-400" />
                      <HeroText className="flex-1 text-sm leading-5 text-neutral-700">
                        <HeroText className="font-bold">Trade-off:</HeroText> {item.tradeOffs[0]}
                      </HeroText>
                    </View>
                  </View>

                  <View className="mt-4 flex-row flex-wrap gap-2">
                    {item.strengths.slice(0, 3).map((strength) => (
                      <AppChip key={strength} label={strength} variant="secondary" size="sm" />
                    ))}
                  </View>

                  <View className="mt-4 rounded-xl bg-neutral-50 px-3 py-2">
                    <HeroText className="text-xs text-neutral-500">
                      Suggested tension: <HeroText className="font-bold text-neutral-700">{user.preferredTension} - {user.preferredTension + 1} lbs</HeroText>
                    </HeroText>
                  </View>

                  <View className="mt-5 gap-3">
                    <AppButton
                      label="Book this string"
                      variant={isTop ? 'primary' : 'outline'}
                      size="md"
                      trailingIcon={isTop ? <ArrowRight size={16} color="white" /> : undefined}
                      onPress={() => router.push(`/player/bookings/new?stringId=${item.id}`)}
                    />
                    <View className="flex-row gap-3">
                      <AppButton
                        label="Explain fit"
                        variant="ghost"
                        size="sm"
                        className="flex-1"
                        onPress={() => router.push(`/player/recommend/explain/${item.id}`)}
                      />
                      <AppButton
                        label={isSelected ? 'Selected' : 'Compare'}
                        variant={isSelected ? 'secondary' : 'ghost'}
                        size="sm"
                        className="flex-1"
                        leadingIcon={<Scale size={14} color={isSelected ? '#78350F' : '#64748b'} />}
                        onPress={() => toggleCompareSelection(item.id)}
                      />
                    </View>
                  </View>
                </AppCard>
              );
            })}

            {isLive &&
              liveResults.map((item, index) => {
                const isSelected = item.stringId ? compareSelection.includes(item.stringId) : false;
                const isTop = index === 0;
                const topAspectLabels = Object.entries(item.aspectScores)
                  .sort((left, right) => right[1] - left[1])
                  .slice(0, 2)
                  .map(([label]) => label.replace(/_/g, ' '));

                return (
                  <AppCard key={item.id} variant={isTop ? 'highlighted' : 'elevated'} padding="md">
                    <View className="flex-row items-start justify-between">
                      <View className="flex-1">
                        <View className="flex-row items-center gap-2">
                          <AppChip 
                            label={isTop ? 'Best match' : `Option ${index + 1}`} 
                            variant={isTop ? 'primary' : 'neutral'} 
                            size="sm"
                          />
                          <HeroText className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                            {item.brand}
                          </HeroText>
                        </View>
                        <HeroText className="mt-2 text-xl font-bold tracking-tight text-neutral-950">
                          {item.modelName}
                        </HeroText>
                        <HeroText className="mt-1 text-sm font-semibold text-primary-700">
                          {item.matchScore}% match
                        </HeroText>
                      </View>
                      <View className="items-end">
                        <HeroText className="text-xs font-medium text-neutral-400">
                          Vendor quote
                        </HeroText>
                      </View>
                    </View>

                    <View className="mt-4 gap-2">
                      <View className="flex-row items-start gap-2">
                        <View className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary-500" />
                        <HeroText className="flex-1 text-sm leading-5 text-neutral-700">
                          <HeroText className="font-bold">Fit:</HeroText> {item.reasons[0] ?? 'Ranked highly for your session profile.'}
                        </HeroText>
                      </View>
                      <View className="flex-row items-start gap-2">
                        <View className="mt-1.5 h-1.5 w-1.5 rounded-full bg-orange-400" />
                        <HeroText className="flex-1 text-sm leading-5 text-neutral-700">
                          <HeroText className="font-bold">Trade-off:</HeroText> Slightly lower fit confidence than the top match.
                        </HeroText>
                      </View>
                    </View>

                    <View className="mt-4 flex-row flex-wrap gap-2">
                      {topAspectLabels.map((label) => (
                        <AppChip key={label} label={label} variant="secondary" size="sm" />
                      ))}
                    </View>

                    <View className="mt-4 rounded-xl bg-neutral-50 px-3 py-2">
                      <HeroText className="text-xs text-neutral-500">
                        Suggested tension: <HeroText className="font-bold text-neutral-700">{item.suggestedTensionRange}</HeroText>
                      </HeroText>
                    </View>

                    <View className="mt-5 gap-3">
                      <AppButton
                        label="Book this string"
                        variant={isTop ? 'primary' : 'outline'}
                        size="md"
                        trailingIcon={isTop ? <ArrowRight size={16} color="white" /> : undefined}
                        isDisabled={!item.stringId}
                        onPress={() => item.stringId ? router.push(`/player/bookings/new?stringId=${item.stringId}`) : undefined}
                      />
                      <View className="flex-row gap-3">
                        <AppButton
                          label="Explain fit"
                          variant="ghost"
                          size="sm"
                          className="flex-1"
                          isDisabled={!item.stringId}
                          onPress={() => item.stringId ? router.push(`/player/recommend/explain/${item.stringId}`) : undefined}
                        />
                        <AppButton
                          label={isSelected ? 'Selected' : 'Compare'}
                          variant={isSelected ? 'secondary' : 'ghost'}
                          size="sm"
                          className="flex-1"
                          leadingIcon={<Scale size={14} color={isSelected ? '#78350F' : '#64748b'} />}
                          isDisabled={!item.stringId}
                          onPress={() => item.stringId && toggleCompareSelection(item.stringId)}
                        />
                      </View>
                    </View>
                  </AppCard>
                );
              })}
          </View>
        </AppSection>
      </AppScreen>

      <FloatingCompareTray />
    </View>
  );
}
