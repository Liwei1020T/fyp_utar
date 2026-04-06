import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Bell, ChevronLeft, ChevronRight, Dumbbell, LogOut, Settings, Star, Wallet } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { useAppStore, useBookings, useCurrentUser, useNotifications, useWallets } from '../../../store/appStore';
import { getRacketsForPlayer } from '../../../services/mockAppService';

export default function PlayerProfileScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const logout = useAppStore((state) => state.logout);
  const bookings = useBookings();
  const notifications = useNotifications();
  const wallets = useWallets();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerBookings = bookings.filter((item) => item.playerId === user.id);
  const rackets = getRacketsForPlayer(user.id);
  const unreadNotifications = notifications.filter((item) => item.userId === user.id && !item.read).length;
  const wallet = wallets.find((item) => item.userId === user.id);

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
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <View className="flex-row items-center gap-4">
          <View className="h-20 w-20 items-center justify-center rounded-full bg-white/10">
            <HeroText className="text-[28px] font-bold text-white">{user.avatarLabel}</HeroText>
          </View>
          <View className="min-w-0 flex-1">
            <AppChip label="PLAYER PROFILE" variant="secondary" className="self-start" />
            <HeroText className="mt-4 text-[28px] font-bold tracking-tight text-white">
              {user.name}
            </HeroText>
            <HeroText className="mt-1 text-sm text-primary-100">{user.email}</HeroText>
          </View>
        </View>

        <View className="mt-7 flex-row gap-3">
          <AppCard variant="subtle" className="flex-1 items-center bg-white/14 border-white/15" padding="sm">
            <HeroText className="text-2xl font-bold text-white">{playerBookings.length}</HeroText>
            <HeroText className="mt-1 text-xs uppercase tracking-[0.16em] text-primary-50">
              Bookings
            </HeroText>
          </AppCard>
          <AppCard variant="subtle" className="flex-1 items-center bg-white/14 border-white/15" padding="sm">
            <HeroText className="text-2xl font-bold text-white">{rackets.length}</HeroText>
            <HeroText className="mt-1 text-xs uppercase tracking-[0.16em] text-primary-50">
              Rackets
            </HeroText>
          </AppCard>
          <AppCard variant="subtle" className="flex-1 items-center bg-white/14 border-white/15" padding="sm">
            <HeroText className="text-2xl font-bold text-white">{user.preferredTension}</HeroText>
            <HeroText className="mt-1 text-xs uppercase tracking-[0.16em] text-primary-50">
              Fav lbs
            </HeroText>
          </AppCard>
        </View>
      </AppCard>

      <AppSection eyebrow="Saved profile" title="Player snapshot">
        <AppCard variant="elevated" padding="md">
          <View className="flex-row flex-wrap gap-2">
            <AppChip label={user.skillLevel} variant="primary" />
            <AppChip label={user.playingStyle} variant="info" />
            <AppChip label={`${user.preferredTension} lbs`} variant="secondary" />
            <AppChip label={user.playFrequency} variant="neutral" />
          </View>
          <HeroText className="mt-4 text-sm leading-6 text-neutral-500">
            Current focus: {user.recentGoal}
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Shortcuts" title="Go straight to what matters">
        <View className="gap-3">
          {[
            { title: 'Edit onboarding profile', subtitle: 'Skill level, playing style, priorities, and preferred tension.', icon: <Star size={18} color="#2F64B6" />, route: '/player/profile/edit' },
            { title: 'Notification center', subtitle: `${unreadNotifications} unread alerts across bookings, chat, and service updates.`, icon: <Bell size={18} color="#22766D" />, route: '/player/notifications' },
            { title: 'Racket passport', subtitle: 'Saved frames, string history, tensions, and service notes.', icon: <Dumbbell size={18} color="#6550B8" />, route: '/player/rackets' },
            { title: 'Wallet balance', subtitle: `Stored balance ${wallet ? `RM ${wallet.availableBalance.toFixed(2)}` : 'RM 0.00'} for future checkout support.`, icon: <Wallet size={18} color="#C98A2E" />, route: '/player/wallet' },
          ].map((item) => (
            <Pressable key={item.title} onPress={() => router.push(item.route as never)}>
              <AppCard variant="elevated" padding="md">
                <View className="flex-row items-center justify-between gap-4">
                  <View className="flex-row items-center gap-3">
                    <View className="h-10 w-10 items-center justify-center rounded-2xl bg-primary-50">
                      {item.icon}
                    </View>
                    <View className="flex-1">
                      <HeroText className="text-base font-semibold text-neutral-900">
                        {item.title}
                      </HeroText>
                      <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
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

      <View className="mt-10">
        <AppButton
          label="Log out"
          variant="outline"
          size="lg"
          onPress={() => {
            logout();
            router.replace('/auth/welcome');
          }}
          leadingIcon={<LogOut size={18} color="#DC2626" />}
          textClassName="text-red-600"
          className="border-red-100"
        />
      </View>
    </AppScreen>
  );
}
