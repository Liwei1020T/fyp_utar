import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, Building2, Sparkles } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { HeroText } from '../../components/ui/heroui';
import { appChromeColors } from '../../components/ui/theme';
import { useAppStore } from '../../store/appStore';

const roleCards = [
  {
    role: 'player',
    title: 'Player demo',
    description: 'Recommendations, bookings, tracking, and profile',
    icon: Sparkles,
    accentClassName: 'bg-primary-50',
    accentColor: appChromeColors.primary,
  },
  {
    role: 'admin',
    title: 'Admin demo',
    description: 'Bookings, inventory, business hours, and store settings',
    icon: Building2,
    accentClassName: 'bg-[#F5F5F7]',
    accentColor: appChromeColors.textPrimary,
  },
] as const;

export default function WelcomeScreen() {
  const router = useRouter();
  const loginAsUser = useAppStore((state) => state.loginAsUser);

  return (
    <AuthShell
      eyebrow="FYP demo access"
      title="Log in to StringSense"
      subtitle="Choose a demo workspace to continue with the mobile app."
      footer={
        <View className="items-center gap-3">
          <Pressable onPress={() => router.push('/auth/register')}>
            <HeroText className="text-sm font-semibold text-primary-700">
              New player? Create an account
            </HeroText>
          </Pressable>
          <Pressable
            onPress={() => {
              loginAsUser('player-001');
              router.replace('/player');
            }}
          >
            <HeroText className="text-sm text-neutral-500">
              Quick demo as player
            </HeroText>
          </Pressable>
        </View>
      }
    >
      <View className="gap-3">
        {roleCards.map(({ role, title, description, icon: Icon, accentClassName, accentColor }) => (
          <Pressable key={role} onPress={() => router.push(`/auth/login?role=${role}`)}>
            <AppCard variant="default" padding="md">
              <View className="flex-row items-center gap-4">
                <View className={`h-12 w-12 items-center justify-center rounded-lg ${accentClassName}`}>
                  <Icon size={22} color={accentColor} />
                </View>
                <View className="min-w-0 flex-1">
                  <HeroText className="text-base font-bold tracking-normal text-[#1D1D1F]">
                    {title}
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-5 text-[rgba(29,29,31,0.62)]">
                    {description}
                  </HeroText>
                </View>
                <View className="h-8 w-8 items-center justify-center rounded-full bg-[#F5F5F7]">
                  <ArrowRight size={15} color={appChromeColors.primary} strokeWidth={2} />
                </View>
              </View>
            </AppCard>
          </Pressable>
        ))}
      </View>

      <View className="mt-5 gap-3">
        <AppButton
          label="Continue to login"
          size="lg"
          trailingIcon={<ArrowRight size={16} color="white" strokeWidth={1.8} />}
          onPress={() => router.push('/auth/login')}
        />
        <View className="items-center">
          <AppChip
            label="Player and admin demo accounts are pre-configured"
            variant="neutral"
          />
        </View>
      </View>
    </AuthShell>
  );
}
