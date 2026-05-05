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

  return (
    <AuthShell
      eyebrow="FYP demo access"
      title="Log in to StringSense"
      subtitle="Choose a workspace, then continue with a backend-backed login."
      footer={
        <View className="items-center gap-3">
          <Pressable onPress={() => router.push('/auth/register')}>
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
            onPress={() => router.push(`/auth/login?role=${role}`)}
            style={({ pressed }) => ({
              opacity: pressed ? 0.94 : 1,
              borderWidth: 1,
              borderColor: appChromeColors.border,
              borderRadius: 18,
              padding: 18,
              backgroundColor: appChromeColors.surface,
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
                      role === 'player' ? appChromeColors.primarySoftest : '#F5F5F7',
                  }}
                >
                  <Icon size={22} color={accentColor} />
                </View>
                <View className="min-w-0 flex-1" style={{ minWidth: 0, flex: 1 }}>
                  <HeroText
                    className="text-base font-bold tracking-normal text-[#1D1D1F]"
                    style={{ color: '#1D1D1F', fontSize: 16, fontWeight: '700' }}
                  >
                    {title}
                  </HeroText>
                  <HeroText
                    className="mt-1 text-sm leading-5 text-[rgba(29,29,31,0.62)]"
                    style={{
                      marginTop: 4,
                      color: 'rgba(29,29,31,0.62)',
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
                    backgroundColor: '#F5F5F7',
                  }}
                >
                  <ArrowRight size={15} color={appChromeColors.primary} strokeWidth={2} />
                </View>
              </View>
          </Pressable>
        ))}
      </View>

      <View className="mt-5 gap-3" style={{ gap: 12, marginTop: 20 }}>
        <Pressable
          onPress={() => router.push('/auth/login')}
          style={({ pressed }) => ({
            opacity: pressed ? 0.92 : 1,
            minHeight: 52,
            borderRadius: 14,
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'row',
            gap: 8,
            backgroundColor: appChromeColors.primary,
          })}
        >
          <HeroText style={{ color: 'white', fontSize: 16, fontWeight: '700' }}>
            Continue to login
          </HeroText>
          <ArrowRight size={16} color="white" strokeWidth={1.8} />
        </Pressable>
        <View className="items-center" style={{ alignItems: 'center' }}>
          <HeroText
            style={{
              borderRadius: 999,
              paddingHorizontal: 12,
              paddingVertical: 7,
              overflow: 'hidden',
              color: appChromeColors.textSecondary,
              backgroundColor: appChromeColors.surfaceMuted,
              fontSize: 12,
              fontWeight: '600',
            }}
          >
            Player and admin backend accounts are pre-configured
          </HeroText>
        </View>
      </View>
    </AuthShell>
  );
}
