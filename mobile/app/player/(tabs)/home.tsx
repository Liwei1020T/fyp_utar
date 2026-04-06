import React from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, Bell, CalendarClock, Dumbbell, MessageSquareText, Sparkles, TimerReset, Zap } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { BookingCard } from '../../../components/booking/BookingCard';
import {
  useBookings,
  useConversations,
  useCurrentUser,
  useNotifications,
  useStrings,
  useWallets,
} from '../../../store/appStore';
import { getStringById } from '../../../services/mockAppService';
import { formatCurrency } from '../../../lib/formatters';

const quickActions = [
  {
    title: 'Get recommendation',
    subtitle: 'Tune today’s priorities and generate a shortlist.',
    route: '/player/recommend',
    icon: Zap,
    accentClassName: 'bg-secondary-50',
    accentColor: '#D97706',
  },
  {
    title: 'Book a restring',
    subtitle: 'Choose a string, set drop-off time, and complete full mock payment.',
    route: '/player/bookings/new',
    icon: CalendarClock,
    accentClassName: 'bg-primary-50',
    accentColor: '#2F64B6',
  },
  {
    title: 'Ask support',
    subtitle: 'Start with AI, then request admin support when you need a human.',
    route: '/player/chat',
    icon: MessageSquareText,
    accentClassName: 'bg-[#E4F2F0]',
    accentColor: '#22766D',
  },
] as const;

