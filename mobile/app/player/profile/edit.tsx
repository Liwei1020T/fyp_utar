import React, { useState } from 'react';
import { Alert, Platform, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Sparkles } from 'lucide-react-native';
import { HeroSlider, HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { AppSelect } from '../../../components/ui/AppSelect';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { AppMotion } from '../../../components/ui/AppMotion';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
} from '../../../store/appStore';
import { formatPlayFrequency } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  buildBackendProfilePayload,
  deriveAdvancedPreferences,
  mapBackendUserToPlayerProfile,
} from '../../../services/backendMappers';
import type { PlayerProfile } from '../../../types/domain';

const profileSchema = z.object({
  name: z.string().min(2, 'Please enter your name'),
  skillLevel: z.enum(['Beginner', 'Intermediate', 'Advanced']),
  playingStyle: z.enum(['Attacking', 'Balanced', 'Control']),
  preferredFeel: z.enum(['Soft', 'Medium', 'Hard']),
  preferredGauge: z.enum(['No preference', 'Thin', 'Medium', 'Thick']),
  preferredTension: z.coerce.number().min(18).max(32),
  playFrequency: z.enum(['Social', 'Weekly', 'Tournament']),
  recentGoal: z.enum([
    'Balanced setup',
    'More power',
    'Better control',
    'More durability',
    'More comfort',
    'Hold tension longer',
    'Better value',
  ]),
});

type ProfileForm = z.infer<typeof profileSchema>;
type ProfileFormInput = z.input<typeof profileSchema>;

const priorityKeys = [
  { key: 'power', label: 'Power' },
  { key: 'control', label: 'Control' },
  { key: 'durability', label: 'Durability' },
  { key: 'comfort', label: 'Comfort' },
  { key: 'sound', label: 'Sound' },
  { key: 'value', label: 'Value for money' },
] as const;

