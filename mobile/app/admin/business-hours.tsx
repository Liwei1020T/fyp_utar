import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Plus } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { AppSelect } from '../../components/ui/AppSelect';
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

const MONTH_OPTIONS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
].map((label, index) => ({ id: String(index + 1), label }));

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = [CURRENT_YEAR, CURRENT_YEAR + 1, CURRENT_YEAR + 2].map((year) => ({
  id: String(year),
  label: String(year),
}));

function formatClosedDate(year: number, month: number, day: number) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function daysInMonth(year: number, month: number) {
  return new Date(year, month, 0).getDate();
}

function todayDateValue() {
  const today = new Date();
  return formatClosedDate(today.getFullYear(), today.getMonth() + 1, today.getDate());
}

function minimumClosedDay(year: number, month: number) {
  const today = new Date();
  return year === today.getFullYear() && month === today.getMonth() + 1
    ? today.getDate()
    : 1;
}

function closedMonthOptions(year: number) {
  const today = new Date();
  return MONTH_OPTIONS.filter(
    (_, index) => year > today.getFullYear() || index + 1 >= today.getMonth() + 1,
  );
}

function closedDayOptions(year: number, month: number) {
  const minimumDay = minimumClosedDay(year, month);
  return Array.from({ length: daysInMonth(year, month) }, (_, index) => index + 1)
    .filter((day) => day >= minimumDay)
    .map((day) => ({ id: String(day), label: String(day) }));
}

function normalizeClosedDates(values: string[]) {
  const today = todayDateValue();
  return values.filter((value) => value >= today).sort();
}

function clampClosedDay(year: number, month: number, day: number) {
  return Math.min(
    Math.max(day, minimumClosedDay(year, month)),
    daysInMonth(year, month),
  );
}

