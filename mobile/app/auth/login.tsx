import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { ChevronLeft, LockKeyhole, Mail, Sparkles } from 'lucide-react-native';
import { HeroText } from '../../components/ui/heroui';
import { AppButton } from '../../components/ui/AppButton';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { useAppStore } from '../../store/appStore';
import { getRoleHome } from '../../lib/navigation';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendUserToPlayerProfile } from '../../services/backendMappers';
import type { UserRole } from '../../types/domain';

const loginSchema = z.object({
  identifier: z.string().min(3, 'Enter your email or phone number'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginForm = z.infer<typeof loginSchema>;

const demoUsers: Array<{ role: UserRole; label: string; email: string; description: string }> = [
  { role: 'player', label: 'Player', email: '+60123456789', description: 'Phone login for the live player backend flow.' },
  { role: 'vendor', label: 'Vendor', email: 'vendor@example.com', description: 'Shop operations, inventory, queue, and support flow.' },
];

export default function LoginScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ role?: UserRole; identifier?: string }>();
  const login = useAppStore((state) => state.login);
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const [selectedRole, setSelectedRole] = useState<UserRole>(params.role ?? 'player');
  const [formError, setFormError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      identifier: '',
      password: '',
    },
  });

  const activeDemo = useMemo(
    () => demoUsers.find((item) => item.role === selectedRole) ?? demoUsers[0],
    [selectedRole]
  );
  const identifierValue = watch('identifier');

  useEffect(() => {
    setValue('identifier', params.identifier ?? activeDemo.email);
    setValue('password', activeDemo.role === 'vendor' ? 'password' : '');
  }, [activeDemo.email, activeDemo.role, params.identifier, setValue]);

  const onSubmit = async (data: LoginForm) => {
    setFormError(null);
    await new Promise((resolve) => setTimeout(resolve, 450));
    if (selectedRole === 'vendor') {
      const role = login(data.identifier);

      if (!role) {
        setFormError('No mock user matched that email. Use one of the demo accounts below.');
        return;
      }

      router.replace(getRoleHome(role) as never);
      return;
    }

    try {
      const auth = await backendApi.loginPlayer({
        phone_number: data.identifier,
        password: data.password,
      });
      const profile = await backendApi.fetchProfile(auth.access_token).catch(() => null);

      setBackendPlayerSession({
        accessToken: auth.access_token,
        player: mapBackendUserToPlayerProfile(auth.user, profile),
      });

      router.replace((profile ? '/player' : '/player/profile/edit') as never);
    } catch (error) {
      setFormError(
        error instanceof BackendApiError
          ? error.message
          : 'Login failed. Please try again.',
      );
    }
  };

  return (
    <AppScreen
      tone="auth"
      eyebrow="Mock Access"
      title="Log in"
      subtitle="Use the player demo or the pre-created vendor account to open the correct role surface."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#122018" />}
          accessibilityLabel="Go back"
          variant="auth"
          onPress={() => router.back()}
        />
      }
    >
      <View className="rounded-[32px] border border-[#D9E5F1] bg-white px-5 py-6 shadow-soft">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#6B7C70]">
              Role-based access
            </HeroText>
            <HeroText className="mt-2 text-[27px] font-bold tracking-tight text-[#122018]">
              Open the right prototype area in one step.
            </HeroText>
            <HeroText className="mt-3 text-sm leading-6 text-[#607266]">
              Public registration is only for players. The vendor account is pre-created for the single-store prototype.
            </HeroText>
          </View>
          <View className="h-14 w-14 items-center justify-center rounded-[22px] bg-[#E1EDF9]">
            <Sparkles size={22} color="#2F64B6" />
          </View>
        </View>

        <View className="mt-6 flex-row flex-wrap gap-2">
          {demoUsers.map((item) => (
            <AppChip
              key={item.role}
              label={item.label}
              variant={selectedRole === item.role ? 'primary' : 'neutral'}
              size="md"
              onPress={() => setSelectedRole(item.role)}
            />
          ))}
        </View>
      </View>

      <View className="mt-6 rounded-[32px] border border-[#D9E5F1] bg-white p-5 shadow-soft">
        <Controller
          control={control}
          name="identifier"
          render={({ field: { onChange, value } }) => (
            <AppInput
              label={selectedRole === 'player' ? 'Phone number' : 'Email address'}
              placeholder={
                selectedRole === 'player'
                  ? 'e.g. +60123456789'
                  : 'e.g. vendor@example.com'
              }
              keyboardType={
                selectedRole === 'player' ? 'phone-pad' : 'email-address'
              }
              value={value}
              onChangeText={onChange}
              error={errors.identifier?.message}
              helperText={
                formError ??
                (selectedRole === 'player'
                  ? 'Players now sign in against the live Python backend.'
                  : `Demo ${activeDemo.label.toLowerCase()} account is prefilled.`)
              }
              leftAdornment={<Mail size={18} color="#64748B" />}
            />
          )}
        />

        <Controller
          control={control}
          name="password"
          render={({ field: { onChange, value } }) => (
            <AppInput
              label="Password"
              placeholder="password"
              secureTextEntry
              value={value}
              onChangeText={onChange}
              error={errors.password?.message}
              helperText={
                selectedRole === 'player'
                  ? 'Use the password from your live player account.'
                  : 'Vendor continues to use the mock prototype login.'
              }
              leftAdornment={<LockKeyhole size={18} color="#64748B" />}
            />
          )}
        />

        <AppButton
          label="Sign in"
          size="lg"
          className="border-[#2F64B6] bg-[#2F64B6] shadow-float"
          onPress={handleSubmit(onSubmit)}
          isLoading={isSubmitting}
        />

        {selectedRole === 'player' ? (
          <Pressable
            className="mt-4 self-end"
            onPress={() =>
              router.push(
                `/auth/forgot-password?identifier=${encodeURIComponent(
                  identifierValue || '',
                )}`,
              )
            }
          >
            <HeroText className="text-sm font-semibold text-[#254E90]">
              Forgot password?
            </HeroText>
          </Pressable>
        ) : null}

        <View className="mt-5 gap-3">
          {demoUsers.map((item) => (
            <Pressable
              key={item.role}
              onPress={() => {
                setSelectedRole(item.role);
                setValue('identifier', item.email);
              }}
            >
              <AppCard variant="subtle" padding="sm">
                <View className="flex-row items-center justify-between gap-4">
                  <View className="flex-1">
                    <HeroText className="text-sm font-semibold text-neutral-900">
                      {item.label} demo
                    </HeroText>
                    <HeroText className="mt-1 text-xs leading-5 text-neutral-500">
                      {item.description}
                    </HeroText>
                  </View>
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-700">
                    {item.email}
                  </HeroText>
                </View>
              </AppCard>
            </Pressable>
          ))}
        </View>
      </View>

      <View className="mt-7 flex-row justify-center pb-6">
        <HeroText className="text-[#607266]">Need a player account? </HeroText>
        <Pressable onPress={() => router.push('/auth/register')}>
          <HeroText className="font-semibold text-[#254E90]">Create account</HeroText>
        </Pressable>
      </View>
    </AppScreen>
  );
}
