import React from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  ArrowRight,
  Boxes,
  CalendarRange,
  Clock3,
  LogOut,
  Settings2,
  Store,
  TimerReset,
  Undo2,
} from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppButton } from '../../../components/ui/AppButton';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { MetricStatCard } from '../../../components/analytics/MetricStatCard';
import { useAppStore, useBookings, useCurrentUser, useStrings } from '../../../store/appStore';

const PRIMARY_ACTIONS = [
  {
    title: 'Check-in',
    subtitle: 'Confirm player racket drop-off at the counter.',
    route: '/admin/check-in',
    icon: Undo2,
    variant: 'dark' as const,
  },
  {
    title: 'Bookings',
    subtitle: 'Update service status and monitor the queue.',
    route: '/admin/bookings',
    icon: CalendarRange,
    variant: 'outline' as const,
  },
  {
    title: 'Inventory',
    subtitle: 'Review string stock and low-stock items.',
    route: '/admin/inventory',
    icon: Boxes,
    variant: 'outline' as const,
  },
  {
    title: 'Business hours',
    subtitle: 'Adjust slots and store availability windows.',
    route: '/admin/business-hours',
    icon: Clock3,
    variant: 'outline' as const,
  },
  {
    title: 'Store settings',
    subtitle: 'Edit store profile, notes, and policies.',
    route: '/admin/settings',
    icon: Settings2,
    variant: 'outline' as const,
  },
];

export default function AdminDashboardScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const strings = useStrings();
  const logout = useAppStore((state) => state.logout);

  if (!user || user.role !== 'admin') {
    return null;
  }

  const adminBookings = bookings.filter((item) => item.adminId === user.id);
  const awaitingDropOffCount = adminBookings.filter((item) => item.status === 'awaiting_dropoff').length;
  const inProgressCount = adminBookings.filter((item) => item.status === 'in_progress').length;
  const readyForCollectionCount = adminBookings.filter(
    (item) => item.status === 'ready_for_collection',
  ).length;
  const lowStockCount = strings.filter((item) => item.availability === 'low_stock').length;

  return (
    <AppScreen
      tone="admin"
      headerVariant="primary"
      title="Admin overview"
      subtitle={`${user.businessName} counter operations.`}
      headerRight={
        <AppIconButton
          icon={<LogOut size={20} color="#EF4444" />}
          accessibilityLabel="Log out"
          onPress={() => {
            logout();
            router.replace('/auth/welcome');
          }}
        />
      }
    >
      <View className="gap-5">
        <AppSection eyebrow="Today" title="Operational snapshot" variant="compact">
          <View className="flex-row flex-wrap gap-3">
            <MetricStatCard
              title="Today bookings"
              value={String(adminBookings.length)}
              icon={<CalendarRange size={20} color="#2F64B6" />}
            />
            <MetricStatCard
              title="Awaiting drop-off"
              value={String(awaitingDropOffCount)}
              icon={<Undo2 size={20} color="#B67D21" />}
              accentClassName="bg-warning-50"
            />
            <MetricStatCard
              title="In progress"
              value={String(inProgressCount)}
              icon={<TimerReset size={20} color="#22766D" />}
              accentClassName="bg-[#E4F2F0]"
            />
            <MetricStatCard
              title="Ready pickup"
              value={String(readyForCollectionCount)}
              icon={<Store size={20} color="#6550B8" />}
              accentClassName="bg-[#ECE7FA]"
            />
          </View>
        </AppSection>

        <AppSection
          eyebrow="Primary actions"
          title="Start with the counter flow"
          subtitle="Move the most common shop tasks to the top."
          rightAction={
            <AppChip
              label={`${awaitingDropOffCount} awaiting`}
              variant="warning"
              className="mt-1"
            />
          }
          variant="compact"
        >
          <View className="gap-3">
            {PRIMARY_ACTIONS.map((action) => {
              const Icon = action.icon;

              return (
                <AppCard
                  key={action.title}
                  variant={action.title === 'Check-in' ? 'highlighted' : 'elevated'}
                  padding="md"
                  onPress={() => router.push(action.route as never)}
                >
                  <View className="flex-row items-center justify-between gap-4">
                    <View className="flex-row items-center gap-3 flex-1">
                      <View
                        className={
                          action.title === 'Check-in'
                            ? 'h-12 w-12 items-center justify-center rounded-[18px] bg-primary-600'
                            : 'h-12 w-12 items-center justify-center rounded-[18px] bg-primary-50'
                        }
                      >
                        <Icon
                          size={20}
                          color={action.title === 'Check-in' ? '#FFFFFF' : '#2F64B6'}
                        />
                      </View>
                      <View className="flex-1">
                        <HeroText className="text-[16px] font-semibold tracking-tight text-neutral-950">
                          {action.title}
                        </HeroText>
                        <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
                          {action.subtitle}
                        </HeroText>
                      </View>
                    </View>
                    <ArrowRight size={16} color="#94A3B8" />
                  </View>
                </AppCard>
              );
            })}
          </View>
        </AppSection>

        <AppSection eyebrow="Highlights" title="What needs attention?" className="mb-12" variant="compact">
          <View className="gap-3">
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center gap-3">
                <Undo2 size={18} color="#2F64B6" />
                <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                  {awaitingDropOffCount} booking{awaitingDropOffCount === 1 ? '' : 's'} waiting for racket drop-off.
                </HeroText>
              </View>
            </AppCard>
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center gap-3">
                <Clock3 size={18} color="#22766D" />
                <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                  {inProgressCount} job{inProgressCount === 1 ? '' : 's'} currently on the stringing bench.
                </HeroText>
              </View>
            </AppCard>
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center gap-3">
                <Boxes size={18} color="#C98A2E" />
                <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                  {lowStockCount} string SKU{lowStockCount === 1 ? '' : 's'} flagged for stock review.
                </HeroText>
              </View>
            </AppCard>
          </View>
        </AppSection>
      </View>
    </AppScreen>
  );
}
