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
import { useAppStore, useBookings, useCurrentUser } from '../../../store/appStore';
import { formatCurrency } from '../../../lib/formatters';
import { getAdminAnalytics } from '../../../services/mockAppService';

export default function AdminDashboardScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const logout = useAppStore((state) => state.logout);

  if (!user || user.role !== 'admin') {
    return null;
  }

  const adminBookings = bookings.filter((item) => item.adminId === user.id);
  const analytics = getAdminAnalytics(user.id);

  return (
    <AppScreen
      tone="admin"
      headerLeft={
        <View className="flex-row items-center gap-3">
          <View className="h-11 w-11 items-center justify-center rounded-[18px] bg-[#E4F2F0]">
            <Store size={20} color="#22766D" />
          </View>
          <View>
            <HeroText className="text-xs text-neutral-500">Admin workspace</HeroText>
            <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
              {user.businessName}
            </HeroText>
          </View>
        </View>
      }
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
          Keep today&apos;s queue clear and the counter team aligned.
        </HeroText>
        <HeroText className="mt-2 text-sm leading-6 text-primary-100">
          Focus the dashboard on workload, outstanding payments, and the next operational action.
        </HeroText>
      </AppCard>

      <AppSection eyebrow="Today" title="Operational snapshot">
        <View className="flex-row flex-wrap gap-3">
          <MetricStatCard title="Today bookings" value={String(adminBookings.length)} icon={<CalendarRange size={20} color="#2F64B6" />} />
          <MetricStatCard title="Pending payment" value={String(analytics?.pendingPaymentCount ?? 0)} icon={<Clock3 size={20} color="#C98A2E" />} accentClassName="bg-secondary-50" />
          <MetricStatCard title="Awaiting drop-off" value={String(analytics?.awaitingDropoffCount ?? 0)} icon={<QrCode size={20} color="#2F64B6" />} />
          <MetricStatCard title="In progress" value={String(analytics?.inProgressCount ?? 0)} icon={<TimerReset size={20} color="#22766D" />} accentClassName="bg-[#E4F2F0]" />
          <MetricStatCard title="Ready pickup" value={String(analytics?.readyForCollectionCount ?? 0)} icon={<Store size={20} color="#6550B8" />} accentClassName="bg-[#ECE7FA]" />
          <MetricStatCard title="Revenue" value={formatCurrency(analytics?.todayRevenue ?? 0)} subtitle="mock today" icon={<CalendarRange size={20} color="#2F64B6" />} />
        </View>
      </AppSection>

      <AppSection eyebrow="Quick actions" title="Jump into the queue">
        <View className="gap-3">
          {[
            { title: 'Service queue', subtitle: 'See what is waiting on the bench.', route: '/admin/service-queue' },
            { title: 'Check-in flow', subtitle: 'Handle counter arrivals and scan-ins.', route: '/admin/check-in' },
            { title: 'Business hours', subtitle: 'Adjust opening windows for the shop.', route: '/admin/business-hours' },
            { title: 'Payments monitor', subtitle: 'Review unpaid or failed payment states.', route: '/admin/payments' },
            { title: 'Store settings', subtitle: 'Tune shop-facing defaults and notes.', route: '/admin/settings' },
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
                {analytics?.lowStockCount ?? 0} strings are flagged as low stock and should be reviewed from inventory.
              </HeroText>
            </View>
          </AppCard>
        </View>
      </AppSection>
    </AppScreen>
  );
}
