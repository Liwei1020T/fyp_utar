import React from 'react';
import { Pressable, View, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { 
  ArrowRight, 
  CalendarClock, 
  Sparkles, 
  TimerReset, 
  Zap, 
  Search, 
  Activity, 
  Bell,
  ChevronRight
} from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { TrendingStrings } from '../../../components/player/TrendingStrings';
import {
  useBookings,
  useCurrentUser,
} from '../../../store/appStore';
import { getStringById } from '../../../services/mockAppService';
import { formatCurrency } from '../../../lib/formatters';

const quickActions = [
  {
    title: 'Get Recommendation',
    route: '/player/recommend',
    icon: Zap,
    color: '#3B82F6', // Soft blue
    bgColor: '#EFF6FF',
  },
  {
    title: 'Book Restring',
    route: '/player/bookings/new',
    icon: CalendarClock,
    color: '#D97706', // Gold/Amber
    bgColor: '#FFFBEB',
  },
  {
    title: 'Browse Strings',
    route: '/player/strings',
    icon: Search,
    color: '#10B981', // Emerald
    bgColor: '#ECFDF5',
  },
  {
    title: 'Track Service',
    route: '/player/bookings',
    icon: Activity,
    color: '#8B5CF6', // Violet
    bgColor: '#F5F3FF',
  },
] as const;

export default function PlayerHomeScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerBookings = bookings.filter((item) => item.playerId === user.id);
  const latestBooking = playerBookings[0];
  const latestString = latestBooking ? getStringById(latestBooking.stringId) : undefined;

  return (
    <AppScreen
      tone="player"
      headerLeft={
        <View className="flex-row items-center gap-3">
          <View className="h-10 w-10 items-center justify-center rounded-full bg-primary-100 ring-2 ring-white shadow-sm">
            <HeroText className="text-base font-bold text-primary-700">{user.avatarLabel}</HeroText>
          </View>
          <View>
            <HeroText className="text-xs font-medium text-neutral-400">Welcome back,</HeroText>
            <HeroText className="text-base font-bold tracking-tight text-neutral-900">
              {user.name}
            </HeroText>
          </View>
        </View>
      }
      headerRight={
        <Pressable 
          onPress={() => router.push('/player/notifications')}
          className="h-10 w-10 items-center justify-center rounded-full bg-white shadow-sm border border-neutral-100"
        >
          <Bell size={20} color="#64748B" strokeWidth={2} />
          <View className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-red-500 border-2 border-white" />
        </Pressable>
      }
    >
      {/* 2. Primary Recommendation Hero Card */}
      <View className="px-5 mt-2">
        <AppCard variant="dark" className="rounded-[32px] overflow-hidden" padding="lg">
          <View className="flex-row items-start justify-between">
            <View className="flex-1 pr-4">
              <AppChip 
                label="SMART ADVISOR" 
                variant="secondary" 
                className="self-start opacity-90" 
              />
              <HeroText className="mt-4 text-2xl font-bold leading-tight tracking-tight text-white">
                Find your perfect match
              </HeroText>
              <HeroText className="mt-2 text-sm leading-relaxed text-blue-100/80">
                Personalized string & tension guide based on your playstyle.
              </HeroText>
            </View>
            <View className="h-12 w-12 items-center justify-center rounded-2xl bg-white/10 backdrop-blur-md">
              <Sparkles size={24} color="white" strokeWidth={1.5} />
            </View>
          </View>

          <View className="mt-6 flex-row gap-2">
            <View className="flex-1 rounded-2xl bg-white/5 border border-white/10 p-3">
              <HeroText className="text-[10px] font-bold uppercase tracking-widest text-blue-200/60">
                Tension
              </HeroText>
              <HeroText className="mt-1 text-lg font-bold text-white">
                {user.preferredTension} lbs
              </HeroText>
            </View>
            <View className="flex-1 rounded-2xl bg-white/5 border border-white/10 p-3">
              <HeroText className="text-[10px] font-bold uppercase tracking-widest text-blue-200/60">
                Play Count
              </HeroText>
              <HeroText className="mt-1 text-lg font-bold text-white">
                {playerBookings.length} bookings
              </HeroText>
            </View>
          </View>

          <AppButton
            label="Generate Recommendation"
            variant="secondary"
            size="md"
            className="mt-6 w-full rounded-2xl"
            trailingIcon={<ChevronRight size={18} color="#78350F" strokeWidth={2.5} />}
            onPress={() => router.push('/player/recommend')}
          />
        </AppCard>
      </View>

      {/* 3. Trending Strings */}
      <AppSection 
        title="Trending Strings" 
        className="mt-6"
        headerClassName="px-5"
        titleClassName="text-lg font-bold text-neutral-900"
      >
        <TrendingStrings />
      </AppSection>

      {/* 4. Quick Actions */}
      <AppSection 
        title="Quick Actions" 
        className="mt-6"
        headerClassName="px-5"
        titleClassName="text-lg font-bold text-neutral-900"
      >
        <View className="px-5 flex-row flex-wrap gap-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Pressable 
                key={action.title} 
                onPress={() => router.push(action.route as any)}
                className="w-[48%] active:opacity-70"
              >
                <AppCard padding="md" className="rounded-3xl border border-neutral-100 bg-white shadow-sm">
                  <View 
                    style={{ backgroundColor: action.bgColor }} 
                    className="h-12 w-12 items-center justify-center rounded-2xl mb-3"
                  >
                    <Icon size={24} color={action.color} strokeWidth={2} />
                  </View>
                  <HeroText className="text-sm font-bold text-neutral-900 leading-tight">
                    {action.title}
                  </HeroText>
                </AppCard>
              </Pressable>
            );
          })}
        </View>
      </AppSection>

      {/* 5. Latest Booking */}
      {latestBooking && latestString ? (
        <AppSection
          title="Latest Booking"
          className="mt-6 mb-10"
          headerClassName="px-5"
          titleClassName="text-lg font-bold text-neutral-900"
        >
          <View className="px-5">
            <AppCard variant="elevated" padding="lg" className="rounded-[32px] border border-neutral-100">
              <View className="flex-row items-center justify-between mb-4">
                <View className="flex-row items-center gap-3">
                  <View className="h-10 w-10 items-center justify-center rounded-full bg-blue-50 border border-blue-100">
                    <Activity size={20} color="#3B82F6" />
                  </View>
                  <View>
                    <HeroText className="text-sm font-bold text-neutral-900">
                      {latestBooking.racketBrand} {latestBooking.racketModel}
                    </HeroText>
                    <HeroText className="text-[11px] font-medium text-neutral-500">
                      {latestString.brand} {latestString.model} • {latestBooking.requestedTension}lbs
                    </HeroText>
                  </View>
                </View>
                <AppChip 
                  label={latestBooking.status.replace(/_/g, ' ')} 
                  variant="primary" 
                  className="rounded-full" 
                />
              </View>

              <View className="h-px bg-neutral-100 w-full mb-4" />

              <View className="flex-row justify-between items-center mb-6">
                <View>
                  <HeroText className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">
                    Drop-off Date
                  </HeroText>
                  <HeroText className="mt-1 text-sm font-semibold text-neutral-800">
                    {latestBooking.dropOffDate}
                  </HeroText>
                </View>
                <View className="items-end">
                  <HeroText className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">
                    Total Amount
                  </HeroText>
                  <HeroText className="mt-1 text-sm font-bold text-primary-700">
                    {formatCurrency(latestBooking.totalAmount)}
                  </HeroText>
                </View>
              </View>

              <AppButton
                label="View Booking Details"
                variant="outline"
                size="md"
                className="w-full rounded-2xl border-neutral-900"
                textClassName="text-neutral-900"
                trailingIcon={<ArrowRight size={16} color="#171717" />}
                onPress={() => router.push(`/player/bookings/${latestBooking.id}`)}
              />
            </AppCard>
          </View>
        </AppSection>
      ) : null}
    </AppScreen>
  );
}