const advancedPreferenceKeys = [
  {
    key: 'elasticity',
    label: 'Elasticity',
    description: 'How much elastic rebound you want from the string bed.',
  },
  {
    key: 'tensionRetention',
    label: 'Tension retention',
    description: 'How important it is that the string keeps its feel over time.',
  },
  {
    key: 'stringMovement',
    label: 'String movement',
    description: 'How much you care about a stable string bed after rallies.',
  },
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
const preferredFeelOptions = ['Soft', 'Medium', 'Hard'] as const;
const preferredGaugeOptions = ['No preference', 'Thin', 'Medium', 'Thick'] as const;
const recentGoalOptions = [
  'Balanced setup',
  'More power',
  'Better control',
  'More durability',
  'More comfort',
  'Hold tension longer',
  'Better value',
] as const;

export default function ProfileEditScreen() {
  const user = useCurrentUser();

  if (!user || user.role !== 'player') {
    return null;
  }

  return <ProfileEditContent user={user} />;
}

function ProfileEditContent({ user }: { user: PlayerProfile }) {
  const router = useRouter();
  const params = useLocalSearchParams<{ onboarding?: string }>();
  const updatePlayerProfile = useAppStore((state) => state.updatePlayerProfile);
  const token = useBackendAccessToken();
  const [saveError, setSaveError] = useState<string | null>(null);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const isOnboarding = params.onboarding === '1';
  const stepCopy = {
    1: {
      title: 'Tell us how you play.',
      description:
        'Start with your playing identity and the result you want from your next restring.',
    },
    2: {
      title: 'Shape your ideal setup.',
      description: 'Set your impact feel, preferred gauge, and usual tension.',
    },
    3: {
      title: 'Tune what matters most.',
      description: 'Review the priorities used to rank every recommendation.',
    },
  }[step];

  const normalizedPlayingStyle =
    user.playingStyle === 'Attacking' || user.playingStyle === 'Balanced'
      ? user.playingStyle
      : 'Control';
  const normalizedSkillLevel =
    user.skillLevel === 'Beginner' || user.skillLevel === 'Intermediate'
      ? user.skillLevel
      : 'Advanced';
  const savedPreferredFeel = user.preferredFeel ?? 'Medium';

  const [priorities, setPriorities] = useState(user.priorities);
  const [advancedPreferences, setAdvancedPreferences] = useState(
    user.advancedPreferences ?? deriveAdvancedPreferences(user.priorities),
  );

  const {
    control,
    getValues,
    handleSubmit,
    setValue,
    trigger,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormInput, unknown, ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user.name,
      skillLevel: normalizedSkillLevel,
      playingStyle: normalizedPlayingStyle,
      preferredFeel: savedPreferredFeel,
      preferredGauge: user.preferredGauge ?? 'No preference',
      preferredTension: user.preferredTension,
      playFrequency: user.playFrequency,
      recentGoal: user.recentGoal,
    },
  });

  const onSubmit = async (data: ProfileForm) => {
    setSaveError(null);
    if (!token) {
      setSaveError('Your player session expired. Sign in again before saving.');
      return;
    }

    try {
      const profile = await backendApi.saveProfile(
        token,
        buildBackendProfilePayload({
          name: data.name,
          skillLevel: data.skillLevel,
          playingStyle: data.playingStyle,
          playFrequency: data.playFrequency,
          preferredFeel: data.preferredFeel,
          preferredGauge: data.preferredGauge,
          preferredTension: data.preferredTension,
          recentGoal: data.recentGoal,
          priorities,
          advancedPreferences,
        }),
      );
      updatePlayerProfile(
        user.id,
        mapBackendUserToPlayerProfile(
          {
            id: user.id,
            username: profile.username,
            phone_number: user.phone,
            role: 'customer',
            auth_provider: 'local',
            external_auth_id: null,
            is_active: true,
          },
          profile,
        ),
      );
      router.replace(isOnboarding ? '/player' : '/player/profile');
    } catch (error) {
      setSaveError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to save your live player profile.',
      );
    }
  };

  const continueToNextStep = async () => {
    const fields =
      step === 1
        ? ([
            'name',
            'recentGoal',
            'playingStyle',
            'skillLevel',
            'playFrequency',
          ] as const)
        : (['preferredFeel', 'preferredGauge', 'preferredTension'] as const);
    const isValid = await trigger(fields);
    if (!isValid) {
      return;
    }

    if (step === 2) {
      const { skillLevel, preferredTension } = getValues();
      const tension = Number(preferredTension);
      if (skillLevel === 'Beginner' && tension > 25) {
        const adjustTension = () => {
          setValue('preferredTension', 25, {
            shouldDirty: true,
            shouldValidate: true,
          });
          setStep(3);
        };
        const keepTension = () => setStep(3);
        if (Platform.OS === 'web') {
          if (
            globalThis.confirm?.(
              `For beginners, 22–25 lbs is recommended. You selected ${tension} lbs.\n\nPress OK to adjust to 25 lbs, or Cancel to keep your selection.`,
            )
          ) {
            adjustTension();
          } else {
            keepTension();
          }
          return;
        }
        Alert.alert(
          'High tension for a beginner',
          `For beginners, 22–25 lbs is recommended. You selected ${tension} lbs.`,
          [
            {
              text: 'Adjust to 25 lbs',
              onPress: adjustTension,
            },
            {
              text: `Keep ${tension} lbs`,
              onPress: keepTension,
            },
          ],
        );
        return;
      }
    }

    setStep((current) => (current === 1 ? 2 : 3));
  };

  const goToPreviousStep = () => {
    setStep((current) => (current === 3 ? 2 : 1));
  };

  return (
    <AppScreen
      headerVariant="flow"
      title={isOnboarding ? 'Set up your profile' : 'Edit player profile'}
      subtitle="Three short steps create a recommendation profile you can update anytime."
      showBackButton={!isOnboarding || step > 1}
      onBackPress={() => {
        if (step > 1) {
          goToPreviousStep();
          return;
        }
        router.back();
      }}
      footer={
        <View className="gap-2 border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          {saveError ? (
            <HeroText
              accessibilityLiveRegion="polite"
              className="text-sm font-medium text-red-600"
            >
              {saveError}
            </HeroText>
          ) : null}
          {step > 1 ? (
            <AppButton
              label="Back"
              variant="ghost"
              onPress={goToPreviousStep}
            />
          ) : null}
          {step < 3 ? (
            <AppButton
              label={step === 1 ? 'Continue to setup' : 'Review preferences'}
              size="lg"
              onPress={() => void continueToNextStep()}
            />
          ) : (
            <>
              <AppButton
                label={isOnboarding ? 'Finish profile' : 'Save profile'}
                size="lg"
                onPress={handleSubmit(onSubmit)}
                isLoading={isSubmitting}
              />
              <AppButton
                label="Reset preference sliders"
                variant="outline"
                onPress={() => {
                  setPriorities({
                    power: 5,
                    control: 5,
                    durability: 5,
                    comfort: 5,
                    sound: 5,
                    value: 5,
                  });
                  setAdvancedPreferences({
                    elasticity: 5,
                    tensionRetention: 5,
                    stringMovement: 5,
                  });
                }}
              />
            </>
          )}
        </View>
      }
    >
      <AppCard variant="highlighted" className="rounded-[32px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
              Step {step} of 3
            </HeroText>
            <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-neutral-950">
              {stepCopy.title}
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              {stepCopy.description}
            </HeroText>
          </View>
          <View className="h-12 w-12 items-center justify-center rounded-2xl bg-primary-600">
            <Sparkles size={20} color="white" />
          </View>
        </View>
        <View
          accessibilityRole="progressbar"
          accessibilityValue={{ min: 1, max: 3, now: step }}
          className="mt-5 h-2 overflow-hidden rounded-full bg-white/80"
        >
          <View
            className="h-full rounded-full bg-primary-600"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </View>
      </AppCard>

      <AppMotion key={step} className="gap-5">
      {step === 1 ? (
        <>
      <AppSection eyebrow="Identity" title="Player basics">
        <AppCard variant="elevated" padding="lg">
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
              <AppSelect
                label="Recent goal"
                value={value}
                options={recentGoalOptions.map((option) => ({ id: option, label: option }))}
                onChange={onChange}
                className="mt-4"
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
            <AppSelect
              label="Playing style"
              value={value}
              options={styleOptions.map((style) => ({
                id: style.value,
                label: style.label,
                description: style.description,
              }))}
              onChange={onChange}
            />
          )}
        />
      </AppSection>

      <AppSection eyebrow="Level" title="Experience and playing volume">
        <View className="gap-4">
          <Controller
            control={control}
            name="skillLevel"
            render={({ field: { onChange, value } }) => (
              <AppSelect
                label="Skill level"
                value={value}
                options={skillOptions.map((level) => ({ id: level, label: level }))}
                onChange={onChange}
              />
            )}
          />

          <Controller
            control={control}
            name="playFrequency"
            render={({ field: { onChange, value } }) => (
              <AppSelect
                label="Play frequency"
                value={value}
                options={(['Social', 'Weekly', 'Tournament'] as const).map((frequency) => ({
                  id: frequency,
                  label: formatPlayFrequency(frequency),
                }))}
                onChange={onChange}
              />
            )}
          />
        </View>
      </AppSection>

        </>
      ) : null}

      {step === 2 ? (
        <>
      <AppSection
        eyebrow="FEEL"
        title="How should the string feel on impact?"
        subtitle="This helps the system match strings to your preferred hitting sensation."
      >
        <Controller
          control={control}
          name="preferredFeel"
          render={({ field: { onChange, value } }) => (
            <AppSelect
              label="Preferred feel"
              value={value}
              options={preferredFeelOptions.map((option) => ({ id: option, label: option }))}
              onChange={onChange}
            />
          )}
        />
      </AppSection>

      <AppSection
        eyebrow="GAUGE"
        title="Preferred string gauge"
        subtitle="A soft preference only; every available string remains eligible."
      >
        <Controller
          control={control}
          name="preferredGauge"
          render={({ field: { onChange, value } }) => (
            <AppSelect
              label="Preferred gauge"
              value={value}
              options={preferredGaugeOptions.map((option) => ({ id: option, label: option }))}
              onChange={onChange}
            />
          )}
        />
      </AppSection>

      <AppSection
        eyebrow="TENSION"
        title="Preferred tension"
        subtitle="Your usual restring tension in lbs."
      >
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
      </AppSection>

        </>
      ) : null}

      {step === 3 ? (
        <>
      <AppSection
        eyebrow="PRIORITIES"
        title="What matters most in your setup?"
        subtitle="Adjust the weighting used in recommendations."
      >
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

      <AppButton
        label={showAdvanced ? 'Hide advanced tuning' : 'Fine-tune advanced signals'}
        variant="outline"
        onPress={() => setShowAdvanced((current) => !current)}
      />

      {showAdvanced ? (
        <AppSection
          eyebrow="ADVANCED"
          title="Advanced recommendation preferences"
          subtitle="Optional fine-tuning for advanced string performance signals."
        >
          <View className="mt-2 gap-4">
            {advancedPreferenceKeys.map((item) => (
              <AppCard key={item.key} variant="elevated" padding="md">
                <View className="flex-row items-center justify-between gap-3">
                  <View className="flex-1">
                    <HeroText className="text-base font-semibold text-neutral-900">
                      {item.label}
                    </HeroText>
                    <HeroText className="mt-1 text-xs leading-5 text-neutral-500">
                      {item.description}
                    </HeroText>
                  </View>
                  <AppChip
                    label={`${advancedPreferences[item.key]}/10`}
                    variant="secondary"
                  />
                </View>
                <View className="mt-5">
                  <HeroSlider
                    value={advancedPreferences[item.key]}
                    onValueChange={(nextValue) =>
                      setAdvancedPreferences((current) => ({
                        ...current,
                        [item.key]: nextValue,
                      }))
                    }
                    minimumValue={1}
                    maximumValue={10}
                    step={1}
                  />
                </View>
              </AppCard>
            ))}
          </View>
        </AppSection>
      ) : null}

        </>
      ) : null}
      </AppMotion>

    </AppScreen>
  );
}