export default function AdminBusinessHoursScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const businessHours = useBusinessHoursState();
  const updateBusinessHours = useAppStore((state) => state.updateBusinessHours);
  const [localHours, setLocalHours] = useState<BusinessHours | null>(null);
  const [closedDates, setClosedDates] = useState<string[]>([]);
  const [closedDateYear, setClosedDateYear] = useState(CURRENT_YEAR);
  const [closedDateMonth, setClosedDateMonth] = useState(new Date().getMonth() + 1);
  const [closedDateDay, setClosedDateDay] = useState(new Date().getDate());
  const [closedDateError, setClosedDateError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);

  const hours = localHours ?? businessHours.find((item) => item.adminId === user?.id);

  useEffect(() => {
    const existing = businessHours.find((item) => item.adminId === user?.id);
    if (existing && !localHours) {
      const futureClosedDates = normalizeClosedDates(existing.specialClosedDates);
      setLocalHours({ ...existing, specialClosedDates: futureClosedDates });
      setClosedDates(futureClosedDates);
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
        const futureClosedDates = normalizeClosedDates(mapped.specialClosedDates);
        const normalized = { ...mapped, specialClosedDates: futureClosedDates };
        updateBusinessHours(user.id, normalized);
        setLocalHours(normalized);
        setClosedDates(futureClosedDates);
        setSaveSuccessMessage(null);
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
    setSaveSuccessMessage(null);
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

  const addClosedDate = () => {
    const dateValue = formatClosedDate(closedDateYear, closedDateMonth, closedDateDay);
    if (dateValue < todayDateValue()) {
      setClosedDateError('Closed dates must be today or later.');
      return;
    }
    if (closedDates.includes(dateValue)) {
      setClosedDateError('This date has already been added.');
      return;
    }
    setSaveSuccessMessage(null);
    setClosedDateError(null);
    setClosedDates((current) => [...current, dateValue].sort());
  };

  const removeClosedDate = (dateValue: string) => {
    setSaveSuccessMessage(null);
    setClosedDateError(null);
    setClosedDates((current) => current.filter((value) => value !== dateValue));
  };

  const saveBusinessHours = async () => {
    if (!localHours || !user || user.role !== 'admin') {
      return;
    }
    if (!token) {
      setError('Your admin session expired. Sign in again before saving.');
      return;
    }
    const nextHours = {
      ...localHours,
      specialClosedDates: closedDates,
    };
    setError(null);
    setIsSaving(true);
    try {
      const response = await backendApi.updateBusinessHours(
        token,
        mapBusinessHoursToBackendPayload(nextHours),
      );
      const mapped = mapBackendBusinessHoursToBusinessHours(response, user.id);
      updateBusinessHours(user.id, mapped);
      setLocalHours(mapped);
      setClosedDates(mapped.specialClosedDates);
      setSaveSuccessMessage('Business hours saved. Player booking slots now use the updated schedule.');
    } catch (saveError) {
      setSaveSuccessMessage(null);
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
      headerVariant="secondary"
      title="Business hours"
      subtitle="Backend-connected store schedule used to generate player booking slots."
      showBackButton
      onBackPress={() => router.back()}
      footer={
        <View className="border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          <AppButton
            label="Save business hours"
            size="lg"
            onPress={saveBusinessHours}
            isLoading={isSaving}
          />
        </View>
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

      <AppSection eyebrow="Exceptions" title="Temporary closures">
        <View className="gap-3">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Add dates when the shop will not accept bookings, such as public holidays or maintenance days.
          </HeroText>
          <HeroText className="text-sm text-neutral-500">
            Only today or future dates can be added.
          </HeroText>
          <View className="flex-row gap-2">
            <AppSelect
              label="Month"
              value={String(closedDateMonth)}
              options={closedMonthOptions(closedDateYear)}
              onChange={(value) => {
                const nextMonth = Number(value);
                setClosedDateMonth(nextMonth);
                setClosedDateDay((current) =>
                  clampClosedDay(closedDateYear, nextMonth, current),
                );
              }}
              className="flex-[1.5]"
            />
            <AppSelect
              label="Day"
              value={String(closedDateDay)}
              options={closedDayOptions(closedDateYear, closedDateMonth)}
              onChange={(value) => setClosedDateDay(Number(value))}
              className="flex-1"
            />
            <AppSelect
              label="Year"
              value={String(closedDateYear)}
              options={YEAR_OPTIONS}
              onChange={(value) => {
                const nextYear = Number(value);
                const nextMonthOptions = closedMonthOptions(nextYear);
                const nextMonth = nextMonthOptions.some(
                  (option) => Number(option.id) === closedDateMonth,
                )
                  ? closedDateMonth
                  : Number(nextMonthOptions[0]?.id ?? closedDateMonth);
                setClosedDateYear(nextYear);
                setClosedDateMonth(nextMonth);
                setClosedDateDay((current) =>
                  clampClosedDay(nextYear, nextMonth, current),
                );
              }}
              className="flex-[1.2]"
            />
          </View>
          <AppButton
            label="Add closed date"
            size="sm"
            variant="outline"
            leadingIcon={<Plus size={16} color="#2F64B6" />}
            onPress={addClosedDate}
            className="self-start"
          />
          {closedDateError ? (
            <HeroText accessibilityLiveRegion="polite" className="text-sm font-semibold text-danger-600">
              {closedDateError}
            </HeroText>
          ) : null}
          {closedDates.length > 0 ? (
            <View className="flex-row flex-wrap gap-2">
              {closedDates.map((dateValue) => (
                <AppChip
                  key={dateValue}
                  label={`${dateValue} ×`}
                  variant="primary"
                  onPress={() => removeClosedDate(dateValue)}
                  accessibilityLabel={`Remove temporary closure ${dateValue}`}
                />
              ))}
            </View>
          ) : (
            <HeroText className="text-sm text-neutral-500">No temporary closures added.</HeroText>
          )}
        </View>
      </AppSection>

      {saveSuccessMessage ? (
        <View className="mt-4 rounded-[20px] border border-success-100 bg-success-50 px-4 py-3">
          <HeroText className="text-[13px] font-semibold text-success-700">
            Business hours saved
          </HeroText>
          <HeroText className="mt-1 text-[12px] leading-5 text-success-700">
            {saveSuccessMessage}
          </HeroText>
        </View>
      ) : null}

      {error ? (
        <HeroText className="mt-4 text-sm font-semibold text-danger-600">
          {error}
        </HeroText>
      ) : null}
    </AppScreen>
  );
}
