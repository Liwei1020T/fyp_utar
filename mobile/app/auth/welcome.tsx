import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight, Building2, Sparkles } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import { HeroText } from '../../components/ui/heroui';
import { appChromeColors } from '../../components/ui/theme';

const roleCards = [
  {
    role: 'player',
    title: 'Player workspace',
    description: 'Recommendations, bookings, tracking, and profile',
    icon: Sparkles,
    accentClassName: 'bg-primary-50',
    accentColor: appChromeColors.primary,
  },
  {
    role: 'admin',
    title: 'Admin workspace',
    description: 'Bookings, inventory, business hours, and store settings',
    icon: Building2,
    accentClassName: 'bg-[#F5F5F7]',
    accentColor: appChromeColors.textPrimary,
  },
] as const;

export default function WelcomeScreen() {
  const router = useRouter();

  return (
    <AuthShell
      eyebrow="Secure workspace access"
      title="Choose your workspace"
      subtitle="Open the player experience or the store operations workspace."
      footer={
        <View className="items-center gap-3">
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Create a player account"
            className="min-h-11 justify-center"
            onPress={() => router.push('/auth/register')}
          >
            <HeroText className="text-sm font-semibold text-primary-700">
              New player? Create an account
            </HeroText>
          </Pressable>
        </View>
      }
    >
      <View className="gap-3" style={{ gap: 12 }}>
        {roleCards.map(({ role, title, description, icon: Icon, accentClassName, accentColor }) => (
          <Pressable
            key={role}
            accessibilityRole="button"
            accessibilityLabel={`${title}. ${description}`}
            accessibilityHint={`Continue to ${role} login`}
            onPress={() => router.push(`/auth/login?role=${role}`)}
            style={({ pressed }) => ({
              opacity: pressed ? 0.94 : 1,
              borderWidth: 1,
              borderColor: role === 'player' ? appChromeColors.hero : appChromeColors.border,
              borderRadius: 20,
              padding: 18,
              backgroundColor:
                role === 'player' ? appChromeColors.hero : appChromeColors.surface,
            })}
          >
              <View className="flex-row items-center gap-4">
                <View
                  className={`h-12 w-12 items-center justify-center rounded-lg ${accentClassName}`}
                  style={{
                    width: 48,
                    height: 48,
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 12,
                    backgroundColor:
                      role === 'player' ? 'rgba(255,255,255,0.12)' : '#F5F5F7',
                  }}
                >
                  <Icon
                    size={22}
                    color={role === 'player' ? '#FFFFFF' : accentColor}
                  />
                </View>
                <View className="min-w-0 flex-1" style={{ minWidth: 0, flex: 1 }}>
                  <HeroText
                    className="text-base font-bold tracking-normal"
                    style={{
                      color: role === 'player' ? '#FFFFFF' : '#1D1D1F',
                      fontSize: 16,
                      fontWeight: '700',
                    }}
                  >
                    {title}
                  </HeroText>
                  <HeroText
                    className="mt-1 text-sm leading-5"
                    style={{
                      marginTop: 4,
                      color:
                        role === 'player' ? appChromeColors.heroMuted : 'rgba(29,29,31,0.62)',
                      fontSize: 14,
                      lineHeight: 20,
                    }}
                  >
                    {description}
                  </HeroText>
                </View>
                <View
                  className="h-8 w-8 items-center justify-center rounded-full bg-[#F5F5F7]"
                  style={{
                    width: 32,
                    height: 32,
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 16,
                    backgroundColor:
                      role === 'player' ? 'rgba(255,255,255,0.12)' : '#F5F5F7',
                  }}
                >
                  <ArrowRight
                    size={15}
                    color={role === 'player' ? '#FFFFFF' : appChromeColors.primary}
                    strokeWidth={2}
                  />
                </View>
              </View>
          </Pressable>
        ))}
      </View>

      <View className="mt-4 border-t border-[#D8E0EA] pt-4">
        <HeroText className="text-center text-[12px] leading-[18px] text-slate-600">
          Player registration is open. Admin accounts are configured by the store operator.
        </HeroText>
      </View>
    </AuthShell>
  );
}
