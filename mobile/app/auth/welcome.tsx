import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, Building2, Sparkles } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { HeroText } from '../../components/ui/heroui';
import { useAppStore } from '../../store/appStore';

const roleCards = [
  {
    role: 'player',
    title: 'Player demo',
    description: 'Recommendations, bookings, tracking, and profile.',
    icon: Sparkles,
    accentClassName: 'bg-[#DCE8F6]',
    accentColor: '#2F64B6',
  },
  {
    role: 'admin',
    title: 'Admin demo',
    description: 'Bookings, inventory, business hours, and store settings.',
    icon: Building2,
    accentClassName: 'bg-[#E2F1EF]',
    accentColor: '#22766D',
  },
] as const;

export default function WelcomeScreen() {
  const router = useRouter();
  const loginAsUser = useAppStore((state) => state.loginAsUser);

  return (
    <AuthShell
      eyebrow="FYP demo access"
      title="Choose a role and continue"
      subtitle="One clean entry point for the player journey and the shop admin workspace."
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
            <AppCard variant="subtle" padding="md">
              <View className="flex-row items-center gap-4">
                <View className={`h-12 w-12 items-center justify-center rounded-[18px] ${accentClassName}`}>
                  <Icon size={22} color={accentColor} />
                </View>
                <View className="flex-1">
                  <HeroText className="text-base font-bold tracking-tight text-neutral-950">
                    {title}
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
                    {description}
                  </HeroText>
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
