import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, CalendarRange, Clock3, LogOut, QrCode, Store, TimerReset } from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppButton } from '../../../components/ui/AppButton';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { MetricStatCard } from '../../../components/analytics/MetricStatCard';
import { useAppStore, useBookings, useCurrentUser, useStrings } from '../../../store/appStore';

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
  const lowStockCount = strings.filter((item) => item.availability === 'low_stock').length;

  return (
    <AppScreen
      tone="admin"
      headerVariant="primary"
      title="Admin overview"
      subtitle={`${user.businessName} operations at a glance.`}
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
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
          Shop operations
        </HeroText>
        <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-white">
          Keep bookings, inventory, and store scheduling aligned for the FYP1 demo.
        </HeroText>
        <HeroText className="mt-2 text-sm leading-6 text-primary-100">
          Focus the dashboard on backend-connected booking, inventory, business-hours, and store-setting actions.
        </HeroText>
      </AppCard>

      <AppSection eyebrow="Today" title="Operational snapshot">
        <View className="flex-row flex-wrap gap-3">
          <MetricStatCard title="Today bookings" value={String(adminBookings.length)} icon={<CalendarRange size={20} color="#2F64B6" />} />
          <MetricStatCard title="Awaiting drop-off" value={String(adminBookings.filter((item) => item.status === 'awaiting_dropoff').length)} icon={<QrCode size={20} color="#2F64B6" />} />
          <MetricStatCard title="In progress" value={String(adminBookings.filter((item) => item.status === 'in_progress').length)} icon={<TimerReset size={20} color="#22766D" />} accentClassName="bg-[#E4F2F0]" />
          <MetricStatCard title="Ready pickup" value={String(adminBookings.filter((item) => item.status === 'ready_for_collection').length)} icon={<Store size={20} color="#6550B8" />} accentClassName="bg-[#ECE7FA]" />
          <MetricStatCard title="Low stock" value={String(lowStockCount)} icon={<Clock3 size={20} color="#C98A2E" />} accentClassName="bg-secondary-50" />
        </View>
      </AppSection>

      <AppSection eyebrow="Quick actions" title="Manage the FYP1 flow">
        <View className="gap-3">
          {[
            { title: 'Bookings', subtitle: 'Review and update real booking status.', route: '/admin/bookings' },
            { title: 'Inventory', subtitle: 'Manage live string stock and notes.', route: '/admin/inventory' },
            { title: 'Business hours', subtitle: 'Adjust slot-generating opening windows.', route: '/admin/business-hours' },
            { title: 'Store settings', subtitle: 'Edit store contact, support, and booking policy copy.', route: '/admin/settings' },
          ].map((item) => (
            <Pressable key={item.title} onPress={() => router.push(item.route as never)}>
              <AppCard variant="elevated" padding="md">
                <View className="flex-row items-center justify-between gap-4">
                  <View className="flex-1">
                    <HeroText className="text-base font-semibold text-neutral-900">{item.title}</HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-neutral-500">{item.subtitle}</HeroText>
                  </View>
                  <ArrowRight size={16} color="#94A3B8" />
                </View>
              </AppCard>
            </Pressable>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Highlights" title="What needs attention?" className="mb-12">
        <View className="gap-3">
          <AppCard variant="subtle" padding="md">
            <View className="flex-row items-center gap-3">
              <QrCode size={18} color="#2F64B6" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                {adminBookings.filter((item) => item.status === 'awaiting_dropoff').length} bookings are waiting for counter drop-off today.
              </HeroText>
            </View>
          </AppCard>
          <AppCard variant="subtle" padding="md">
            <View className="flex-row items-center gap-3">
              <Clock3 size={18} color="#22766D" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                {lowStockCount} strings are flagged as low stock and should be reviewed from inventory.
              </HeroText>
            </View>
          </AppCard>
        </View>
      </AppSection>
    </AppScreen>
  );
}
