import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendRacketToRacketPassport } from '../../../services/backendMappers';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useRackets,
} from '../../../store/appStore';

const racketSchema = z.object({
  nickname: z.string().trim().min(1, 'Nickname is required').max(80),
  brand: z.string().trim().min(1, 'Brand is required').max(100),
  model: z.string().trim().min(1, 'Model is required').max(100),
  weightClass: z.string().trim().max(30),
  balancePoint: z.string().trim().max(50),
  gripSize: z.string().trim().max(30),
  preferredUse: z.string().trim().max(120),
  notes: z.string().trim().max(1000),
});

type RacketFormInput = z.input<typeof racketSchema>;
type RacketForm = z.output<typeof racketSchema>;

export default function NewRacketScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const rackets = useRackets();
  const setLiveRackets = useAppStore((state) => state.setLiveRackets);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RacketFormInput, unknown, RacketForm>({
    resolver: zodResolver(racketSchema),
    defaultValues: {
      nickname: '',
      brand: '',
      model: '',
      weightClass: '',
      balancePoint: '',
      gripSize: '',
      preferredUse: '',
      notes: '',
    },
  });

  if (!user || user.role !== 'player') {
    return null;
  }

  const onSubmit = async (data: RacketForm) => {
    if (!token) {
      setSubmitError('A live player login is required to register a racket.');
      return;
    }

    setSubmitError(null);
    try {
      const response = await backendApi.createRacket(token, {
        nickname: data.nickname,
        brand: data.brand,
        model: data.model,
        weight_class: data.weightClass || null,
        balance_point: data.balancePoint || null,
        grip_size: data.gripSize || null,
        preferred_use: data.preferredUse || null,
        notes: data.notes || null,
      });
      const created = mapBackendRacketToRacketPassport(response);
      setLiveRackets([
        created,
        ...rackets.filter((item) => item.id !== created.id),
      ]);
      router.replace(`/player/rackets/${created.id}`);
    } catch (error) {
      setSubmitError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to register the racket.',
      );
    }
  };

  return (
    <AppScreen
      headerVariant="flow"
      title="Register racket"
      subtitle="Create a durable passport before linking the frame to future bookings."
      showBackButton
      onBackPress={() => router.back()}
    >
      {!token ? (
        <AppCard variant="subtle" className="mb-4" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Your player session expired. Sign in again before registering a
            racket.
          </HeroText>
        </AppCard>
      ) : null}

      <AppSection eyebrow="Identity" title="Name this frame">
        <AppCard variant="elevated" padding="md">
          <Controller
            control={control}
            name="nickname"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Nickname"
                placeholder="Match Day 88D"
                value={value}
                onChangeText={onChange}
                error={errors.nickname?.message}
                maxLength={80}
              />
            )}
          />
          <Controller
            control={control}
            name="brand"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Brand"
                placeholder="Yonex"
                value={value}
                onChangeText={onChange}
                error={errors.brand?.message}
                maxLength={100}
              />
            )}
          />
          <Controller
            control={control}
            name="model"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Model"
                placeholder="Astrox 88D Pro"
                value={value}
                onChangeText={onChange}
                error={errors.model?.message}
                maxLength={100}
              />
            )}
          />
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Specs" title="Optional racket details">
        <AppCard variant="elevated" padding="md">
          <Controller
            control={control}
            name="weightClass"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Weight class"
                placeholder="3U or 4U"
                value={value}
                onChangeText={onChange}
                error={errors.weightClass?.message}
                maxLength={30}
              />
            )}
          />
          <Controller
            control={control}
            name="balancePoint"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Balance point"
                placeholder="Head heavy, even, or head light"
                value={value}
                onChangeText={onChange}
                error={errors.balancePoint?.message}
                maxLength={50}
              />
            )}
          />
          <Controller
            control={control}
            name="gripSize"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Grip size"
                placeholder="G5"
                value={value}
                onChangeText={onChange}
                error={errors.gripSize?.message}
                maxLength={30}
              />
            )}
          />
          <Controller
            control={control}
            name="preferredUse"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Preferred use"
                placeholder="Attack-heavy doubles"
                value={value}
                onChangeText={onChange}
                error={errors.preferredUse?.message}
                maxLength={120}
              />
            )}
          />
          <Controller
            control={control}
            name="notes"
            render={({ field: { onChange, value } }) => (
              <AppInput
                label="Notes"
                placeholder="Feel preferences or frame-specific notes..."
                value={value}
                onChangeText={onChange}
                error={errors.notes?.message}
                maxLength={1000}
                multiline
                inputClassName="min-h-24"
              />
            )}
          />
        </AppCard>
      </AppSection>

      {submitError ? (
        <AppCard
          variant="subtle"
          className="mt-4 border border-red-100"
          padding="md"
        >
          <HeroText className="text-sm font-medium text-red-600">
            {submitError}
          </HeroText>
        </AppCard>
      ) : null}

      <View className="mb-12 mt-8 gap-3">
        <AppButton
          label="Register racket"
          size="lg"
          isLoading={isSubmitting}
          isDisabled={!token}
          onPress={handleSubmit(onSubmit)}
        />
        <AppButton
          label="Cancel"
          variant="outline"
          size="lg"
          onPress={() => router.back()}
        />
      </View>
    </AppScreen>
  );
}
