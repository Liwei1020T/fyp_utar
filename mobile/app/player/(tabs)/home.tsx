import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  Activity,
  ArrowRight,
  Bell,
  CalendarClock,
  ChevronRight,
  Dumbbell,
  MessageSquareText,
  Search,
  Sparkles,
  Store,
  Wallet,
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
  useBusinessHoursState,
  useCurrentUser,
  useNotifications,
  useStrings,
  useWallets,
} from '../../../store/appStore';
import {
  formatBookingStatus,
  formatCurrency,
  formatDateLabel,
} from '../../../lib/formatters';
import type { Booking, BusinessHours } from '../../../types/domain';

const quickActions = [
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
    title: 'My rackets',
    accessibilityLabel: 'Open saved racket passports',
    route: '/player/rackets',
    icon: Dumbbell,
  },
  {
    title: 'Ask AI',
    accessibilityLabel: 'Open StringSense AI assistant',
    route: '/player/chatbot',
    icon: Sparkles,
  },
] as const;

export default function PlayerHomeScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const businessHours = useBusinessHoursState();
  const notifications = useNotifications();
  const strings = useStrings();
  const wallets = useWallets();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerBookings = bookings.filter((item) => item.playerId === user.id);
  const activeBooking = playerBookings.find(
    (item) => !['completed', 'cancelled', 'rejected'].includes(item.status),
  );
  const unreadNotifications = notifications.filter(
    (item) => item.userId === user.id && !item.read,
  );
  const hasUnreadNotifications = unreadNotifications.length > 0;
  const wallet = wallets.find((item) => item.userId === user.id);
  const storeHoursLabel = getStoreHoursLabel(businessHours);
  const latestBooking = playerBookings[0];
  const primaryBooking = activeBooking ?? latestBooking;
  const latestString = primaryBooking
    ? strings.find((item) => item.id === primaryBooking.stringId)
    : undefined;
  const firstName = user.name.trim().split(/\s+/)[0] || 'player';
  const greetingName =
    firstName.length > 18 ? `${firstName.slice(0, 17)}…` : firstName;
  const homeShortcuts = [
    {
      title: 'My bookings',
      detail:
        playerBookings.length === 0
          ? 'No bookings yet'
          : `${playerBookings.length} ${playerBookings.length === 1 ? 'booking' : 'bookings'}`,
      route: '/player/bookings',
      icon: CalendarClock,
    },
    {
      title: 'Notifications',
      detail:
        unreadNotifications.length === 0
          ? 'All caught up'
          : `${unreadNotifications.length} unread`,
      route: '/player/notifications',
      icon: Bell,
    },
    {
      title: 'Message shop',
      detail: 'Ask about a service',
      route: '/player/chat',
      icon: MessageSquareText,
    },
    {
      title: 'Wallet',
      detail: wallet ? `${formatCurrency(wallet.availableBalance)} available` : 'View balance',
      route: '/player/wallet',
      icon: Wallet,
    },
  ] as const;

  return (
    <AppScreen
      tone="player"
      headerVariant="primary"
      compactHeader
      title={`Welcome back, ${greetingName}`}
      subtitle="Recommendations, bookings, and updates."
      headerRight={
        <AppIconButton
          icon={
            <View className="relative">
              <Bell size={20} color="#475569" strokeWidth={2} />
              {hasUnreadNotifications ? (
                <View className="absolute -right-2 -top-2 h-4 min-w-4 items-center justify-center rounded-full border border-white bg-red-500 px-1">
                  <HeroText className="text-[9px] font-bold leading-3 text-white">
                    {unreadNotifications.length > 9 ? '9+' : unreadNotifications.length}
                  </HeroText>
                </View>
              ) : null}
            </View>
          }
          accessibilityLabel={
            hasUnreadNotifications
              ? `Open notifications, ${unreadNotifications.length} unread ${unreadNotifications.length === 1 ? 'update' : 'updates'}`
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
            className="min-h-11 flex-row items-center gap-1 rounded-[10px] border border-primary-100 bg-white px-3"
            onPress={() => router.push('/player/tools')}
          >
            <HeroText className="text-[13px] font-semibold text-primary-700">
              More
            </HeroText>
            <ChevronRight size={14} color={appChromeColors.primary} />
          </Pressable>
        }
      >
        <View className="flex-row items-start gap-1">
          {quickActions.map((action) => {
            const Icon = action.icon;
            const isFeatured = action.title === 'Book service';
            return (
              <Pressable
                key={action.title}
                onPress={() => router.push(action.route as never)}
                accessibilityRole="button"
                accessibilityLabel={action.accessibilityLabel}
                className="min-h-[76px] flex-1 items-center rounded-[12px] px-1 py-1"
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
                  className="h-10 w-10 items-center justify-center rounded-[12px]"
                >
                  <Icon
                    size={18}
                    color={isFeatured ? '#F5D67A' : appChromeColors.primary}
                    strokeWidth={2.1}
                  />
                </View>
                <HeroText
                  className="mt-1.5 text-center text-[12px] font-semibold leading-[15px] text-slate-800"
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
        <AppMotion className="mt-4">
          <AppCard variant="dark" className="overflow-hidden rounded-[24px]" padding="lg">
            <View className="flex-row items-start justify-between gap-3">
              <View className="min-w-0 flex-1">
                <AppChip
                  label={formatBookingStatus(activeBooking.status)}
                  variant={getBookingStatusVariant(activeBooking.status)}
                  className="self-start"
                />
                <HeroText className="mt-3 text-[22px] font-bold leading-[27px] tracking-tight text-white">
                  Your restring is moving.
                </HeroText>
                <HeroText className="mt-1.5 text-[13px] font-semibold leading-[18px] text-white">
                  {activeBooking.racketBrand} {activeBooking.racketModel}
                </HeroText>
                <HeroText className="mt-0.5 text-[13px] leading-[18px] text-secondary-100">
                  {latestString.brand} {latestString.model} • {activeBooking.requestedTension} lbs
                </HeroText>
              </View>
              <View className="h-10 w-10 items-center justify-center rounded-[12px] bg-white/10">
                <Activity size={18} color="#FFFFFF" />
              </View>
            </View>
            <View className="mt-4 flex-row gap-2">
              <View className="flex-1 rounded-[14px] bg-white/10 px-3 py-2.5">
                <HeroText className="text-[10px] font-semibold uppercase tracking-[0.16em] text-secondary-100">
                  Drop-off
                </HeroText>
                <HeroText
                  className="mt-1 text-[13px] font-semibold leading-[17px] text-white"
                  numberOfLines={2}
                >
                  {formatRelativeBookingDate(activeBooking.dropOffDate, activeBooking.dropOffTime)}
                </HeroText>
              </View>
              <View className="flex-1 rounded-[14px] bg-white/10 px-3 py-2.5">
                <HeroText className="text-[10px] font-semibold uppercase tracking-[0.16em] text-secondary-100">
                  Payment
                </HeroText>
                <HeroText
                  className="mt-1 text-[13px] font-semibold leading-[17px] text-white"
                  numberOfLines={2}
                >
                  {getBookingPaymentLabel(activeBooking)}
                </HeroText>
              </View>
            </View>
            <View className="mt-4 rounded-[14px] border border-white/15 bg-white/10 px-3 py-2.5">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-secondary-100">
                Next step
              </HeroText>
              <HeroText className="mt-1 text-sm leading-5 text-white">
                {getNextBookingStep(
                  activeBooking.status,
                  activeBooking.dropOffDate,
                  activeBooking.dropOffTime,
                )}
              </HeroText>
            </View>
            <AppButton
              label="Open service progress"
              variant="accent"
              size="md"
              className="mt-3 w-full"
              trailingIcon={<ArrowRight size={16} color="#9A6700" />}
              onPress={() => router.push(`/player/bookings/${activeBooking.id}/tracking`)}
            />
          </AppCard>
        </AppMotion>
      ) : (
        <View className="mt-4">
          <AppCard variant="dark" className="overflow-hidden rounded-[20px]" padding="md">
            <View
              style={{ pointerEvents: 'none' }}
              className="absolute -right-8 -top-10 h-28 w-28 rounded-full bg-primary-500/25"
            />
            <View className="flex-row items-start justify-between gap-3">
              <View className="min-w-0 flex-1">
                <HeroText className="text-[20px] font-bold leading-[24px] tracking-tight text-white">
                  Find your next string
                </HeroText>
                <HeroText className="mt-1 text-[13px] leading-[18px] text-secondary-100">
                  Based on your game and {user.preferredTension} lbs preference.
                </HeroText>
              </View>
              <View className="h-10 w-10 items-center justify-center rounded-[14px] bg-white/10">
                <Sparkles size={18} color="white" strokeWidth={1.9} />
              </View>
            </View>

            <AppButton
              label="Get recommendation"
              variant="accent"
              size="sm"
              className="mt-3 w-full"
              trailingIcon={<ChevronRight size={16} color="#9A6700" strokeWidth={2.5} />}
              onPress={() => router.push('/player/recommend')}
            />
          </AppCard>
        </View>
      )}

      {storeHoursLabel ? (
        <View className="mt-2 flex-row items-center gap-1.5 px-1">
          <Store size={14} color={appChromeColors.primary} strokeWidth={2} />
          <HeroText className="text-[12px] font-medium text-slate-600">
            {storeHoursLabel}
          </HeroText>
        </View>
      ) : null}

      <AppSection
        title="Quick access"
        subtitle="Your everyday shortcuts."
        className="mt-4"
        variant="compact"
      >
        {[homeShortcuts.slice(0, 2), homeShortcuts.slice(2)].map((row, rowIndex) => (
          <View
            key={rowIndex}
            className={rowIndex === 0 ? 'flex-row gap-2' : 'mt-2 flex-row gap-2'}
          >
            {row.map((shortcut) => {
              const Icon = shortcut.icon;

              return (
                <Pressable
                  key={shortcut.title}
                  accessibilityRole="button"
                  accessibilityLabel={`${shortcut.title}, ${shortcut.detail}`}
                  accessibilityHint={`Open ${shortcut.title.toLowerCase()}`}
                  onPress={() => router.push(shortcut.route as never)}
                  className="min-h-[68px] flex-1 flex-row items-center gap-2 rounded-[14px] border border-[#DCE6F7] bg-white px-3 py-2.5"
                  style={({ pressed }) => ({
                    opacity: pressed ? 0.72 : 1,
                    transform: [{ scale: pressed ? 0.98 : 1 }],
                  })}
                >
                  <View className="h-8 w-8 items-center justify-center rounded-[10px] bg-primary-50">
                    <Icon size={16} color={appChromeColors.primary} strokeWidth={2} />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText
                      className="text-[13px] font-semibold leading-[17px] text-slate-900"
                      numberOfLines={1}
                    >
                      {shortcut.title}
                    </HeroText>
                    <HeroText
                      className="mt-0.5 text-[11px] leading-[15px] text-slate-500"
                      numberOfLines={1}
                    >
                      {shortcut.detail}
                    </HeroText>
                  </View>
                  <ChevronRight size={14} color="#94A3B8" />
                </Pressable>
              );
            })}
          </View>
        ))}
      </AppSection>

      <AppSection
        title="Featured strings"
        subtitle="Selected by the shop this week."
        className="mt-4"
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
          className="mt-4"
          variant="compact"
        >
          <AppCard variant="elevated" padding="md">
            <View className="flex-row items-start justify-between gap-2.5">
              <View className="flex-1 flex-row items-start gap-2.5">
                <View className="h-10 w-10 items-center justify-center rounded-[10px] border border-primary-200 bg-primary-50">
                  <Activity size={18} color={appChromeColors.primary} />
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

            <View className="my-3 h-px w-full bg-[#E2E8F0]" />

            <View className="flex-row gap-2">
              <View className="flex-1 rounded-xl bg-[#F8FBFF] px-3 py-2">
                <HeroText className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                  {latestBooking.status === 'ready_for_collection' ? 'Pickup by' : 'Expected ready'}
                </HeroText>
                <HeroText className="mt-1 text-[13px] font-semibold text-slate-900">
                  {formatDateLabel(latestBooking.dropOffDate)}
                </HeroText>
              </View>
              <View className="flex-1 rounded-xl bg-[#F8FBFF] px-3 py-2">
                <HeroText className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Price status
                </HeroText>
                <HeroText className="mt-1 text-[13px] font-semibold text-primary-700">
                  {getBookingPriceLabel(latestBooking)}
                </HeroText>
              </View>
            </View>

            <View className="mt-3 rounded-xl border border-primary-200 bg-primary-50 px-3 py-2.5">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                Next step
              </HeroText>
              <HeroText className="mt-1 text-[13px] leading-[18px] text-slate-800">
                {getNextBookingStep(
                  latestBooking.status,
                  latestBooking.dropOffDate,
                  latestBooking.dropOffTime,
                )}
              </HeroText>
            </View>

            <AppButton
              label="Open Booking"
              variant="outline"
              size="md"
              className="mt-3 w-full"
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

function getNextBookingStep(
  status: Booking['status'],
  dropOffDate: string,
  dropOffTime?: string,
) {
  switch (status) {
    case 'pending':
    case 'pending_payment':
      return 'Next: Confirm your booking details and finalise the quote at the shop.';
    case 'confirmed':
    case 'awaiting_dropoff':
      {
        const schedule = formatRelativeBookingDate(dropOffDate, dropOffTime);
        return schedule.startsWith('Overdue')
          ? `Next: Drop off — ${schedule.toLowerCase()}.`
          : `Next: Drop off ${schedule}.`;
      }
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

function getBookingPaymentLabel(booking: Booking) {
  switch (booking.paymentStatus) {
    case 'paid':
      return booking.totalAmount > 0
        ? `Paid · ${formatCurrency(booking.totalAmount)}`
        : 'Paid';
    case 'pending':
      return 'Payment pending';
    case 'unpaid':
      return 'Payment due';
    case 'failed':
      return 'Payment failed';
    case 'cancelled':
      return 'Payment cancelled';
  }
}

function formatRelativeBookingDate(dateValue: string, time?: string) {
  const bookingDate = parseCalendarDate(dateValue);
  if (!bookingDate) {
    return `${formatDateLabel(dateValue)}${time ? ` · ${time}` : ''}`;
  }

  const difference = calendarDayNumber(bookingDate) - calendarDayNumber(new Date());
  const formattedTime = time ? ` ${formatClockTime(time)}` : '';

  if (difference < 0) {
    const days = Math.abs(difference);
    return `Overdue by ${days} ${days === 1 ? 'day' : 'days'}`;
  }

  if (difference === 0) {
    return `Today${formattedTime}`;
  }

  if (difference === 1) {
    return `Tomorrow${formattedTime}`;
  }

  return `On ${formatDateLabel(dateValue)}${formattedTime}`;
}

function parseCalendarDate(value: string) {
  const [year, month, day] = value.slice(0, 10).split('-').map(Number);
  if (![year, month, day].every(Number.isFinite)) {
    return null;
  }

  const date = new Date(year, month - 1, day);
  return date.getFullYear() === year &&
    date.getMonth() === month - 1 &&
    date.getDate() === day
    ? date
    : null;
}

function calendarDayNumber(date: Date) {
  return Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86_400_000;
}

function formatClockTime(value?: string) {
  if (!value) {
    return '';
  }

  const [hour, minute] = value.split(':').map(Number);
  if (![hour, minute].every(Number.isFinite)) {
    return value;
  }

  const suffix = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${String(minute).padStart(2, '0')} ${suffix}`;
}

const WEEKDAY_NAMES = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
] as const;

function getStoreHoursLabel(hoursList: BusinessHours[]) {
  const hours = hoursList[0];
  if (!hours) {
    return null;
  }

  const now = new Date();
  const today = hours.days.find((item) => item.day === WEEKDAY_NAMES[now.getDay()]);
  const todayKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  const isSpecialClosed = hours.specialClosedDates.includes(todayKey);
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const openMinutes = toMinutes(today?.openTime);
  const closeMinutes = toMinutes(today?.closeTime);
  const breakStart = toMinutes(today?.breakStart);
  const breakEnd = toMinutes(today?.breakEnd);

  if (
    today?.isOpen &&
    !isSpecialClosed &&
    openMinutes != null &&
    closeMinutes != null &&
    currentMinutes >= openMinutes &&
    currentMinutes < closeMinutes
  ) {
    if (
      breakStart != null &&
      breakEnd != null &&
      currentMinutes >= breakStart &&
      currentMinutes < breakEnd
    ) {
      return `Closed for break · Reopens ${formatClockTime(today.breakEnd)}`;
    }
    return `Open until ${formatClockTime(today.closeTime)}`;
  }

  if (
    today?.isOpen &&
    !isSpecialClosed &&
    openMinutes != null &&
    currentMinutes < openMinutes
  ) {
    return `Closed · Opens today at ${formatClockTime(today.openTime)}`;
  }

  return `Closed · Opens ${getNextOpenLabel(hours, now)}`;
}

function getNextOpenLabel(hours: BusinessHours, now: Date) {
  for (let offset = 1; offset <= 7; offset += 1) {
    const date = new Date(now);
    date.setDate(date.getDate() + offset);
    const day = hours.days.find((item) => item.day === WEEKDAY_NAMES[date.getDay()]);
    const dateKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

    if (day?.isOpen && !hours.specialClosedDates.includes(dateKey)) {
      const label = offset === 1 ? 'tomorrow' : day.day;
      return `${label} at ${formatClockTime(day.openTime)}`;
    }
  }

  return 'later';
}

function toMinutes(value?: string) {
  if (!value) {
    return null;
  }

  const [hour, minute] = value.split(':').map(Number);
  return [hour, minute].every(Number.isFinite) ? hour * 60 + minute : null;
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
