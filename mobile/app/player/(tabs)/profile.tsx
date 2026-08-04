import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  BadgeCheck,
  Bell,
  Gauge,
  LogOut,
  MessageSquareText,
  NotebookText,
  Settings2,
  Settings,
  Sparkles,
  Wallet,
} from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  useAppStore,
  useBookings,
  useCurrentUser,
} from '../../../store/appStore';
import { formatPlayFrequency } from '../../../lib/formatters';

export default function PlayerProfileScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const logout = useAppStore((state) => state.logout);
  const bookings = useBookings();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerBookings = bookings.filter((item) => item.playerId === user.id);
  const apiAlignedSkillLevel =
    user.skillLevel === 'Competitive' ? 'Advanced' : user.skillLevel;
  const apiAlignedPlayingStyle =
    user.playingStyle === 'Defensive'
      ? 'Control / Defensive'
      : user.playingStyle;
  const budgetRange = user.budgetRange ?? 'RM30–RM50';
  const preferredFeel = user.preferredFeel ?? 'Balanced';
  const profileSummarySentence = `${apiAlignedSkillLevel} player leaning ${user.playingStyle.toLowerCase()} with a ${preferredFeel.toLowerCase()} impact feel, ${budgetRange.toLowerCase()} budget, and a preferred ${user.preferredTension} lbs setup for ${formatPlayFrequency(user.playFrequency).toLowerCase()} sessions.`;
  const profileChips = [
    apiAlignedSkillLevel,
    user.playingStyle,
    `${user.preferredTension} lbs`,
    formatPlayFrequency(user.playFrequency).replace(' / ', '/'),
  ];
  const shortcutItems = [
    {
      title: 'Booking support',
      subtitle: 'Find messages attached to your service bookings.',
      icon: <MessageSquareText size={18} color="#2F64B6" />,
      route: '/player/chat',
    },
    {
      title: 'Notifications',
      subtitle: 'Review booking, payment, chat, and recommendation updates.',
      icon: <Bell size={18} color="#2F64B6" />,
      route: '/player/notifications',
    },
    {
      title: 'Racket passport',
      subtitle: 'Review rackets and stringing history from completed bookings.',
      icon: <BadgeCheck size={18} color="#2F64B6" />,
      route: '/player/rackets',
    },
    {
      title: 'Wallet',
      subtitle: 'Review verified balance, transactions, and pending top-ups.',
      icon: <Wallet size={18} color="#2F64B6" />,
      route: '/player/wallet',
    },
    {
      title: 'App settings',
      subtitle: 'Manage account, password, privacy, notifications, and deletion requests.',
      icon: <Settings2 size={18} color="#2F64B6" />,
      route: '/player/settings',
    },
    {
      title: 'Edit onboarding profile',
      subtitle: 'Update skill level, style, priorities, and preferred tension.',
      icon: <Sparkles size={18} color="#2F64B6" />,
      route: '/player/profile/edit',
    },
    {
      title: 'Recommendation setup',
      subtitle: 'Refresh your recommendation flow with your latest preferences.',
      icon: <Gauge size={18} color="#2F64B6" />,
      route: '/player/recommend',
    },
    {
      title: 'My bookings',
      subtitle: 'Check current orders, collection status, and service history.',
      icon: <NotebookText size={18} color="#2F64B6" />,
      route: '/player/bookings',
    },
  ] as const;
  const profileFacts = [
    { label: 'Skill level', value: apiAlignedSkillLevel },
    { label: 'Playing style', value: apiAlignedPlayingStyle },
    { label: 'Budget range', value: budgetRange },
    { label: 'Preferred feel', value: preferredFeel },
    { label: 'Preferred tension', value: `${user.preferredTension} lbs` },
    { label: 'Play frequency', value: formatPlayFrequency(user.playFrequency) },
  ];

  return (
    <AppScreen
      headerVariant="primary"
      title="Profile"
      subtitle="Your badminton preferences, activity snapshot, and quick actions."
      headerRight={
        <AppIconButton
          icon={<Settings size={20} color="#475569" />}
          accessibilityLabel="Edit player profile"
          onPress={() => router.push('/player/profile/edit')}
        />
      }
    >
      <AppCard variant="elevated" className="rounded-[30px]" padding="md">
        <View className="flex-row items-start gap-4">
          <View className="h-16 w-16 items-center justify-center rounded-full bg-primary-100">
            <HeroText className="text-[22px] font-bold text-primary-700 leading-none">
              {user.avatarLabel}
            </HeroText>
          </View>
          <View className="min-w-0 flex-1">
            <HeroText className="text-[20px] font-bold tracking-tight text-neutral-950 leading-tight">
              {user.name}
            </HeroText>
            <HeroText className="mt-1 text-[13px] text-neutral-500 font-medium">
              {user.phone || user.email}
            </HeroText>
            <View className="mt-3 flex-row flex-wrap gap-2">
              {profileChips.map((chip) => (
                <AppChip
                  key={chip}
                  label={chip}
                  variant={chip === `${user.preferredTension} lbs` ? 'secondary' : 'primary'}
                />
              ))}
            </View>
          </View>
        </View>
      </AppCard>

      <AppSection
        eyebrow="ALL FEATURES"
        title="More player tools"
        subtitle="Find every account, support, racket, and payment feature here."
        variant="compact"
      >
        <View className="flex-row flex-wrap gap-3">
          {shortcutItems.map((item) => (
            <Pressable
              key={item.title}
              onPress={() => router.push(item.route as never)}
              accessibilityRole="button"
              accessibilityLabel={`${item.title}. ${item.subtitle}`}
              accessibilityHint={`Open ${item.title.toLowerCase()}`}
              className="w-[48%] active:opacity-70"
            >
              <AppCard
                variant="elevated"
                padding="sm"
                className="h-full rounded-[20px]"
                contentClassName="min-h-[96px] justify-between"
              >
                <View className="h-11 w-11 items-center justify-center rounded-2xl bg-primary-50">
                  {item.icon}
                </View>
                <View className="mt-3">
                  <HeroText className="text-[14px] font-bold leading-5 text-neutral-900">
                    {item.title}
                  </HeroText>
                </View>
              </AppCard>
            </Pressable>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="ACTIVITY" title="Your quick stats" variant="compact">
        <View className="flex-row gap-3">
          {[
            { value: playerBookings.length, label: 'Bookings' },
            { value: `${user.preferredTension} lbs`, label: 'Fav tension' },
          ].map((stat) => (
            <AppCard
              key={stat.label}
              variant="elevated"
              padding="md"
              className="flex-1 rounded-[24px]"
            >
              <HeroText className="text-[22px] font-bold tracking-tight text-neutral-950">
                {stat.value}
              </HeroText>
              <HeroText className="mt-1 text-[12px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
                {stat.label}
              </HeroText>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="SAVED PROFILE" title="Preference summary">
        <AppCard variant="elevated" padding="md" className="rounded-[28px]">
          <View className="flex-row flex-wrap">
            {profileFacts.map((fact, index) => (
              <View
                key={fact.label}
                className={[
                  'w-1/2 pb-4',
                  index % 2 === 0 ? 'pr-2' : 'pl-2',
                  index >= profileFacts.length - 2 ? 'pb-0' : '',
                ].join(' ')}
              >
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
                  {fact.label}
                </HeroText>
                <HeroText className="mt-1.5 text-[15px] font-bold tracking-tight text-neutral-900">
                  {fact.value}
                </HeroText>
              </View>
            ))}
          </View>

          <View className="mt-4 rounded-[22px] bg-secondary-50 px-4 py-3.5">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-700">
              Profile note
            </HeroText>
            <HeroText className="mt-1.5 text-[13px] leading-5 text-neutral-600 font-medium">
              {profileSummarySentence}
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      <View className="mt-8 mb-3">
        <HeroText className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
          Account
        </HeroText>
        <AppButton
          label="Log out"
          variant="ghost"
          size="md"
          onPress={() => {
            logout();
            router.replace('/auth/login');
          }}
          leadingIcon={<LogOut size={18} color="#DC2626" />}
          textClassName="text-red-600 font-semibold"
          className="h-[48px] justify-start rounded-[18px] border border-red-100/80 bg-white/70 px-4"
        />
      </View>
    </AppScreen>
  );
}
