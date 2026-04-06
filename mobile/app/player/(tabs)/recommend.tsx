import React, { useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Info, Sparkles, WandSparkles, ChevronLeft } from 'lucide-react-native';
import { HeroSlider, HeroText } from '../../../components/ui/heroui';
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
  useStrings,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  buildRecommendationPayload,
  mapBackendStringToStringItem,
  mapRecommendationResponse,
} from '../../../services/backendMappers';

const priorityLabels = [
  { key: 'power', title: 'Power and rebound' },
  { key: 'control', title: 'Control and touch' },
  { key: 'durability', title: 'Durability' },
  { key: 'comfort', title: 'Comfort' },
  { key: 'sound', title: 'Hitting sound' },
] as const;

export default function RecommendationInputScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);
  const setLiveRecommendationResults = useAppStore(
    (state) => state.setLiveRecommendationResults,
  );
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  if (!user || user.role !== 'player') {
    return null;
  }

  const [playingStyle, setPlayingStyle] = useState(user.playingStyle);
  const [skillLevel, setSkillLevel] = useState(user.skillLevel);
  const [priorities, setPriorities] = useState(user.priorities);

  const strongestPriority = useMemo(
    () =>
      Object.entries(priorities).sort((left, right) => right[1] - left[1])[0]?.[0] ?? 'power',
    [priorities]
  );

  const handleGenerate = async () => {
    setSubmitError(null);

    if (!token) {
      router.push('/player/recommend/results');
      return;
    }

    setIsGenerating(true);
    try {
      const availableStrings =
        strings.length > 0
          ? strings
          : (await backendApi.listStrings(token)).items.map((item) =>
              mapBackendStringToStringItem(item),
            );
      if (strings.length === 0) {
        setLiveStrings(availableStrings);
      }
      const response = await backendApi.previewRecommendations(
        token,
        buildRecommendationPayload({
          userId: user.id,
          skillLevel,
          playingStyle,
          preferredTension: user.preferredTension,
          playFrequency: user.playFrequency,
          priorities,
        }),
      );
      setLiveRecommendationResults(
        mapRecommendationResponse(response, availableStrings),
      );
      router.push('/player/recommend/results');
    } catch (error) {
      setSubmitError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to generate recommendation.',
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <AppScreen
      title="Recommendation lab"
      subtitle="Shape the session profile before generating your shortlist."
      headerLeft={
        router.canGoBack() ? (
          <AppIconButton
            icon={<ChevronLeft size={20} color="#111827" />}
            accessibilityLabel="Go back"
            onPress={() => router.back()}
          />
        ) : undefined
      }
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <AppChip label="AI MATCH INPUT" variant="secondary" className="self-start" />
            <HeroText className="mt-4 text-[26px] font-bold tracking-tight text-white leading-[32px]">
              Build today&apos;s string profile.
            </HeroText>
            <HeroText className="mt-3 text-sm leading-6 text-primary-100">
              Adjust the player context first so the shortlist feels grounded and believable.
            </HeroText>
          </View>
          <View className="h-14 w-14 items-center justify-center rounded-[22px] bg-white/12">
            <WandSparkles size={24} color="white" />
          </View>
        </View>

        <View className="mt-7 flex-row gap-3">
          <View className="min-h-[100px] flex-1 rounded-[26px] border border-white/20 bg-white/12 p-4">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-100/80">
              Default tension
            </HeroText>
            <HeroText className="mt-2 text-lg font-bold text-white">
              {user.preferredTension} lbs
            </HeroText>
          </View>
          <View className="min-h-[100px] flex-1 rounded-[26px] border border-white/20 bg-white/12 p-4">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-100/80">
              Strongest priority
            </HeroText>
            <HeroText className="mt-2 text-lg font-bold text-white">
              {strongestPriority}
            </HeroText>
          </View>
        </View>
      </AppCard>

      <AppSection eyebrow="Profile overlay" title="Adjust today’s playing context" subtitle="Keep the recommendation inputs easy to read in the demo.">
        <AppCard variant="elevated" padding="lg">
          <HeroText className="text-sm font-semibold uppercase tracking-[0.18em] text-neutral-400">
            Playing style
          </HeroText>
          <View className="mt-4 flex-row flex-wrap gap-2">
            {(['Attacking', 'Balanced', 'Control', 'Defensive'] as const).map((style) => (
              <AppChip
                key={style}
                label={style}
                size="md"
                variant={playingStyle === style ? 'primary' : 'neutral'}
                onPress={() => setPlayingStyle(style)}
              />
            ))}
          </View>

          <HeroText className="mt-6 text-sm font-semibold uppercase tracking-[0.18em] text-neutral-400">
            Skill level
          </HeroText>
          <View className="mt-4 flex-row flex-wrap gap-2">
            {(['Beginner', 'Intermediate', 'Advanced', 'Competitive'] as const).map((level) => (
              <AppChip
                key={level}
                label={level}
                size="md"
                variant={skillLevel === level ? 'info' : 'neutral'}
                onPress={() => setSkillLevel(level)}
              />
            ))}
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Priority mixer" title="Refine what matters most" subtitle="Make the weighting explicit so every recommendation feels explainable.">
        <View className="gap-4">
          {priorityLabels.map((item) => (
            <AppCard key={item.key} variant="elevated" padding="md">
              <View className="flex-row items-center justify-between gap-4">
                <View>
                  <HeroText className="text-base font-semibold text-neutral-900">
                    {item.title}
                  </HeroText>
                  <HeroText className="mt-1 text-xs uppercase tracking-[0.2em] text-neutral-400">
                    Priority weight
                  </HeroText>
                </View>
                <AppChip label={`${priorities[item.key]}/10`} variant="primary" />
              </View>
              <View className="mt-5">
                <HeroSlider
                  value={priorities[item.key]}
                  onValueChange={(nextValue) => setPriorities((current) => ({ ...current, [item.key]: nextValue }))}
                  minimumValue={1}
                  maximumValue={10}
                  step={1}
                />
              </View>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Context" title="What will this recommendation consider?">
        <AppCard variant="subtle" padding="md">
          <View className="flex-row gap-3">
            <Info size={18} color="#0891B2" />
            <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
              Style, skill level, preferred tension, and your five weighted priorities feed the ranking engine shown on the next screen.
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      {submitError ? (
        <AppCard variant="subtle" className="mt-4 border border-red-100" padding="md">
          <HeroText className="text-sm font-medium text-red-600">
            {submitError}
          </HeroText>
        </AppCard>
      ) : null}

      <View className="mt-10">
        <AppButton
          label="Generate recommendation"
          size="lg"
          onPress={handleGenerate}
          isLoading={isGenerating}
        />
        <Pressable className="mt-4 items-center" onPress={() => router.push('/player/profile/edit')}>
          <HeroText className="text-sm font-semibold text-primary-700">
            Edit my saved player profile
          </HeroText>
        </Pressable>
      </View>
    </AppScreen>
  );
}
