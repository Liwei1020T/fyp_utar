import React, { useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Info, WandSparkles } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useStrings,
} from '../../../store/appStore';
import { formatPlayFrequency } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  mapBackendStringToStringItem,
  mapRecommendationResponse,
  deriveAdvancedPreferences,
} from '../../../services/backendMappers';
import type { PlayerProfile } from '../../../types/domain';

const priorityLabels = [
  { key: 'power', title: 'Power and rebound' },
  { key: 'control', title: 'Control and touch' },
  { key: 'durability', title: 'Durability' },
  { key: 'comfort', title: 'Comfort' },
  { key: 'sound', title: 'Hitting sound' },
] as const;

function clampPreference(value: number) {
  return Math.max(1, Math.min(10, Math.round(value)));
}

const styleOptions = [
  { value: 'Attacking', label: 'Attacking' },
  { value: 'Balanced', label: 'Balanced' },
  { value: 'Control', label: 'Control / Defensive' },
] as const;

const skillOptions = ['Beginner', 'Intermediate', 'Advanced'] as const;

export default function RecommendationInputScreen() {
  const user = useCurrentUser();

  if (!user || user.role !== 'player') {
    return null;
  }

  return <RecommendationInputContent user={user} />;
}

function RecommendationInputContent({ user }: { user: PlayerProfile }) {
  const router = useRouter();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const setLiveStrings = useAppStore((state) => state.setLiveStrings);
  const setLiveRecommendationResults = useAppStore(
    (state) => state.setLiveRecommendationResults,
  );
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const normalizedPlayingStyle =
    user.playingStyle === 'Attacking' || user.playingStyle === 'Balanced'
      ? user.playingStyle
      : 'Control';
  const normalizedSkillLevel =
    user.skillLevel === 'Beginner' || user.skillLevel === 'Intermediate'
      ? user.skillLevel
      : 'Advanced';
  const savedBudgetRange = user.budgetRange ?? 'RM30–RM50';
  const savedPreferredFeel = user.preferredFeel ?? 'Balanced';

  const playingStyle = normalizedPlayingStyle;
  const skillLevel = normalizedSkillLevel;
  const priorities = user.priorities;

  const strongestPriority = useMemo(() => {
    const top = Object.entries(priorities).sort((left, right) => right[1] - left[1])[0];
    const label = priorityLabels.find((l) => l.key === top?.[0]);
    return label ? label.title.split(' ')[0] : 'Power';
  }, [priorities]);

  const handleGenerate = async () => {
    setSubmitError(null);

    if (!token) {
      setSubmitError('Your player session expired. Sign in again to generate recommendations.');
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
      const response = await backendApi.generateRecommendations(token, 3);
      setLiveRecommendationResults(
        mapRecommendationResponse(response, availableStrings),
      );
      router.push('/player/results');
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

  const topThreePriorities = useMemo(() => {
    return Object.entries(priorities)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([key]) => priorityLabels.find((p) => p.key === key)?.title.split(' ')[0])
      .join(', ');
  }, [priorities]);
  const advancedPreferences = useMemo(
    () => {
      const savedAdvanced =
        user.advancedPreferences ?? deriveAdvancedPreferences(priorities);
      return [
        {
          label: 'Elasticity',
          value: clampPreference(savedAdvanced.elasticity),
        },
        {
          label: 'Tension retention',
          value: clampPreference(savedAdvanced.tensionRetention),
        },
        {
          label: 'String movement',
          value: clampPreference(savedAdvanced.stringMovement),
        },
      ];
    },
    [priorities, user.advancedPreferences],
  );

  return (
    <AppScreen
      headerVariant="flow"
      title="Recommendation lab"
      subtitle="Generate a backend-scored shortlist from your saved player profile."
      showBackButton={router.canGoBack()}
      onBackPress={() => router.back()}
    >
      <AppCard variant="dark" className="rounded-[24px]" padding="md">
        <View className="flex-row items-center justify-between gap-4">
          <View className="flex-1">
            <AppChip label="RECOMMENDATION" variant="accent" size="sm" className="self-start" />
            <HeroText className="mt-2 text-xl font-bold tracking-tight text-white">
              Use your saved profile.
            </HeroText>
          </View>
          <View className="h-10 w-10 items-center justify-center rounded-xl bg-white/12">
            <WandSparkles size={20} color="white" />
          </View>
        </View>

        <View className="mt-4 flex-row gap-2">
          <View className="flex-1 rounded-2xl border border-white/18 bg-white/8 p-3">
            <HeroText className="text-[10px] font-semibold uppercase tracking-[0.12em] text-primary-100/75">
              Tension
            </HeroText>
            <HeroText className="mt-1 text-base font-bold text-white">
              {user.preferredTension} lbs
            </HeroText>
          </View>
          <View className="flex-1 rounded-2xl border border-white/18 bg-white/8 p-3">
            <HeroText className="text-[10px] font-semibold uppercase tracking-[0.12em] text-primary-100/75">
              Priority
            </HeroText>
            <HeroText className="mt-1 text-base font-bold text-white">
              {strongestPriority}
            </HeroText>
          </View>
        </View>
      </AppCard>

      <AppSection title="Live Profile Summary" className="mt-2">
        <AppCard variant="subtle" padding="sm" className="border-dashed border-neutral-200">
          <View className="flex-row flex-wrap gap-y-2">
            <View className="w-1/2 pr-2">
              <HeroText className="text-[10px] font-bold uppercase text-neutral-400">Style</HeroText>
              <HeroText className="text-sm font-medium text-neutral-800">{playingStyle}</HeroText>
            </View>
            <View className="w-1/2">
              <HeroText className="text-[10px] font-bold uppercase text-neutral-400">Skill</HeroText>
              <HeroText className="text-sm font-medium text-neutral-800">{skillLevel}</HeroText>
            </View>
            <View className="w-full mt-1">
              <HeroText className="text-[10px] font-bold uppercase text-neutral-400">Top Priorities</HeroText>
              <HeroText className="text-sm font-medium text-primary-600">{topThreePriorities}</HeroText>
            </View>
            <View className="w-1/2 mt-1 pr-2">
              <HeroText className="text-[10px] font-bold uppercase text-neutral-400">Budget</HeroText>
              <HeroText className="text-sm font-medium text-neutral-800">{savedBudgetRange}</HeroText>
            </View>
            <View className="w-1/2 mt-1">
              <HeroText className="text-[10px] font-bold uppercase text-neutral-400">Feel</HeroText>
              <HeroText className="text-sm font-medium text-neutral-800">{savedPreferredFeel}</HeroText>
            </View>
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Context" title="Saved Player Context">
        <AppCard variant="elevated" padding="md" className="gap-4">
          <View>
            <HeroText className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">Playing style</HeroText>
            <View className="mt-2 flex-row flex-wrap gap-2">
              {styleOptions.map((style) => (
                <AppChip
                  key={style.value}
                  label={style.label}
                  size="sm"
                  variant={playingStyle === style.value ? 'primary' : 'neutral'}
                />
              ))}
            </View>
          </View>

          <View>
            <HeroText className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">Skill level</HeroText>
            <View className="mt-2 flex-row flex-wrap gap-2">
              {skillOptions.map((level) => (
                <AppChip
                  key={level}
                  label={level}
                  size="sm"
                  variant={skillLevel === level ? 'primary' : 'neutral'}
                />
              ))}
            </View>
          </View>

          <View className="flex-row items-center justify-between">
            <HeroText className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">Play frequency</HeroText>
            <AppChip label={formatPlayFrequency(user.playFrequency)} size="sm" variant="secondary" />
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Matrix input" title="Saved Priority Weights">
        <View className="gap-3">
          {priorityLabels.map((item) => (
            <AppCard key={item.key} variant="elevated" padding="sm" className="px-4 py-3">
              <View className="flex-row items-center justify-between">
                <HeroText className="text-sm font-bold text-neutral-900">
                  {item.title}
                </HeroText>
                <HeroText className="text-sm font-black text-primary-600">
                  {priorities[item.key]}/10
                </HeroText>
              </View>
              <View className="mt-3">
                <View className="h-2 overflow-hidden rounded-full bg-neutral-100">
                  <View
                    className="h-full rounded-full bg-primary-600"
                    style={{ width: `${Math.max(10, priorities[item.key] * 10)}%` }}
                  />
                </View>
              </View>
            </AppCard>
          ))}
          <AppCard variant="subtle" padding="md" className="rounded-[24px]">
            <HeroText className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">
              Advanced preferences
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              These editable inputs help the recommendation engine account for
              elasticity, tension retention, and string movement.
            </HeroText>
            <View className="mt-4 flex-row flex-wrap gap-2">
              {advancedPreferences.map((item) => (
                <AppChip
                  key={item.label}
                  label={`${item.label} ${item.value}/10`}
                  variant="neutral"
                />
              ))}
            </View>
          </AppCard>
        </View>
      </AppSection>

      <AppSection>
        <AppCard variant="subtle" padding="sm" className="bg-primary-50/50 border-0">
          <View className="flex-row items-center gap-2">
            <Info size={14} color="#2F64B6" />
            <HeroText className="flex-1 text-[13px] leading-5 text-neutral-600">
              Recommendations combine your preferences with verified string
              specifications, playing characteristics, and budget fit.
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

      <View className="mt-8 mb-6">
        <AppButton
          label="Generate recommendation"
          size="lg"
          onPress={handleGenerate}
          isLoading={isGenerating}
        />
        <Pressable className="mt-4 items-center" onPress={() => router.push('/player/profile/edit')}>
          <HeroText className="text-xs font-bold text-primary-700 uppercase tracking-widest">
            Edit profile and advanced preferences
          </HeroText>
        </Pressable>
      </View>
    </AppScreen>
  );
}