export default function PlayerHomeScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const conversations = useConversations();
  const notifications = useNotifications();
  const strings = useStrings();
  const wallets = useWallets();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerBookings = bookings.filter((item) => item.playerId === user.id);
  const latestBooking = playerBookings[0];
  const latestString = latestBooking ? getStringById(latestBooking.stringId) : undefined;
  const unreadNotifications = notifications.filter((item) => item.userId === user.id && !item.read);
  const chatCount = conversations.filter((item) => item.playerId === user.id).length;
  const wallet = wallets.find((item) => item.userId === user.id);
  const recommendations = [...strings]
    .map((item) => ({
      item,
      score:
        item.ratings.power * user.priorities.power +
        item.ratings.control * user.priorities.control +
        item.ratings.durability * user.priorities.durability +
        item.ratings.comfort * user.priorities.comfort +
        item.ratings.sound * user.priorities.sound,
    }))
    .sort((left, right) => right.score - left.score)
    .slice(0, 3)
    .map((entry) => entry.item);

  return (
    <AppScreen
      tone="player"
      headerLeft={
        <View className="flex-row items-center gap-3">
          <View className="h-11 w-11 items-center justify-center rounded-full bg-primary-100">
            <HeroText className="text-base font-bold text-primary-700">{user.avatarLabel}</HeroText>
          </View>
          <View>
            <HeroText className="text-xs text-neutral-500">Welcome back</HeroText>
            <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
              {user.name}
            </HeroText>
          </View>
        </View>
      }
      headerRight={
        <AppIconButton
          icon={<Bell size={20} color="#475569" />}
          accessibilityLabel="Open notifications"
          onPress={() => router.push('/player/notifications')}
        />
      }
    >
      <AppCard variant="dark" className="rounded-[34px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <AppChip label="PLAYER COMMAND CENTER" variant="secondary" className="self-start" />
            <HeroText className="mt-4 text-[28px] font-bold leading-[34px] tracking-tight text-white">
              Recommendation, booking, and service updates in one place.
            </HeroText>
            <HeroText className="mt-3 text-sm leading-6 text-primary-100">
              Keep the next action obvious and the latest booking easy to track during the demo.
            </HeroText>
          </View>
          <View className="h-14 w-14 items-center justify-center rounded-[22px] bg-white/12">
            <Sparkles size={24} color="white" />
          </View>
        </View>

        <View className="mt-7 flex-row gap-3">
          <View className="min-h-[104px] flex-1 rounded-[26px] border border-white/20 bg-white/12 p-4">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-100/80">
              Preferred tension
            </HeroText>
            <HeroText className="mt-2 text-2xl font-bold text-white">
              {user.preferredTension} lbs
            </HeroText>
          </View>
          <View className="min-h-[104px] flex-1 rounded-[26px] border border-white/20 bg-white/12 p-4">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-100/80">
              Wallet balance
            </HeroText>
            <HeroText className="mt-2 text-2xl font-bold text-white">
              {formatCurrency(wallet?.availableBalance ?? 0)}
            </HeroText>
          </View>
        </View>

        <View className="mt-6 flex-row flex-wrap gap-3">
          <AppButton
            label="Open racket passport"
            variant="secondary"
            size="md"
            className="self-start"
            trailingIcon={<ArrowRight size={16} color="#78350F" strokeWidth={1.7} />}
            onPress={() => router.push('/player/rackets')}
          />
          <AppButton
            label={`Support threads ${chatCount}`}
            variant="ghost"
            size="md"
            className="self-start border-white/10 bg-white/10"
            textClassName="text-white"
            onPress={() => router.push('/player/chat')}
          />
        </View>
      </AppCard>

      <AppSection eyebrow="Quick actions" title="What do you want to do next?" subtitle="Jump straight into the player flows that matter most.">
        <View className="gap-3">
          {quickActions.map((item) => {
            const Icon = item.icon;
            return (
              <Pressable key={item.title} onPress={() => router.push(item.route as never)}>
                <AppCard variant="elevated" padding="md">
                  <View className="flex-row items-center justify-between gap-4">
                    <View className="flex-row items-center gap-4">
                      <View className={`h-12 w-12 items-center justify-center rounded-2xl ${item.accentClassName}`}>
                        <Icon size={22} color={item.accentColor} strokeWidth={1.7} />
                      </View>
                      <View className="flex-1">
                        <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                          {item.title}
                        </HeroText>
                        <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                          {item.subtitle}
                        </HeroText>
                      </View>
                    </View>
                    <ArrowRight size={18} color="#64748B" strokeWidth={1.7} />
                  </View>
                </AppCard>
              </Pressable>
            );
          })}
        </View>
      </AppSection>

      {latestBooking && latestString ? (
        <AppSection
          eyebrow="Latest booking"
          title="Current service snapshot"
          subtitle="Keep the latest service visible without digging through tabs."
          rightAction={
            <Pressable onPress={() => router.push(`/player/bookings/${latestBooking.id}/tracking`)}>
              <HeroText className="text-sm font-semibold text-primary-700">Track</HeroText>
            </Pressable>
          }
        >
          <BookingCard
            booking={latestBooking}
            stringLabel={`${latestString.brand} ${latestString.model}`}
            onPress={() => router.push(`/player/bookings/${latestBooking.id}`)}
          />
          <View className="mt-3 flex-row gap-3">
            <AppCard variant="subtle" className="flex-1" padding="sm">
              <View className="flex-row items-center gap-3">
                <View className="h-10 w-10 items-center justify-center rounded-2xl bg-primary-50">
                  <TimerReset size={18} color="#2F64B6" />
                </View>
                <View>
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
                    Payment
                  </HeroText>
                  <HeroText className="mt-1 text-base font-bold text-neutral-950">
                    {latestBooking.paymentStatus === 'paid'
                      ? 'Paid in full'
                      : formatCurrency(latestBooking.totalAmount)}
                  </HeroText>
                </View>
              </View>
            </AppCard>
            <AppCard variant="subtle" className="flex-1" padding="sm">
              <View className="flex-row items-center gap-3">
                <View className="h-10 w-10 items-center justify-center rounded-2xl bg-[#E4F2F0]">
                  <Dumbbell size={18} color="#22766D" />
                </View>
                <View>
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
                    Drop-off
                  </HeroText>
                  <HeroText className="mt-1 text-base font-bold text-neutral-950">
                    {latestBooking.dropOffDate}
                  </HeroText>
                </View>
              </View>
            </AppCard>
          </View>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Recommended now" title="Top strings for your current profile" subtitle="Ranked from your saved playing style and priority mix.">
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {recommendations.map((item) => (
            <AppCard
              key={item.id}
              variant="elevated"
              className="mr-4 w-72"
              onPress={() => router.push(`/player/strings/${item.id}`)}
            >
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary-700">
                {item.brand}
              </HeroText>
              <HeroText className="mt-2 text-xl font-bold tracking-tight text-neutral-950">
                {item.model}
              </HeroText>
              <HeroText className="mt-3 text-sm leading-6 text-neutral-500" numberOfLines={3}>
                {item.reviewHighlight}
              </HeroText>
              <View className="mt-4 flex-row flex-wrap gap-2">
                <AppChip label={`${item.ratings.power}/10 power`} variant="secondary" />
                <AppChip label={`${item.ratings.control}/10 control`} variant="info" />
                <AppChip label={item.gauge} variant="neutral" />
              </View>
            </AppCard>
          ))}
        </ScrollView>
      </AppSection>

      <AppSection eyebrow="Attention" title="What needs review?" className="mb-12">
        <View className="gap-3">
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-base font-semibold text-neutral-950">
              Unread notifications
            </HeroText>
            <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
              {unreadNotifications.length} item{unreadNotifications.length === 1 ? '' : 's'} waiting across bookings, payments, chat replies, and service updates.
            </HeroText>
          </AppCard>
        </View>
      </AppSection>
    </AppScreen>
  );
}
