import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import {
  useAppStore,
  useBackendAccessToken,
  useBusinessHoursState,
  useCurrentUser,
} from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import {
  mapBackendBusinessHoursToBusinessHours,
  mapBusinessHoursToBackendPayload,
} from '../../services/backendMappers';
import type { BusinessHours } from '../../types/domain';

export default function AdminBusinessHoursScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const businessHours = useBusinessHoursState();
  const updateBusinessHours = useAppStore((state) => state.updateBusinessHours);
  const [localHours, setLocalHours] = useState<BusinessHours | null>(null);
  const [closedDatesText, setClosedDatesText] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hours = localHours ?? businessHours.find((item) => item.adminId === user?.id);

  useEffect(() => {
    const existing = businessHours.find((item) => item.adminId === user?.id);
    if (existing && !localHours) {
      setLocalHours(existing);
      setClosedDatesText(existing.specialClosedDates.join(', '));
    }
  }, [businessHours, localHours, user?.id]);

  useEffect(() => {
    if (!token || !user || user.role !== 'admin') {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      setError(null);
      try {
        const response = await backendApi.fetchBusinessHours(token);
        if (cancelled) {
          return;
        }
        const mapped = mapBackendBusinessHoursToBusinessHours(response, user.id);
        updateBusinessHours(user.id, mapped);
        setLocalHours(mapped);
        setClosedDatesText(mapped.specialClosedDates.join(', '));
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof BackendApiError
              ? loadError.message
              : 'Failed to load business hours.',
          );
        }
      }
    };

    void hydrate();

    return () => {
      cancelled = true;
    };
  }, [token, updateBusinessHours, user]);

  const patchDay = (
    dayName: BusinessHours['days'][number]['day'],
    patch: Partial<BusinessHours['days'][number]>,
  ) => {
    setLocalHours((current) =>
      current
        ? {
            ...current,
            days: current.days.map((day) =>
              day.day === dayName ? { ...day, ...patch } : day,
            ),
          }
        : current,
    );
  };

  const saveBusinessHours = async () => {
    if (!localHours || !user || user.role !== 'admin') {
      return;
    }
    const nextHours = {
      ...localHours,
      specialClosedDates: closedDatesText
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
    };
    setError(null);
    setIsSaving(true);
    try {
      if (token) {
        const response = await backendApi.updateBusinessHours(
          token,
          mapBusinessHoursToBackendPayload(nextHours),
        );
        const mapped = mapBackendBusinessHoursToBusinessHours(response, user.id);
        updateBusinessHours(user.id, mapped);
        setLocalHours(mapped);
        setClosedDatesText(mapped.specialClosedDates.join(', '));
      } else {
        updateBusinessHours(user.id, nextHours);
      }
    } catch (saveError) {
      setError(
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to save business hours.',
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (!user || user.role !== 'admin') {
    return null;
  }

  if (!hours) {
    return (
      <AppScreen tone="admin" title="Business hours">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Loading store business hours...
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  return (
    <AppScreen
      tone="admin"
      title="Business hours"
      subtitle="Backend-connected store schedule used to generate player booking slots."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      <AppSection eyebrow="Schedule" title="Weekly operating pattern">
        <View className="gap-3">
          {hours.days.map((day) => (
            <AppCard key={day.day} variant="elevated" padding="md">
              <View className="flex-row items-center justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-base font-semibold text-neutral-900">{day.day}</HeroText>
                  <HeroText className="mt-1 text-sm text-neutral-500">
                    {day.isOpen ? `${day.openTime} - ${day.closeTime}` : 'Closed'}
                  </HeroText>
                  {day.isOpen ? (
                    <View className="mt-3 gap-2">
                      <View className="flex-row gap-2">
                        <AppInput className="flex-1" label="Open" value={day.openTime} onChangeText={(value) => patchDay(day.day, { openTime: value })} />
                        <AppInput className="flex-1" label="Close" value={day.closeTime} onChangeText={(value) => patchDay(day.day, { closeTime: value })} />
                      </View>
                      <View className="flex-row gap-2">
                        <AppInput className="flex-1" label="Break start" value={day.breakStart ?? ''} onChangeText={(value) => patchDay(day.day, { breakStart: value || undefined })} />
                        <AppInput className="flex-1" label="Break end" value={day.breakEnd ?? ''} onChangeText={(value) => patchDay(day.day, { breakEnd: value || undefined })} />
                      </View>
                      <View className="flex-row gap-2">
                        <AppInput className="flex-1" label="Slot minutes" keyboardType="numeric" value={String(day.slotDurationMinutes)} onChangeText={(value) => patchDay(day.day, { slotDurationMinutes: Number(value) || day.slotDurationMinutes })} />
                        <AppInput className="flex-1" label="Capacity" keyboardType="numeric" value={String(day.maxBookingsPerSlot)} onChangeText={(value) => patchDay(day.day, { maxBookingsPerSlot: Number(value) || day.maxBookingsPerSlot })} />
                      </View>
                    </View>
                  ) : null}
                </View>
                <AppChip
                  label={day.isOpen ? 'Open' : 'Closed'}
                  variant={day.isOpen ? 'success' : 'neutral'}
                  onPress={() => patchDay(day.day, { isOpen: !day.isOpen })}
                />
              </View>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Special dates" title="Closed dates">
        <View className="gap-3">
          <AppInput
            label="Special closed dates"
            helperText="Comma-separated YYYY-MM-DD dates."
            value={closedDatesText}
            onChangeText={setClosedDatesText}
          />
        </View>
      </AppSection>

      {error ? (
        <HeroText className="mt-4 text-sm font-semibold text-danger-600">
          {error}
        </HeroText>
      ) : null}
      <AppButton
        label="Save business hours"
        size="lg"
        className="mt-8"
        onPress={saveBusinessHours}
        isLoading={isSaving}
      />
    </AppScreen>
  );
}
