import React, { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { ChevronLeft, Sparkles } from 'lucide-react-native';
import { HeroSlider, HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
} from '../../../store/appStore';
import { formatPlayFrequency } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  buildBackendProfilePayload,
  mapBackendUserToPlayerProfile,
} from '../../../services/backendMappers';

const profileSchema = z.object({
  name: z.string().min(2, 'Please enter your name'),
  skillLevel: z.enum(['Beginner', 'Intermediate', 'Advanced']),
  playingStyle: z.enum(['Attacking', 'Balanced', 'Control']),
  preferredTension: z.coerce.number().min(18).max(32),
  playFrequency: z.enum(['Social', 'Weekly', 'Tournament']),
  recentGoal: z.string().min(8, 'Tell us what you want from your next setup'),
});

type ProfileForm = z.infer<typeof profileSchema>;
type ProfileFormInput = z.input<typeof profileSchema>;

const priorityKeys = [
  { key: 'power', label: 'Power' },
  { key: 'control', label: 'Control' },
  { key: 'durability', label: 'Durability' },
  { key: 'comfort', label: 'Comfort' },
  { key: 'sound', label: 'Sound' },
] as const;

const styleOptions = [
  {
    value: 'Attacking',
    label: 'Attacking',
    description: 'Fast rebound, crisp contact, and confident pressure in drives.',
  },
  {
    value: 'Balanced',
    label: 'Balanced',
    description: 'A little bit of everything with reliable all-court feel.',
  },
  {
    value: 'Control',
    label: 'Control / Defensive',
    description: 'Touch, placement, comfort, and patient rallies over raw punch.',
  },
] as const;

const skillOptions = ['Beginner', 'Intermediate', 'Advanced'] as const;

