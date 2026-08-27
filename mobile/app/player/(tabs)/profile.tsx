import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  BadgeCheck,
  Bell,
  CalendarDays,
  ChevronRight,
  LockKeyhole,
  LogOut,
  Pencil,
  WalletCards,
  type LucideIcon,
} from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  useAppStore,
  useBookings,
  useCurrentUser,
  useNotifications,
  useRackets,
  useWallets,
} from '../../../store/appStore';
import { formatCurrency, formatPlayFrequency } from '../../../lib/formatters';

interface ProfileActionRowProps {
  icon: LucideIcon;
  title: string;
  detail: string;
  onPress: () => void;
  first?: boolean;
}

function ProfileActionRow({
  icon: Icon,
  title,
  detail,
  onPress,
  first = false,
}: ProfileActionRowProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${title}. ${detail}`}
      accessibilityHint={`Open ${title.toLowerCase()}`}
      className={`min-h-[64px] flex-row items-center gap-3 px-3.5 py-3 ${
        first ? '' : 'border-t border-[#E7ECF2]'
      }`}
      style={({ pressed }) => ({
        opacity: pressed ? 0.72 : 1,
        transform: [{ scale: pressed ? 0.99 : 1 }],
      })}
      onPress={onPress}
    >
      <View className="h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-primary-50">
        <Icon size={18} color="#2563EB" strokeWidth={2} />
      </View>
      <View className="min-w-0 flex-1">
        <HeroText className="text-[14px] font-semibold leading-[18px] text-slate-900">
          {title}
        </HeroText>
        <HeroText className="mt-0.5 text-[12px] leading-[17px] text-slate-500">
          {detail}
        </HeroText>
      </View>
      <ChevronRight size={18} color="#94A3B8" />
    </Pressable>
  );
}

export default function PlayerProfileScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const logout = useAppStore((state) => state.logout);
  const bookings = useBookings();
  const rackets = useRackets();
  const wallets = useWallets();
  const notifications = useNotifications();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerBookings = bookings.filter((item) => item.playerId === user.id);
  const playerRackets = rackets.filter((item) => item.playerId === user.id);
  const playerNotifications = notifications.filter((item) => item.userId === user.id);
  const unreadNotifications = playerNotifications.filter((item) => !item.read).length;
  const wallet = wallets.find((item) => item.userId === user.id);
  const skillLevel = user.skillLevel === 'Competitive' ? 'Advanced' : user.skillLevel;
  const playingStyle =
    user.playingStyle === 'Defensive' ? 'Control / Defensive' : user.playingStyle;
  const preferredFeel = user.preferredFeel ?? 'Medium';
  const setupRows = [
    [
      { label: 'Skill', value: skillLevel },
      { label: 'Style', value: playingStyle },
    ],
    [
      { label: 'Tension', value: `${user.preferredTension} lbs` },
      { label: 'Frequency', value: formatPlayFrequency(user.playFrequency) },
    ],
    [
      { label: 'Feel', value: preferredFeel },
      { label: 'Goal', value: user.recentGoal },
    ],
  ];

  return (
    <AppScreen
      headerVariant="primary"
      title="Profile"
      subtitle="Your setup, activity, and gear."
      headerRight={
        <AppIconButton
          icon={<Pencil size={18} color="#475569" />}
          accessibilityLabel="Edit player profile"
          onPress={() => router.push('/player/profile/edit')}
        />
      }
    >
      <AppCard variant="dark" className="rounded-[16px]" padding="md">
        <View className="flex-row items-center gap-3">
          <View className="h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white/15">
            <HeroText className="text-[18px] font-bold leading-none text-white">
              {user.avatarLabel}
            </HeroText>
          </View>
          <View className="min-w-0 flex-1">
            <HeroText className="text-[18px] font-bold leading-[22px] tracking-tight text-white">
              {user.name}
            </HeroText>
            <HeroText className="mt-0.5 text-[12px] font-medium text-primary-100">
              {user.phone || user.email}
            </HeroText>
          </View>
        </View>

        <View className="mt-3 flex-row gap-2">
          <View className="flex-1 rounded-[10px] bg-white/10 px-3 py-2">
            <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-primary-100">
              Preferred tension
            </HeroText>
            <HeroText className="mt-1 text-[16px] font-bold text-white">
              {user.preferredTension} lbs
            </HeroText>
          </View>
          <View className="flex-1 rounded-[10px] bg-white/10 px-3 py-2">
            <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-primary-100">
              Bookings
            </HeroText>
            <HeroText className="mt-1 text-[16px] font-bold text-white">
              {playerBookings.length}
            </HeroText>
          </View>
        </View>
      </AppCard>

      <AppSection
        title="Your setup"
        subtitle="Used by Advisor and booking guidance."
        variant="compact"
      >
        <AppCard variant="default" padding="none" className="rounded-[14px]">
          {setupRows.map((row, rowIndex) => (
            <View
              key={rowIndex}
              className={`flex-row ${rowIndex > 0 ? 'border-t border-[#E7ECF2]' : ''}`}
            >
              {row.map((fact) => (
                <View key={fact.label} className="min-w-0 flex-1 px-3.5 py-3">
                  <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
                    {fact.label}
                  </HeroText>
                  <HeroText
                    className="mt-1 text-[14px] font-semibold leading-[18px] text-slate-900"
                    numberOfLines={2}
                  >
                    {fact.value}
                  </HeroText>
                </View>
              ))}
            </View>
          ))}
        </AppCard>
      </AppSection>

      <AppSection title="Your space" variant="compact">
        <AppCard variant="default" padding="none" className="rounded-[14px]">
          <ProfileActionRow
            icon={BadgeCheck}
            title="Racket passport"
            detail={`${playerRackets.length} saved ${playerRackets.length === 1 ? 'racket' : 'rackets'}`}
            onPress={() => router.push('/player/rackets')}
            first
          />
          <ProfileActionRow
            icon={CalendarDays}
            title="Bookings"
            detail={`${playerBookings.length} ${playerBookings.length === 1 ? 'service' : 'services'} in your history`}
            onPress={() => router.push('/player/bookings')}
          />
          <ProfileActionRow
            icon={WalletCards}
            title="Wallet"
            detail={`${formatCurrency(wallet?.availableBalance ?? 0)} available`}
            onPress={() => router.push('/player/wallet')}
          />
          <ProfileActionRow
            icon={Bell}
            title="Notifications"
            detail={
              unreadNotifications > 0
                ? `${unreadNotifications} unread update${unreadNotifications === 1 ? '' : 's'}`
                : 'No unread updates'
            }
            onPress={() => router.push('/player/notifications')}
          />
          <ProfileActionRow
            icon={LockKeyhole}
            title="Password & session"
            detail="Update your password or sign out"
            onPress={() => router.push('/player/settings')}
          />
        </AppCard>
      </AppSection>

      <AppButton
        label="Log out"
        variant="ghost"
        size="sm"
        leadingIcon={<LogOut size={17} color="#DC2626" />}
        textClassName="text-red-600 font-semibold"
        className="mb-3 mt-4 h-11 justify-start rounded-[10px] border border-red-100 bg-white px-3.5"
        onPress={() => {
          logout();
          router.replace('/auth/login');
        }}
      />
    </AppScreen>
  );
}
