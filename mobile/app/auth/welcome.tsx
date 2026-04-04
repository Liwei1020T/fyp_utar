import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Activity, ArrowRight, Building2, CalendarClock, Sparkles, UsersRound } from 'lucide-react-native';
import { HeroText } from '../../components/ui/heroui';
import { AppButton } from '../../components/ui/AppButton';
import { AppChip } from '../../components/ui/AppChip';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppCard } from '../../components/ui/AppCard';
import { useAppStore } from '../../store/appStore';

const roleCards = [
  {
    role: 'player',
    title: 'Player',
    description: 'Recommendations, bookings, payments, tracking, chat, rackets, and feedback.',
    icon: Sparkles,
    accent: '#2F64B6',
    surface: 'bg-[#E1EDF9]',
    email: 'player@example.com',
  },
  {
    role: 'admin',
    title: 'Admin',
    description: 'Shop dashboard, service queue, drop-off flow, inventory, support, and store analytics.',
    icon: Building2,
    accent: '#22766D',
    surface: 'bg-[#E4F2F0]',
    email: 'admin@example.com',
  },
] as const;

export default function WelcomeScreen() {
  const router = useRouter();
  const loginAsUser = useAppStore((state) => state.loginAsUser);

  return (
    <AppScreen tone="auth" contentContainerClassName="justify-between">
      <View>
        <View className="mt-3 rounded-[32px] border border-[#D9E5F1] bg-white px-5 py-6 shadow-soft">
          <View className="h-12 w-12 items-center justify-center rounded-[20px] bg-[#E1EDF9]">
            <Activity color="#2F64B6" size={24} />
          </View>

          <AppChip
            label="STRINGSENSE FYP 1 PROTOTYPE"
            variant="secondary"
            className="mt-5 self-start border-[#F0DFB8] bg-[#FBF2DE]"
          />

          <HeroText className="mt-4 text-[30px] font-bold leading-[36px] tracking-tight text-[#122018]">
            Premium frontend prototype for one badminton stringing shop.
          </HeroText>

          <HeroText className="mt-3 text-[14px] leading-6 text-[#496153]">
            Explore the complete player journey and the shop admin workspace from one polished Expo Router build.
          </HeroText>

          <View className="mt-6 gap-2.5">
            <View className="flex-row items-start gap-3 rounded-[22px] border border-[#E5ECE6] bg-[#FAFCFA] px-3.5 py-3.5">
              <View className="h-10 w-10 items-center justify-center rounded-[16px] bg-[#E1EDF9]">
                <CalendarClock color="#2F64B6" size={18} />
              </View>
              <View className="flex-1">
                <HeroText className="text-[15px] font-semibold tracking-tight text-[#122018]">
                  Booking and payment flow
                </HeroText>
                <HeroText className="mt-1 text-[13px] leading-5 text-[#607266]">
                  Drop-off scheduling, booking summary, full-payment flow, service tracking, and QR check-in.
                </HeroText>
              </View>
            </View>
            <View className="flex-row items-start gap-3 rounded-[22px] border border-[#E5ECE6] bg-[#FAFCFA] px-3.5 py-3.5">
              <View className="h-10 w-10 items-center justify-center rounded-[16px] bg-[#EDF4EA]">
                <UsersRound color="#22766D" size={18} />
              </View>
              <View className="flex-1">
                <HeroText className="text-[15px] font-semibold tracking-tight text-[#122018]">
                  Role-based product surfaces
                </HeroText>
                <HeroText className="mt-1 text-[13px] leading-5 text-[#607266]">
                  Player and admin areas are separated and guarded with mock session routing for the single-store flow.
                </HeroText>
              </View>
            </View>
          </View>
        </View>

        <View className="mt-6 gap-3">
          {roleCards.map(({ role, title, description, icon: Icon, accent, surface, email }) => (
            <Pressable key={role} onPress={() => router.push(`/auth/login?role=${role}`)}>
              <AppCard variant="elevated" padding="md">
                <View className="flex-row items-start gap-4">
                  <View className={`h-12 w-12 items-center justify-center rounded-[18px] ${surface}`}>
                    <Icon color={accent} size={22} />
                  </View>
                  <View className="flex-1">
                    <View className="flex-row items-center justify-between">
                      <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                        {title} demo
                      </HeroText>
                      <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
                        {email}
                      </HeroText>
                    </View>
                    <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
                      {description}
                    </HeroText>
                  </View>
                </View>
              </AppCard>
            </Pressable>
          ))}
        </View>
      </View>

      <View className="pt-6">
        <AppButton
          label="Continue to login"
          size="lg"
          className="border-[#2F64B6] bg-[#2F64B6] shadow-float"
          trailingIcon={<ArrowRight size={16} color="white" strokeWidth={1.8} />}
          onPress={() => router.push('/auth/login')}
        />

        <Pressable className="mt-5 items-center" onPress={() => router.push('/auth/register')}>
          <HeroText className="text-sm font-semibold text-[#254E90]">
            New player? Create an account
          </HeroText>
        </Pressable>

        <Pressable
          className="mt-4 items-center"
          onPress={() => {
            loginAsUser('player-001');
            router.replace('/player');
          }}
        >
          <HeroText className="text-sm font-medium text-[#6B7C70]">
            Quick demo as player
          </HeroText>
        </Pressable>

        <HeroText className="mt-6 text-center text-[11px] uppercase tracking-[0.16em] text-[#869588]">
          frontend-only • mock data • expo router • fyp 2026
        </HeroText>
      </View>
    </AppScreen>
  );
}
