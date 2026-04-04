import React from 'react';
import { View } from 'react-native';
import { BarChart3, Clock3, Flame, Gauge } from 'lucide-react-native';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { MetricStatCard } from '../../../components/analytics/MetricStatCard';
import { AppCard } from '../../../components/ui/AppCard';
import { HeroText } from '../../../components/ui/heroui';
import { useCurrentUser } from '../../../store/appStore';
import { formatCurrency } from '../../../lib/formatters';
import { getAdminAnalytics, getStringById } from '../../../services/mockAppService';

export default function AdminAnalyticsScreen() {
  const user = useCurrentUser();

  if (!user || user.role !== 'admin') {
    return null;
  }

  const analytics = getAdminAnalytics(user.id);

  return (
    <AppScreen tone="admin" title="Admin analytics" subtitle="Admin operations analytics UI for trends, busy slots, popular strings, payments, and workload." >
      <AppSection eyebrow="Metrics" title="Shop performance">
        <View className="flex-row flex-wrap gap-3">
          <MetricStatCard title="Weekly bookings" value={String(analytics?.weeklyBookings ?? 0)} icon={<BarChart3 size={20} color="#2F64B6" />} />
          <MetricStatCard title="Pending payment" value={String(analytics?.pendingPaymentCount ?? 0)} icon={<Clock3 size={20} color="#22766D" />} accentClassName="bg-[#E4F2F0]" />
          <MetricStatCard title="Ready pickup" value={String(analytics?.readyForCollectionCount ?? 0)} icon={<Gauge size={20} color="#6550B8" />} accentClassName="bg-[#ECE7FA]" />
          <MetricStatCard title="Revenue" value={formatCurrency(analytics?.todayRevenue ?? 0)} icon={<BarChart3 size={20} color="#2F64B6" />} />
        </View>
      </AppSection>

      <AppSection eyebrow="Demand" title="Popular strings">
        <View className="gap-3">
          {analytics?.popularStringIds.map((stringId) => (
            <AppCard key={stringId} variant="elevated" padding="sm">
              <HeroText className="text-sm font-semibold text-neutral-900">
                {getStringById(stringId)?.brand} {getStringById(stringId)?.model}
              </HeroText>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Busy slots" title="When the desk gets crowded">
        <View className="gap-3">
          {analytics?.busySlots.map((slot) => (
            <AppCard key={slot} variant="highlighted" padding="sm">
              <View className="flex-row items-center gap-3">
                <Flame size={18} color="#C98A2E" />
                <HeroText className="text-sm font-semibold text-neutral-900">{slot}</HeroText>
              </View>
            </AppCard>
          ))}
        </View>
      </AppSection>
    </AppScreen>
  );
}
