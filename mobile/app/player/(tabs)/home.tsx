import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  Activity,
  ArrowRight,
  Bell,
  CalendarClock,
  ChevronRight,
  MessageSquareText,
  Search,
  Sparkles,
  Zap,
} from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppMotion } from '../../../components/ui/AppMotion';
import { appChromeColors, getBookingStatusVariant } from '../../../components/ui/theme';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { TrendingStrings } from '../../../components/player/TrendingStrings';
import {
  useBookings,
  useCurrentUser,
  useNotifications,
  useStrings,
} from '../../../store/appStore';
import { formatBookingStatus, formatDateLabel } from '../../../lib/formatters';
import type { Booking } from '../../../types/domain';

const quickActions = [
  {
    title: 'Advisor',
    accessibilityLabel: 'Get recommendation',
    route: '/player/recommend',
    icon: Zap,
  },
  {
    title: 'Book service',
    accessibilityLabel: 'Book service',
    route: '/player/bookings/new',
    icon: CalendarClock,
  },
  {
    title: 'String catalog',
    accessibilityLabel: 'Open string catalog',
    route: '/player/strings',
    icon: Search,
  },
  {
    title: 'Message shop',
    accessibilityLabel: 'Message shop',
    route: '/player/chat',
    icon: MessageSquareText,
  },
] as const;

