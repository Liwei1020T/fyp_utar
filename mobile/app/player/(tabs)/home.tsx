import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  Activity,
  ArrowRight,
  Bell,
  CalendarClock,
  ChevronRight,
  Search,
  Sparkles,
  Zap,
} from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { getBookingStatusVariant } from '../../../components/ui/theme';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { TrendingStrings } from '../../../components/player/TrendingStrings';
import { getStringById } from '../../../services/mockAppService';
import {
  useBookings,
  useCurrentUser,
} from '../../../store/appStore';
import { formatBookingStatus, formatDateLabel } from '../../../lib/formatters';
import type { Booking } from '../../../types/domain';

const quickActions = [
  {
    title: 'Get recommendation',
    route: '/player/recommend',
    icon: Zap,
    color: '#3B82F6',
    bgColor: '#EFF6FF',
  },
  {
    title: 'Book restring',
    route: '/player/bookings/new',
    icon: CalendarClock,
    color: '#D97706',
    bgColor: '#FFFBEB',
  },
  {
    title: 'Browse strings',
    route: '/player/strings',
    icon: Search,
    color: '#10B981',
    bgColor: '#ECFDF5',
  },
  {
    title: 'Track service',
    route: '/player/bookings',
    icon: Activity,
    color: '#8B5CF6',
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
      headerVariant="primary"
      compactHeader
      title={`Welcome back, ${user.name.split(' ')[0]}`}
      subtitle="Recommendations, bookings, and service updates in one place."
      headerRight={
        <Pressable
          onPress={() => router.push('/player/notifications')}
          className="h-10 w-10 items-center justify-center rounded-full border border-neutral-100 bg-white shadow-sm"
        >
          <Bell size={20} color="#64748B" strokeWidth={2} />
          <View className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full border-2 border-white bg-red-500" />
        </Pressable>
      }
    >
      <View className="mt-1">
        <AppCard variant="dark" className="overflow-hidden rounded-[30px]" padding="md">
          <View className="flex-row items-start justify-between gap-3">
            <View className="flex-1">
              <AppChip
                label="Smart advisor"
                variant="secondary"
                className="self-start opacity-95"
              />
              <HeroText className="mt-3 text-[25px] font-bold leading-[30px] tracking-[-0.03em] text-white">
                Find your ideal setup
              </HeroText>
              <HeroText className="mt-1.5 text-[13px] leading-[19px] text-blue-100/85">
                Get a string and tension suggestion based on how you play.
              </HeroText>
            </View>
            <View className="mt-0.5 h-10 w-10 items-center justify-center rounded-2xl bg-white/10">
              <Sparkles size={18} color="white" strokeWidth={1.9} />
            </View>
          </View>

          <View className="mt-4 flex-row gap-2.5">
            <View className="flex-1 rounded-[18px] border border-white/10 bg-white/5 px-3 py-2.5">
              <HeroText className="text-[10px] font-semibold uppercase tracking-[0.18em] text-blue-200/70">
                Tension
              </HeroText>
              <HeroText className="mt-1 text-[17px] font-bold tracking-[-0.02em] text-white">
                {user.preferredTension} lbs
              </HeroText>
            </View>
            <View className="flex-1 rounded-[18px] border border-white/10 bg-white/5 px-3 py-2.5">
              <HeroText className="text-[10px] font-semibold uppercase tracking-[0.18em] text-blue-200/70">
                Bookings
              </HeroText>
              <HeroText className="mt-1 text-[17px] font-bold tracking-[-0.02em] text-white">
                {playerBookings.length} logged
              </HeroText>
            </View>
          </View>

          <AppButton
            label="Generate Recommendation"
            variant="secondary"
            size="md"
            className="mt-4 w-full rounded-[18px]"
            trailingIcon={<ChevronRight size={18} color="#78350F" strokeWidth={2.5} />}
            onPress={() => router.push('/player/recommend')}
          />
        </AppCard>
      </View>

      <AppSection
        title="Trending Strings"
        subtitle="Popular setups players are browsing this week."
        className="mt-5"
        rightAction={
          <Pressable onPress={() => router.push('/player/strings')}>
            <HeroText className="text-[13px] font-semibold text-primary-700">
              See all
            </HeroText>
          </Pressable>
        }
      >
        <TrendingStrings />
      </AppSection>

      <AppSection
        title="Quick Actions"
        subtitle="Jump into the tasks you use most."
        className="mt-5"
        variant="compact"
      >
        <View className="flex-row flex-wrap gap-3">
          {quickActions.map((action) => {
            const Icon = action.icon;

            return (
              <Pressable
                key={action.title}
                onPress={() => router.push(action.route as never)}
                className="w-[48%] active:opacity-70"
              >
                <AppCard
                  padding="sm"
                  className="rounded-[26px] border border-neutral-100 bg-white shadow-sm"
                  contentClassName="h-[112px] justify-between"
                >
                  <View
                    style={{ backgroundColor: action.bgColor }}
                    className="h-11 w-11 items-center justify-center rounded-[16px]"
                  >
                    <Icon size={21} color={action.color} strokeWidth={2.15} />
                  </View>
                  <HeroText
                    className="text-[14px] font-semibold leading-[18px] tracking-[-0.02em] text-neutral-900"
                    numberOfLines={2}
                  >
                    {action.title}
                  </HeroText>
                </AppCard>
              </Pressable>
            );
          })}
        </View>
      </AppSection>

      {latestBooking && latestString ? (
        <AppSection
          title="Latest Booking"
          subtitle="Your current restring progress at a glance."
          className="mt-5"
          variant="compact"
        >
          <AppCard variant="elevated" padding="md" className="rounded-[30px] border border-neutral-100">
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1 flex-row items-start gap-3">
                <View className="h-11 w-11 items-center justify-center rounded-full border border-blue-100 bg-blue-50">
                  <Activity size={20} color="#3B82F6" />
                </View>
                <View className="min-w-0 flex-1">
                  <HeroText className="text-[15px] font-semibold leading-[20px] tracking-[-0.02em] text-neutral-950">
                    {latestBooking.racketBrand} {latestBooking.racketModel}
                  </HeroText>
                  <HeroText className="mt-1 text-[12px] font-medium leading-[17px] text-neutral-500">
                    {latestString.model} • {latestString.brand} • {latestBooking.requestedTension} lbs
                  </HeroText>
                </View>
              </View>
              <AppChip
                label={formatBookingStatus(latestBooking.status)}
                variant={getBookingStatusVariant(latestBooking.status)}
                className="rounded-full"
              />
            </View>

            <View className="my-4 h-px w-full bg-neutral-100" />

            <View className="flex-row gap-3">
              <View className="flex-1 rounded-[18px] bg-[#F7FAFD] px-3 py-2.5">
                <HeroText className="text-[10px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
                  {latestBooking.status === 'ready_for_collection' ? 'Pickup by' : 'Expected ready'}
                </HeroText>
                <HeroText className="mt-1 text-[13px] font-semibold text-neutral-900">
                  {formatDateLabel(latestBooking.dropOffDate)}
                </HeroText>
              </View>
              <View className="flex-1 rounded-[18px] bg-[#F7FAFD] px-3 py-2.5">
                <HeroText className="text-[10px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
                  Price status
                </HeroText>
                <HeroText className="mt-1 text-[13px] font-semibold text-primary-700">
                  {getBookingPriceLabel(latestBooking)}
                </HeroText>
              </View>
            </View>

            <View className="mt-4 rounded-[18px] border border-[#DCE9F8] bg-[#F2F8FF] px-3.5 py-3">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                Next step
              </HeroText>
              <HeroText className="mt-1 text-[13px] leading-[18px] text-neutral-800">
                {getNextBookingStep(latestBooking.status, latestBooking.dropOffDate)}
              </HeroText>
            </View>

            <AppButton
              label="Open Booking"
              variant="outline"
              size="md"
              className="mt-4 w-full rounded-[18px] border-neutral-900"
              textClassName="text-neutral-900"
              trailingIcon={<ArrowRight size={16} color="#171717" />}
              onPress={() => router.push(`/player/bookings/${latestBooking.id}`)}
            />
          </AppCard>
        </AppSection>
      ) : null}
    </AppScreen>
  );
}

function getNextBookingStep(status: Booking['status'], dropOffDate: string) {
  switch (status) {
    case 'pending':
    case 'pending_payment':
      return 'Next: Confirm your booking details and finalise the quote at the shop.';
    case 'confirmed':
    case 'awaiting_dropoff':
      return `Next: Drop off on ${dropOffDate}.`;
    case 'in_progress':
      return 'Next: Waiting for stringing completion.';
    case 'ready_for_collection':
      return 'Next: Ready for collection.';
    case 'completed':
      return 'Next: Review your setup and book your next restring when needed.';
    case 'cancelled':
      return 'Next: Start a new booking when you are ready.';
    default:
      return 'Next: Check booking details for the latest service update.';
  }
}

function getBookingPriceLabel(booking: Booking) {
  if (booking.paymentStatus === 'paid' && booking.totalAmount > 0) {
    return 'Paid at shop';
  }

  if (booking.totalAmount > 0) {
    return 'Vendor quote';
  }

  if (booking.status === 'pending' || booking.status === 'pending_payment') {
    return 'Price pending';
  }

  return 'Quoted at shop';
}
