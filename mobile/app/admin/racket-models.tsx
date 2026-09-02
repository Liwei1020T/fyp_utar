import React, { useCallback, useState } from 'react';
import { useFocusEffect, useRouter } from 'expo-router';
import { CircleDot, EyeOff, Plus } from 'lucide-react-native';
import { View } from 'react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { appChromeColors } from '../../components/ui/theme';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { useBackendAccessToken, useCurrentUser } from '../../store/appStore';
import type { BackendAdminRacketModel } from '../../types/backend';

function sortModels(models: BackendAdminRacketModel[]) {
  return [...models].sort((left, right) => {
    if (left.is_active !== right.is_active) {
      return left.is_active ? -1 : 1;
    }
    return `${left.brand} ${left.model}`.localeCompare(
      `${right.brand} ${right.model}`,
    );
  });
}

export default function AdminRacketModelsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const isAdmin = user?.role === 'admin';
  const [models, setModels] = useState<BackendAdminRacketModel[]>([]);
  const [brand, setBrand] = useState('');
  const [model, setModel] = useState('');
  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [isSaving, setIsSaving] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const refreshModels = useCallback(async () => {
    if (!isAdmin) {
      return;
    }
    if (!token) {
      setIsLoading(false);
      setError('A live admin login is required to manage racket models.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await backendApi.adminListRacketModels(token);
      setModels(sortModels(response));
    } catch (loadError) {
      setError(
        loadError instanceof BackendApiError
          ? loadError.message
          : 'Failed to load racket models.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [isAdmin, token]);

  useFocusEffect(
    useCallback(() => {
      void refreshModels();
    }, [refreshModels]),
  );

  if (!isAdmin) {
    return null;
  }

  const addModel = async () => {
    const nextBrand = brand.trim();
    const nextModel = model.trim();
    if (!nextBrand || !nextModel) {
      setError('Enter both a racket brand and model.');
      setSuccess(null);
      return;
    }
    if (!token) {
      setError('Your admin session expired. Sign in again before saving.');
      setSuccess(null);
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const created = await backendApi.adminCreateRacketModel(token, {
        brand: nextBrand,
        model: nextModel,
      });
      setModels((current) => sortModels([...current, created]));
      setBrand('');
      setModel('');
      setSuccess(`${created.brand} ${created.model} is now available to players.`);
    } catch (saveError) {
      setError(
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to add the racket model.',
      );
    } finally {
      setIsSaving(false);
    }
  };

  const toggleModel = async (item: BackendAdminRacketModel) => {
    if (!token) {
      setError('Your admin session expired. Sign in again before changing visibility.');
      setSuccess(null);
      return;
    }

    setUpdatingId(item.id);
    setError(null);
    setSuccess(null);
    try {
      const updated = await backendApi.adminUpdateRacketModel(token, item.id, {
        is_active: !item.is_active,
      });
      setModels((current) =>
        sortModels(current.map((modelItem) => (modelItem.id === updated.id ? updated : modelItem))),
      );
      setSuccess(
        updated.is_active
          ? `${updated.brand} ${updated.model} is visible to players.`
          : `${updated.brand} ${updated.model} is hidden from new selections.`,
      );
    } catch (updateError) {
      setError(
        updateError instanceof BackendApiError
          ? updateError.message
          : 'Failed to update racket model visibility.',
      );
    } finally {
      setUpdatingId(null);
    }
  };

  const activeCount = models.filter((item) => item.is_active).length;

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title="Racket models"
      subtitle="Manage the models players can choose when registering a racket."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection
        eyebrow="Player selection"
        title="Add a model"
        subtitle="Only active models appear in the player racket selector."
      >
        <AppCard variant="highlighted" padding="md">
          <AppInput
            label="Brand"
            placeholder="Yonex"
            value={brand}
            onChangeText={setBrand}
            maxLength={100}
          />
          <AppInput
            label="Model"
            placeholder="Astrox 100 ZZ"
            value={model}
            onChangeText={setModel}
            maxLength={100}
          />
          <AppButton
            label="Add racket model"
            leadingIcon={<Plus size={18} color="#FFFFFF" />}
            isLoading={isSaving}
            onPress={() => void addModel()}
          />
        </AppCard>
      </AppSection>

      <AppSection
        eyebrow="Catalog"
        title="Available models"
        subtitle={`${activeCount} visible to players · ${models.length} total`}
      >
        <View className="gap-3">
          {isLoading ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-600">
                Loading racket models...
              </HeroText>
            </AppCard>
          ) : null}
          {!isLoading && models.length === 0 ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm font-semibold text-neutral-900">
                No racket models yet.
              </HeroText>
              <HeroText className="mt-1 text-sm leading-6 text-neutral-600">
                Add the first model above to make it available during player registration.
              </HeroText>
            </AppCard>
          ) : null}
          {models.map((item) => (
            <AppCard
              key={item.id}
              variant={item.is_active ? 'elevated' : 'subtle'}
              padding="md"
            >
              <View className="flex-row items-start gap-3">
                <View className="h-10 w-10 items-center justify-center rounded-[12px] border border-primary-200 bg-primary-50">
                  {item.is_active ? (
                    <CircleDot size={19} color={appChromeColors.primary} />
                  ) : (
                    <EyeOff size={19} color={appChromeColors.textMuted} />
                  )}
                </View>
                <View className="min-w-0 flex-1">
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-700">
                    {item.brand}
                  </HeroText>
                  <HeroText className="mt-1 text-[16px] font-bold tracking-tight text-neutral-950">
                    {item.model}
                  </HeroText>
                  <AppChip
                    label={item.is_active ? 'Visible to players' : 'Hidden from players'}
                    variant={item.is_active ? 'success' : 'neutral'}
                    size="md"
                    className="mt-2 self-start"
                  />
                </View>
              </View>
              <AppButton
                label={item.is_active ? 'Hide from new selections' : 'Show to players'}
                variant="outline"
                size="sm"
                className="mt-3"
                isLoading={updatingId === item.id}
                onPress={() => void toggleModel(item)}
              />
            </AppCard>
          ))}
        </View>
      </AppSection>

      {success ? (
        <AppCard variant="subtle" className="mt-4 border border-success-100" padding="md">
          <HeroText className="text-sm font-semibold text-success-700">Saved</HeroText>
          <HeroText className="mt-1 text-sm leading-6 text-success-700">{success}</HeroText>
        </AppCard>
      ) : null}
      {error ? (
        <AppCard variant="subtle" className="mt-4 border border-red-100" padding="md">
          <HeroText className="text-sm font-semibold text-red-600">{error}</HeroText>
        </AppCard>
      ) : null}
    </AppScreen>
  );
}
