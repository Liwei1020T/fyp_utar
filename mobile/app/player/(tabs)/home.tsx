import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, CalendarClock, Sparkles, TimerReset, Zap } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { BookingCard } from '../../../components/booking/BookingCard';
import {
  useBookings,
  useCurrentUser,
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
    subtitle: 'Choose a string, select a backend slot, and confirm the booking.',
    route: '/player/bookings/new',
    icon: CalendarClock,
    accentClassName: 'bg-primary-50',
    accentColor: '#2F64B6',
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
              My bookings
            </HeroText>
            <HeroText className="mt-2 text-2xl font-bold text-white">
              {playerBookings.length}
            </HeroText>
          </View>
        </View>

        <AppButton
          label="Generate recommendation"
          variant="secondary"
          size="md"
          className="mt-6 self-start"
          trailingIcon={<ArrowRight size={16} color="#78350F" strokeWidth={1.7} />}
          onPress={() => router.push('/player/recommend')}
        />
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
                    Estimated total
                  </HeroText>
                  <HeroText className="mt-1 text-base font-bold text-neutral-950">
                    {formatCurrency(latestBooking.totalAmount)}
                  </HeroText>
                </View>
              </View>
            </AppCard>
            <AppCard variant="subtle" className="flex-1" padding="sm">
              <View className="flex-row items-center gap-3">
                <View className="h-10 w-10 items-center justify-center rounded-2xl bg-[#E4F2F0]">
                  <CalendarClock size={18} color="#22766D" />
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

      <AppSection eyebrow="Recommendation" title="Use the backend recommender" className="mb-12">
        <AppCard variant="highlighted" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            FYP1 keeps recommendation scoring centralized on the recommendation page so the demo uses one backend-backed flow.
          </HeroText>
          <AppButton
            label="Open recommendation"
            className="mt-4"
            onPress={() => router.push('/player/recommend')}
          />
        </AppCard>
      </AppSection>
    </AppScreen>
  );
}
