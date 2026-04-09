import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  ChevronLeft,
  ChevronRight,
  LogOut,
  Settings,
  Star,
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

  return (
    <AppScreen
      title="Profile"
      subtitle="Your player identity, saved preferences, and product shortcuts."
      headerLeft={
        router.canGoBack() ? (
          <AppIconButton
            icon={<ChevronLeft size={20} color="#475569" />}
            accessibilityLabel="Go back"
            onPress={() => router.back()}
          />
        ) : undefined
      }
      headerRight={
        <AppIconButton
          icon={<Settings size={20} color="#475569" />}
          accessibilityLabel="Edit player profile"
          onPress={() => router.push('/player/profile/edit')}
        />
      }
    >
      <AppCard variant="dark" className="rounded-[40px] pt-10 pb-9" padding="lg">
        <View className="flex-row items-center gap-6 px-1">
          <View className="h-24 w-24 items-center justify-center rounded-full bg-white/10 shadow-sm">
            <HeroText className="text-[34px] font-bold text-white leading-none">
              {user.avatarLabel}
            </HeroText>
          </View>
          <View className="min-w-0 flex-1">
            <View className="self-start rounded-full bg-white/10 border border-white/5 px-4 py-2">
              <HeroText className="text-[10px] font-bold tracking-[0.08em] text-secondary-300">
                PLAYER PROFILE
              </HeroText>
            </View>
            <HeroText className="mt-5 text-[34px] font-bold tracking-tight text-white leading-[38px]">
              {user.name}
            </HeroText>
            <HeroText className="mt-1 text-base text-white/70 font-medium tracking-wide">
              {user.phone || user.email}
            </HeroText>
          </View>
        </View>

        <View className="mt-9 flex-row gap-4">
          {[
            { value: playerBookings.length, label: 'Bookings' },
            { value: user.preferredTension, label: 'Fav lbs' },
          ].map((stat, index) => (
            <View key={index} className="flex-1">
              <View className="rounded-[30px] border border-white/10 p-1 bg-white/5 shadow-sm">
                <View className="items-center justify-center rounded-[24px] bg-white/10 py-5 px-2">
                  <HeroText className="text-3xl font-bold text-white">
                    {stat.value}
                  </HeroText>
                  <HeroText className="mt-1.5 text-[10px] uppercase font-bold tracking-[0.16em] text-white/40">
                    {stat.label}
                  </HeroText>
                </View>
              </View>
            </View>
          ))}
        </View>
      </AppCard>

      <AppSection eyebrow="SAVED PROFILE" title="Player snapshot">
        <AppCard variant="elevated" padding="md" className="rounded-[28px]">
          <View className="flex-row flex-wrap gap-2">
            <AppChip label={apiAlignedSkillLevel} variant="primary" />
            <AppChip label={apiAlignedPlayingStyle} variant="info" />
            <AppChip
              label={`${user.preferredTension} lbs`}
              variant="warning"
              className="bg-secondary-50 border-secondary-100"
            />
            <AppChip label={formatPlayFrequency(user.playFrequency)} variant="neutral" />
          </View>
          <HeroText className="mt-4 text-[13px] leading-6 text-neutral-500 font-medium">
            Current focus: Use your saved profile to generate a grounded
            shortlist for the next restring.
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="SHORTCUTS" title="Go straight to what matters">
        <View className="gap-3">
          {[
            {
              title: 'Edit onboarding profile',
              subtitle:
                'Skill level, playing style, priorities, and preferred tension.',
              icon: <Star size={18} color="#2F64B6" />,
              route: '/player/profile/edit',
            },
          ].map((item) => (
            <Pressable
              key={item.title}
              onPress={() => router.push(item.route as never)}
              className="active:opacity-70"
            >
              <AppCard
                variant="elevated"
                padding="md"
                className="rounded-[24px]"
              >
                <View className="flex-row items-center justify-between gap-4">
                  <View className="flex-row items-center gap-3.5">
                    <View className="h-10 w-10 items-center justify-center rounded-2xl bg-primary-50">
                      {item.icon}
                    </View>
                    <View className="flex-1">
                      <HeroText className="text-[15px] font-bold text-neutral-900 leading-tight">
                        {item.title}
                      </HeroText>
                      <HeroText className="mt-1 text-[13px] leading-5 text-neutral-500 font-medium">
                        {item.subtitle}
                      </HeroText>
                    </View>
                  </View>
                  <ChevronRight size={18} color="#94A3B8" />
                </View>
              </AppCard>
            </Pressable>
          ))}
        </View>
      </AppSection>

      <View className="mt-10 mb-6">
        <AppButton
          label="Log out"
          variant="outline"
          size="lg"
          onPress={() => {
            logout();
            router.replace('/auth/welcome');
          }}
          leadingIcon={<LogOut size={18} color="#DC2626" />}
          textClassName="text-red-600 font-bold"
          className="border-red-100 h-[56px] rounded-[18px]"
        />
      </View>
    </AppScreen>
  );
}