export default function PlayerHomeScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const notifications = useNotifications();
  const strings = useStrings();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerBookings = bookings.filter((item) => item.playerId === user.id);
  const activeBooking = playerBookings.find(
    (item) => !['completed', 'cancelled', 'rejected'].includes(item.status),
  );
  const hasUnreadNotifications = notifications.some(
    (item) => item.userId === user.id && !item.read,
  );
  const latestBooking = playerBookings[0];
  const primaryBooking = activeBooking ?? latestBooking;
  const latestString = primaryBooking
    ? strings.find((item) => item.id === primaryBooking.stringId)
    : undefined;
  const firstName = user.name.trim().split(/\s+/)[0] || 'player';
  const greetingName =
    firstName.length > 18 ? `${firstName.slice(0, 17)}…` : firstName;

  return (
    <AppScreen
      tone="player"
      headerVariant="primary"
      compactHeader
      title={`Welcome back, ${greetingName}`}
      subtitle="Recommendations, bookings, and service updates in one place."
      headerRight={
        <AppIconButton
          icon={
            <View>
              <Bell size={20} color="#475569" strokeWidth={2} />
              {hasUnreadNotifications ? (
                <View className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full border border-white bg-red-500" />
              ) : null}
            </View>
          }
          accessibilityLabel={
            hasUnreadNotifications
              ? 'Open notifications, unread alerts available'
              : 'Open notifications'
          }
          accessibilityHint="View booking, payment, chat, and recommendation alerts"
          onPress={() => router.push('/player/notifications')}
        />
      }
    >
      <AppSection
        title="Quick actions"
        className="mt-1"
        variant="compact"
        rightAction={
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Open all player features"
            className="min-h-11 flex-row items-center gap-1 rounded-[14px] border border-primary-100 bg-white px-3"
            onPress={() => router.push('/player/profile')}
          >
            <HeroText className="text-[13px] font-semibold text-primary-700">
              All tools
            </HeroText>
            <ChevronRight size={14} color={appChromeColors.primary} />
          </Pressable>
        }
      >
        <View className="flex-row items-start gap-1">
          {quickActions.map((action) => {
            const Icon = action.icon;
            const isFeatured = action.route === '/player/recommend';

            return (
              <Pressable
                key={action.title}
                onPress={() => router.push(action.route as never)}
                accessibilityRole="button"
                accessibilityLabel={action.accessibilityLabel}
                className="min-h-[84px] flex-1 items-center rounded-[14px] px-1 py-1.5"
                style={({ pressed }) => ({
                  opacity: pressed ? 0.72 : 1,
                  transform: [{ scale: pressed ? 0.97 : 1 }],
                })}
              >
                <View
                  style={{
                    backgroundColor: isFeatured
                      ? appChromeColors.primary
                      : appChromeColors.primarySoft,
                  }}
                  className="h-11 w-11 items-center justify-center rounded-[15px]"
                >
                  <Icon
                    size={20}
                    color={isFeatured ? '#F5D67A' : appChromeColors.primary}
                    strokeWidth={2.1}
                  />
                </View>
                <HeroText
                  className="mt-2 text-center text-[12px] font-semibold leading-[15px] text-slate-800"
                  numberOfLines={2}
                >
                  {action.title}
                </HeroText>
              </Pressable>
            );
          })}
        </View>
      </AppSection>

      {activeBooking && latestString ? (
        <AppMotion className="mt-5">
          <AppCard variant="dark" className="overflow-hidden rounded-[24px]" padding="lg">
            <View className="flex-row items-start justify-between gap-3">
              <View className="min-w-0 flex-1">
                <AppChip
                  label={formatBookingStatus(activeBooking.status)}
                  variant={getBookingStatusVariant(activeBooking.status)}
                  className="self-start"
                />
                <HeroText className="mt-4 text-[25px] font-bold leading-[30px] tracking-tight text-white">
                  Your restring is moving.
                </HeroText>
                <HeroText className="mt-2 text-sm leading-5 text-secondary-100">
                  {latestString.brand} {latestString.model} • {activeBooking.requestedTension} lbs
                </HeroText>
              </View>
              <View className="h-11 w-11 items-center justify-center rounded-[16px] bg-white/10">
                <Activity size={20} color="#FFFFFF" />
              </View>
            </View>
            <View className="mt-5 rounded-[16px] border border-white/15 bg-white/10 px-4 py-3">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-secondary-100">
                Next step
              </HeroText>
              <HeroText className="mt-1.5 text-sm leading-5 text-white">
                {getNextBookingStep(activeBooking.status, activeBooking.dropOffDate)}
              </HeroText>
            </View>
            <AppButton
              label="Open service progress"
              variant="accent"
              size="md"
              className="mt-4 w-full"
              trailingIcon={<ArrowRight size={16} color="#9A6700" />}
              onPress={() => router.push(`/player/bookings/${activeBooking.id}/tracking`)}
            />
          </AppCard>
        </AppMotion>
      ) : (
      <View className="mt-5">
        <AppCard variant="dark" className="overflow-hidden rounded-[24px]" padding="lg">
          <View
            style={{ pointerEvents: 'none' }}
            className="absolute -right-12 -top-14 h-40 w-40 rounded-full bg-primary-500/25"
          />
          <View
            style={{ pointerEvents: 'none' }}
            className="absolute -bottom-20 left-10 h-36 w-36 rounded-full bg-accent-400/10"
          />
          <View className="flex-row items-start justify-between gap-3">
            <View className="flex-1">
              <AppChip
                label="Smart recommendation"
                variant="accent"
                className="self-start opacity-95"
              />
              <HeroText className="mt-4 text-[28px] font-bold leading-[33px] tracking-tight text-white">
                Your next setup, simplified
              </HeroText>
              <HeroText className="mt-1.5 text-[13px] leading-[19px] text-secondary-100">
                Get a string and tension suggestion based on how you play.
              </HeroText>
            </View>
            <View className="mt-0.5 h-10 w-10 items-center justify-center rounded-lg bg-white/10">
              <Sparkles size={18} color="white" strokeWidth={1.9} />
            </View>
          </View>

          <View className="mt-4 flex-row gap-2.5">
            <View className="flex-1 rounded-xl border border-white/18 bg-white/8 px-3 py-2.5">
              <HeroText className="text-[10px] font-semibold uppercase tracking-[0.16em] text-secondary-100">
                Tension
              </HeroText>
              <HeroText className="mt-1 text-[17px] font-bold tracking-normal text-white">
                {user.preferredTension} lbs
              </HeroText>
            </View>
            <View className="flex-1 rounded-xl border border-white/18 bg-white/8 px-3 py-2.5">
              <HeroText className="text-[10px] font-semibold uppercase tracking-[0.16em] text-secondary-100">
                Bookings
              </HeroText>
              <HeroText className="mt-1 text-[17px] font-bold tracking-normal text-white">
                {playerBookings.length} logged
              </HeroText>
            </View>
          </View>

          <AppButton
            label="Get my recommendation"
            variant="accent"
            size="md"
            className="mt-4 w-full"
            trailingIcon={<ChevronRight size={18} color="#9A6700" strokeWidth={2.5} />}
            onPress={() => router.push('/player/recommend')}
          />
        </AppCard>
      </View>
      )}

      <AppSection
        title="Trending Strings"
        subtitle="Popular setups players are browsing this week."
        className="mt-5"
        rightAction={
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="See all strings"
            className="min-h-11 min-w-11 items-center justify-center"
            onPress={() => router.push('/player/strings')}
          >
            <HeroText className="text-[13px] font-semibold text-primary-700">
              See all
            </HeroText>
          </Pressable>
        }
      >
        <TrendingStrings />
      </AppSection>

      {!activeBooking && latestBooking && latestString ? (
        <AppSection
          title="Latest Booking"
          subtitle="Your current restring progress at a glance."
          className="mt-5"
          variant="compact"
        >
          <AppCard variant="elevated" padding="md">
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1 flex-row items-start gap-3">
                <View className="h-11 w-11 items-center justify-center rounded-xl border border-primary-200 bg-primary-50">
                  <Activity size={20} color={appChromeColors.primary} />
                </View>
                <View className="min-w-0 flex-1">
                  <HeroText className="text-[15px] font-semibold leading-[20px] tracking-normal text-slate-900">
                    {latestBooking.racketBrand} {latestBooking.racketModel}
                  </HeroText>
                  <HeroText className="mt-1 text-[12px] font-medium leading-[17px] text-slate-600">
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

            <View className="my-4 h-px w-full bg-[#E2E8F0]" />

            <View className="flex-row gap-3">
              <View className="flex-1 rounded-xl bg-[#F8FBFF] px-3 py-2.5">
                <HeroText className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                  {latestBooking.status === 'ready_for_collection' ? 'Pickup by' : 'Expected ready'}
                </HeroText>
                <HeroText className="mt-1 text-[13px] font-semibold text-slate-900">
                  {formatDateLabel(latestBooking.dropOffDate)}
                </HeroText>
              </View>
              <View className="flex-1 rounded-xl bg-[#F8FBFF] px-3 py-2.5">
                <HeroText className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Price status
                </HeroText>
                <HeroText className="mt-1 text-[13px] font-semibold text-primary-700">
                  {getBookingPriceLabel(latestBooking)}
                </HeroText>
              </View>
            </View>

            <View className="mt-4 rounded-xl border border-primary-200 bg-primary-50 px-3.5 py-3">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                Next step
              </HeroText>
              <HeroText className="mt-1 text-[13px] leading-[18px] text-slate-800">
                {getNextBookingStep(latestBooking.status, latestBooking.dropOffDate)}
              </HeroText>
            </View>

            <AppButton
              label="Open Booking"
              variant="outline"
              size="md"
              className="mt-4 w-full"
              textClassName="text-slate-900"
              trailingIcon={<ArrowRight size={16} color="#0F172A" />}
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
    case 'rejected':
      return 'Next: Review the shop reason, then choose another slot or setup.';
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
