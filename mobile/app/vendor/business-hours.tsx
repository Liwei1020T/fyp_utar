import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { useAppStore, useBusinessHoursState, useCurrentUser } from '../../store/appStore';
import { MOCK_BOOKING_SLOTS } from '../../mocks';

export default function AdminBusinessHoursScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const businessHours = useBusinessHoursState();
  const updateBusinessHours = useAppStore((state) => state.updateBusinessHours);

  if (!user || user.role !== 'admin') {
    return null;
  }

  const hours = businessHours.find((item) => item.adminId === user.id);
  const slotPreview = MOCK_BOOKING_SLOTS.filter((item) => item.adminId === user.id).slice(0, 5);

  if (!hours) {
    return null;
  }

  return (
    <AppScreen
      tone="admin"
      title="Business hours"
      subtitle="Frontend-only editing for weekday hours, break windows, slot duration, and capacity."
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
                    <HeroText className="mt-2 text-xs leading-5 text-neutral-500">
                      Break {day.breakStart ?? '-'} to {day.breakEnd ?? '-'} • {day.slotDurationMinutes} min slots • max {day.maxBookingsPerSlot} bookings per slot
                    </HeroText>
                  ) : null}
                </View>
                <AppChip
                  label={day.isOpen ? 'Open' : 'Closed'}
                  variant={day.isOpen ? 'success' : 'neutral'}
                  onPress={() =>
                    updateBusinessHours(user.id, {
                      ...hours,
                      days: hours.days.map((entry) =>
                        entry.day === day.day ? { ...entry, isOpen: !entry.isOpen } : entry
                      ),
                    })
                  }
                />
              </View>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Special dates" title="Closed dates and slot preview">
        <View className="gap-3">
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-600">
              Special closed dates: {hours.specialClosedDates.join(', ')}
            </HeroText>
          </AppCard>
          {slotPreview.map((slot) => (
            <AppCard key={slot.id} variant="elevated" padding="sm">
              <HeroText className="text-sm font-semibold text-neutral-900">
                {slot.dayLabel} {slot.date} at {slot.label}
              </HeroText>
              <HeroText className="mt-1 text-sm text-neutral-500">
                Available spots {slot.availableSpots}/{slot.capacity}
              </HeroText>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppButton label="Done" size="lg" className="mt-8" onPress={() => router.back()} />
    </AppScreen>
  );
}
