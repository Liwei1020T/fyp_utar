import React from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { LogOut, Settings, Settings2 } from 'lucide-react-native';
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
  const preferredFeel = user.preferredFeel ?? 'Medium';
  const profileSummarySentence = `${apiAlignedSkillLevel} player leaning ${user.playingStyle.toLowerCase()} with a ${preferredFeel.toLowerCase()} impact feel, ${user.preferredGauge.toLowerCase()} gauge preference, and a preferred ${user.preferredTension} lbs setup for ${formatPlayFrequency(user.playFrequency).toLowerCase()} sessions.`;
  const profileChips = [
    apiAlignedSkillLevel,
    user.playingStyle,
    `${user.preferredTension} lbs`,
    formatPlayFrequency(user.playFrequency).replace(' / ', '/'),
  ];
  const profileFacts = [
    { label: 'Skill level', value: apiAlignedSkillLevel },
    { label: 'Playing style', value: apiAlignedPlayingStyle },
    { label: 'Preferred feel', value: preferredFeel },
    { label: 'Preferred gauge', value: user.preferredGauge },
    { label: 'Recent goal', value: user.recentGoal },
    { label: 'Value priority', value: `${user.priorities.value}/10` },
    { label: 'Preferred tension', value: `${user.preferredTension} lbs` },
    { label: 'Play frequency', value: formatPlayFrequency(user.playFrequency) },
  ];

  return (
    <AppScreen
      headerVariant="primary"
      title="Profile"
      subtitle="Your badminton preferences and account."
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
          label="Account settings"
          variant="outline"
          size="md"
          leadingIcon={<Settings2 size={18} color="#2F64B6" />}
          onPress={() => router.push('/player/settings')}
        />
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
          className="mt-3 h-[48px] justify-start rounded-[18px] border border-red-100/80 bg-white/70 px-4"
        />
      </View>
    </AppScreen>
  );
}