export default function ProfileEditScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const updatePlayerProfile = useAppStore((state) => state.updatePlayerProfile);
  const token = useBackendAccessToken();
  const [saveError, setSaveError] = useState<string | null>(null);

  if (!user || user.role !== 'player') {
    return null;
  }

  const normalizedPlayingStyle =
    user.playingStyle === 'Attacking' || user.playingStyle === 'Balanced'
      ? user.playingStyle
      : 'Control';
  const normalizedSkillLevel =
    user.skillLevel === 'Beginner' || user.skillLevel === 'Intermediate'
      ? user.skillLevel
      : 'Advanced';

  const [priorities, setPriorities] = useState(user.priorities);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormInput, unknown, ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user.name,
      skillLevel: normalizedSkillLevel,
      playingStyle: normalizedPlayingStyle,
      preferredTension: user.preferredTension,
      playFrequency: user.playFrequency,
      recentGoal: user.recentGoal,
    },
  });

  const onSubmit = async (data: ProfileForm) => {
    setSaveError(null);
    await new Promise((resolve) => setTimeout(resolve, 250));

    if (token) {
      try {
        const profile = await backendApi.saveProfile(
          token,
          buildBackendProfilePayload({
            skillLevel: data.skillLevel,
            playingStyle: data.playingStyle,
            playFrequency: data.playFrequency,
            preferredTension: data.preferredTension,
            priorities,
          }),
        );
        updatePlayerProfile(
          user.id,
          mapBackendUserToPlayerProfile(
            {
              id: user.id,
              username: data.name,
              phone_number: user.phone,
              role: 'customer',
              auth_provider: 'local',
              external_auth_id: null,
            },
            profile,
          ),
        );
      } catch (error) {
        setSaveError(
          error instanceof BackendApiError
            ? error.message
            : 'Failed to save your live player profile.',
        );
        return;
      }
    }

    updatePlayerProfile(user.id, {
      ...data,
      priorities,
    });
    router.replace('/player/profile');
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Player profile"
      subtitle="Make onboarding feel premium and keep recommendations grounded in real preferences."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="highlighted" className="rounded-[32px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
              Onboarding polish
            </HeroText>
            <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-neutral-950">
              Capture the feel your game actually needs.
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              Skill level, style, priorities, and tension preference feed every recommendation, comparison, and booking shortcut.
            </HeroText>
          </View>
          <View className="h-12 w-12 items-center justify-center rounded-2xl bg-primary-600">
            <Sparkles size={20} color="white" />
          </View>
        </View>
      </AppCard>

      <AppSection eyebrow="Identity" title="Player basics">
        <AppCard variant="elevated" padding="lg">
          {saveError ? (
            <HeroText className="mb-4 text-sm font-medium text-red-600">
              {saveError}
            </HeroText>
          ) : null}
          <Controller
            control={control}
            name="name"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Display name"
                placeholder="Your name"
                value={value}
                onChangeText={onChange}
                error={errors.name?.message}
              />
            )}
          />

          <Controller
            control={control}
            name="recentGoal"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Current setup goal"
                placeholder="e.g. More punch on clears without losing net control"
                value={value}
                onChangeText={onChange}
                error={errors.recentGoal?.message}
                multiline
                inputClassName="min-h-24"
              />
            )}
          />
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Style" title="Select your playing identity">
        <Controller
          control={control}
          name="playingStyle"
          render={({ field: { onChange, value } }) => (
            <View className="flex-row flex-wrap gap-3">
              {styleOptions.map((style) => (
                <Pressable
                  key={style.value}
                  className="w-full"
                  onPress={() => onChange(style.value)}
                >
                  <AppCard
                    variant={value === style.value ? 'highlighted' : 'elevated'}
                    padding="md"
                  >
                    <HeroText className="text-base font-bold tracking-tight text-neutral-950">
                      {style.label}
                    </HeroText>
                    <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
                      {style.description}
                    </HeroText>
                  </AppCard>
                </Pressable>
              ))}
            </View>
          )}
        />
      </AppSection>

      <AppSection eyebrow="Level" title="Experience and playing volume">
        <View className="gap-4">
          <Controller
            control={control}
            name="skillLevel"
            render={({ field: { onChange, value } }) => (
              <View className="flex-row flex-wrap gap-2">
                {skillOptions.map((level) => (
                  <AppChip
                    key={level}
                    label={level}
                    size="md"
                    variant={value === level ? 'primary' : 'neutral'}
                    onPress={() => onChange(level)}
                  />
                ))}
              </View>
            )}
          />

          <Controller
            control={control}
            name="playFrequency"
            render={({ field: { onChange, value } }) => (
              <View className="flex-row flex-wrap gap-2">
                {(['Social', 'Weekly', 'Tournament'] as const).map((frequency) => (
                  <AppChip
                    key={frequency}
                    label={formatPlayFrequency(frequency)}
                    size="md"
                    variant={value === frequency ? 'info' : 'neutral'}
                    onPress={() => onChange(frequency)}
                  />
                ))}
              </View>
            )}
          />
        </View>
      </AppSection>

      <AppSection eyebrow="Feel" title="Tension and priority weighting">
        <Controller
          control={control}
          name="preferredTension"
          render={({ field: { onChange, value } }) => (
            <AppInput
              label="Preferred tension"
              placeholder="26"
              keyboardType="numeric"
              value={String(value)}
              onChangeText={onChange}
              error={errors.preferredTension?.message}
            />
          )}
        />

        <View className="mt-2 gap-4">
          {priorityKeys.map((item) => (
            <AppCard key={item.key} variant="elevated" padding="md">
              <View className="flex-row items-center justify-between">
                <HeroText className="text-base font-semibold text-neutral-900">
                  {item.label}
                </HeroText>
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

      <View className="mb-12 mt-8">
        <AppButton
          label="Save player profile"
          size="lg"
          onPress={handleSubmit(onSubmit)}
          isLoading={isSubmitting}
        />
      </View>
    </AppScreen>
  );
}
