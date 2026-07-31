import React, { useCallback, useState } from 'react';
import { Alert, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppButton } from '../../../components/ui/AppButton';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  useAppStore,
  useBackendAccessToken,
  useCurrentUser,
  useRackets,
  useStrings,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendRacketToRacketPassport } from '../../../services/backendMappers';
import { formatDateTime } from '../../../lib/formatters';
import type { RacketPassport } from '../../../types/domain';

interface RacketEditFields {
  nickname: string;
  brand: string;
  model: string;
  weightClass: string;
  balancePoint: string;
  gripSize: string;
  preferredUse: string;
  notes: string;
}

function editFieldsFor(racket: RacketPassport): RacketEditFields {
  return {
    nickname: racket.nickname,
    brand: racket.brand,
    model: racket.model,
    weightClass:
      racket.weightClass === 'Not recorded' ? '' : racket.weightClass,
    balancePoint:
      racket.balancePoint === 'Not recorded' ? '' : racket.balancePoint,
    gripSize: racket.gripSize === 'Not recorded' ? '' : racket.gripSize,
    preferredUse:
      racket.preferredUse === 'Not recorded' ? '' : racket.preferredUse,
    notes: racket.notes,
  };
}

export default function RacketPassportDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const racketId = params.id;
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const rackets = useRackets();
  const strings = useStrings();
  const upsertLiveRacket = useAppStore((state) => state.upsertLiveRacket);
  const removeLiveRacket = useAppStore((state) => state.removeLiveRacket);
  const [isLoading, setIsLoading] = useState(Boolean(token && racketId));
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [editFields, setEditFields] = useState<RacketEditFields | null>(null);

  const refreshRacket = useCallback(async () => {
    if (!token || !racketId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      const detail = mapBackendRacketToRacketPassport(
        await backendApi.fetchRacket(token, racketId),
      );
      upsertLiveRacket(detail);
    } catch (error) {
      setLoadError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to load this racket passport.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [racketId, token, upsertLiveRacket]);

  useFocusEffect(
    useCallback(() => {
      void refreshRacket();
    }, [refreshRacket]),
  );

  if (!user || user.role !== 'player') {
    return null;
  }

  const racket = rackets.find(
    (item) => item.playerId === user.id && item.id === racketId,
  );

  if (!racketId || (!isLoading && !racket)) {
    return (
      <AppScreen
        title="Racket not found"
        subtitle="This passport is unavailable or does not belong to your account."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Return to your racket list and choose a valid saved frame.
          </HeroText>
          {loadError ? (
            <HeroText className="mt-2 text-sm font-medium text-red-600">
              {loadError}
            </HeroText>
          ) : null}
          <View className="mt-4 gap-3">
            {racketId && token ? (
              <AppButton
                label="Retry"
                variant="outline"
                isLoading={isLoading}
                onPress={() => void refreshRacket()}
              />
            ) : null}
            <AppButton
              label="Back to rackets"
              onPress={() => router.replace('/player/rackets')}
            />
          </View>
        </AppCard>
      </AppScreen>
    );
  }

  if (!racket) {
    return (
      <AppScreen
        title="Loading racket"
        subtitle="Fetching the passport and completed service history."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Loading racket details...
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  const currentString = strings.find(
    (item) => item.id === racket.currentStringId,
  );
  const averageTension =
    racket.stringHistory.length > 0
      ? Math.round(
          racket.stringHistory.reduce((sum, item) => sum + item.tension, 0) /
            racket.stringHistory.length,
        )
      : 0;

  const beginEditing = () => {
    setEditFields(editFieldsFor(racket));
    setSaveError(null);
    setIsEditing(true);
  };

  const patchEditField = (
    field: keyof RacketEditFields,
    value: string,
  ) => {
    setEditFields((current) =>
      current ? { ...current, [field]: value } : current,
    );
  };

  const saveRacket = async () => {
    if (!token || !editFields) {
      setSaveError('A live player login is required to edit this passport.');
      return;
    }
    if (
      !editFields.nickname.trim() ||
      !editFields.brand.trim() ||
      !editFields.model.trim()
    ) {
      setSaveError('Nickname, brand, and model are required.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    try {
      const response = await backendApi.updateRacket(token, racket.id, {
        nickname: editFields.nickname.trim(),
        brand: editFields.brand.trim(),
        model: editFields.model.trim(),
        weight_class: editFields.weightClass.trim() || null,
        balance_point: editFields.balancePoint.trim() || null,
        grip_size: editFields.gripSize.trim() || null,
        preferred_use: editFields.preferredUse.trim() || null,
        notes: editFields.notes.trim() || null,
      });
      const updatedBase = mapBackendRacketToRacketPassport(response);
      const updated: RacketPassport = {
        ...updatedBase,
        serviceCount: racket.serviceCount,
        currentStringId: racket.currentStringId,
        currentTension: racket.currentTension,
        preferredRange: racket.preferredRange,
        lastServicedAt: racket.lastServicedAt,
        stringHistory: racket.stringHistory,
      };
      upsertLiveRacket(updated);
      setEditFields(editFieldsFor(updated));
      setIsEditing(false);
    } catch (error) {
      setSaveError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to update this racket.',
      );
    } finally {
      setIsSaving(false);
    }
  };

  const deleteRacket = () => {
    if (!token) {
      return;
    }
    Alert.alert(
      'Delete racket passport?',
      'Completed booking history stays on the booking records.',
      [
        { text: 'Keep passport', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            setIsDeleting(true);
            setSaveError(null);
            void backendApi
              .deleteRacket(token, racket.id)
              .then(() => {
                removeLiveRacket(racket.id);
                router.replace('/player/rackets');
              })
              .catch((error: unknown) => {
                setSaveError(
                  error instanceof BackendApiError
                    ? error.message
                    : 'Failed to delete this racket passport.',
                );
              })
              .finally(() => setIsDeleting(false));
          },
        },
      ],
    );
  };

  return (
    <AppScreen
      headerVariant="secondary"
      title={racket.nickname}
      subtitle="Racket profile and completed stringing history."
      showBackButton
      onBackPress={() => router.back()}
    >
      {loadError ? (
        <AppCard
          variant="subtle"
          className="mb-4 border border-red-100"
          padding="md"
        >
          <HeroText className="text-sm font-medium text-red-600">
            {loadError}
          </HeroText>
          <AppButton
            label="Retry history"
            variant="outline"
            className="mt-4"
            isLoading={isLoading}
            onPress={() => void refreshRacket()}
          />
        </AppCard>
      ) : null}

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

      <View className="mt-4 gap-3">
        <AppButton
          label="Book with this racket"
          onPress={() =>
            router.push(`/player/bookings/new?racketId=${racket.id}`)
          }
        />
        {token ? (
          <>
            <AppButton
              label={isEditing ? 'Close editor' : 'Edit passport'}
              variant="outline"
              onPress={() =>
                isEditing ? setIsEditing(false) : beginEditing()
              }
            />
            <AppButton
              label="Delete passport"
              variant="outline"
              isLoading={isDeleting}
              onPress={deleteRacket}
            />
          </>
        ) : (
          <AppCard variant="subtle" padding="sm">
            <HeroText className="text-sm leading-6 text-neutral-600">
              Your player session expired. Sign in again to edit this passport.
            </HeroText>
          </AppCard>
        )}
        {!isEditing && saveError ? (
          <HeroText className="text-sm font-medium text-red-600">
            {saveError}
          </HeroText>
        ) : null}
      </View>

      {isEditing && editFields ? (
        <AppSection eyebrow="Edit" title="Passport details">
          <AppCard variant="elevated" padding="md">
            <AppInput
              label="Nickname"
              value={editFields.nickname}
              onChangeText={(value) => patchEditField('nickname', value)}
              maxLength={80}
            />
            <AppInput
              label="Brand"
              value={editFields.brand}
              onChangeText={(value) => patchEditField('brand', value)}
              maxLength={100}
            />
            <AppInput
              label="Model"
              value={editFields.model}
              onChangeText={(value) => patchEditField('model', value)}
              maxLength={100}
            />
            <AppInput
              label="Weight class"
              value={editFields.weightClass}
              onChangeText={(value) => patchEditField('weightClass', value)}
              maxLength={30}
            />
            <AppInput
              label="Balance point"
              value={editFields.balancePoint}
              onChangeText={(value) => patchEditField('balancePoint', value)}
              maxLength={50}
            />
            <AppInput
              label="Grip size"
              value={editFields.gripSize}
              onChangeText={(value) => patchEditField('gripSize', value)}
              maxLength={30}
            />
            <AppInput
              label="Preferred use"
              value={editFields.preferredUse}
              onChangeText={(value) => patchEditField('preferredUse', value)}
              maxLength={120}
            />
            <AppInput
              label="Notes"
              value={editFields.notes}
              onChangeText={(value) => patchEditField('notes', value)}
              maxLength={1000}
              multiline
              inputClassName="min-h-24"
            />
            {saveError ? (
              <HeroText className="mb-4 text-sm font-medium text-red-600">
                {saveError}
              </HeroText>
            ) : null}
            <AppButton
              label="Save passport"
              isLoading={isSaving}
              onPress={() => void saveRacket()}
            />
          </AppCard>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Current setup" title="Latest completed service">
        <AppCard variant="elevated" padding="md">
          <HeroText className="text-base font-semibold text-neutral-900">
            {currentString
              ? `${currentString.brand} ${currentString.model}`
              : racket.stringHistory[0]?.stringName ??
                'No completed service yet'}
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            {racket.currentTension > 0
              ? `Current tension: ${racket.currentTension} lbs`
              : 'Current tension will appear after the first completed service.'}
            {' • '}
            Preferred use: {racket.preferredUse}
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="History" title="Completed stringing services">
        <View className="gap-3">
          {racket.stringHistory.length === 0 ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-600">
                Completed bookings linked to this racket will appear here.
              </HeroText>
            </AppCard>
          ) : null}
          {racket.stringHistory.map((entry) => {
            const historyString = strings.find(
              (item) => item.id === entry.stringId,
            );
            const stringLabel =
              historyString
                ? `${historyString.brand} ${historyString.model}`
                : entry.stringName ?? 'Custom string setup';

            return (
              <AppCard key={entry.bookingId} variant="elevated" padding="sm">
                <HeroText className="text-sm font-semibold text-neutral-900">
                  {stringLabel}
                </HeroText>
                <HeroText className="mt-1 text-sm text-neutral-500">
                  {entry.tension > 0 ? `${entry.tension} lbs • ` : ''}
                  Serviced {formatDateTime(entry.installedAt)}
                </HeroText>
                {entry.feedback ? (
                  <View className="mt-3 rounded-[16px] bg-primary-50 px-3 py-3">
                    <HeroText className="text-sm font-semibold text-primary-700">
                      Feedback {entry.feedback.rating}/5
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-neutral-600">
                      {entry.feedback.stringFeedback ??
                        entry.feedback.serviceFeedback ??
                        'Sentiment tags recorded.'}
                    </HeroText>
                  </View>
                ) : null}
              </AppCard>
            );
          })}
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
              {averageTension > 0 ? `${averageTension} lbs` : '—'}
            </HeroText>
          </AppCard>
        </View>
      </AppSection>
    </AppScreen>
  );
}
