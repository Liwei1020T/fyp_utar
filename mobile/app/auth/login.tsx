import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { LockKeyhole, Mail } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
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
  {
    role: 'player',
    label: 'Player',
    email: '+60123456789',
    description: 'Use your phone-based player login.',
  },
  {
    role: 'admin',
    label: 'Admin',
    email: 'admin@example.com',
    description: 'Open the shop operations workspace.',
  },
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
    setValue('password', activeDemo.role === 'admin' ? 'password' : '');
  }, [activeDemo.email, activeDemo.role, params.identifier, setValue]);

  const onSubmit = async (data: LoginForm) => {
    setFormError(null);
    await new Promise((resolve) => setTimeout(resolve, 250));

    if (selectedRole === 'admin') {
      const role = login(data.identifier);

      if (!role) {
        setFormError('Use the pre-filled admin demo account to continue.');
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
    <AuthShell
      eyebrow={selectedRole === 'player' ? 'Player access' : 'Admin access'}
      title="Log in"
      subtitle={
        selectedRole === 'player'
          ? 'Use your phone and password to open the player flow.'
          : 'Use the pre-filled admin account to enter the operations workspace.'
      }
      onBack={() => router.back()}
      footer={
        <View className="items-center gap-3">
          <Pressable onPress={() => router.push('/auth/register')}>
            <HeroText className="text-sm font-semibold text-primary-700">
              Need a player account? Create one
            </HeroText>
          </Pressable>
        </View>
      }
    >
      <View className="gap-4">
        <View className="gap-3">
          <View className="flex-row gap-2">
            {demoUsers.map((item) => (
              <AppChip
                key={item.role}
                label={item.label}
                size="md"
                variant={selectedRole === item.role ? 'primary' : 'neutral'}
                onPress={() => setSelectedRole(item.role)}
              />
            ))}
          </View>
          <HeroText className="text-sm leading-5 text-neutral-500">
            {activeDemo.description}
          </HeroText>
        </View>

        <Controller
          control={control}
          name="identifier"
          render={({ field: { onChange, value } }) => (
            <AppInput
              label={selectedRole === 'player' ? 'Phone number' : 'Email address'}
              placeholder={
                selectedRole === 'player'
                  ? 'e.g. +60123456789'
                  : 'e.g. admin@example.com'
              }
              keyboardType={selectedRole === 'player' ? 'phone-pad' : 'email-address'}
              value={value}
              onChangeText={onChange}
              error={errors.identifier?.message}
              helperText={
                formError
                  ?? (selectedRole === 'player'
                    ? 'Player accounts authenticate against the live backend.'
                    : 'Admin access stays mock-first for the demo.')
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
                  ? 'Use the password from your player account.'
                  : 'The admin demo password is already filled in.'
              }
              leftAdornment={<LockKeyhole size={18} color="#64748B" />}
            />
          )}
        />

        <AppButton
          label="Sign in"
          size="lg"
          onPress={handleSubmit(onSubmit)}
          isLoading={isSubmitting}
        />

        {selectedRole === 'player' ? (
          <Pressable
            className="self-end"
            onPress={() =>
              router.push(
                `/auth/forgot-password?identifier=${encodeURIComponent(
                  identifierValue || '',
                )}`,
              )
            }
          >
            <HeroText className="text-sm font-semibold text-primary-700">
              Forgot password?
            </HeroText>
          </Pressable>
        ) : null}

        <View className="gap-2">
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
                    <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
                      {item.description}
                    </HeroText>
                  </View>
                  <HeroText className="text-xs font-semibold text-primary-700">
                    {item.email}
                  </HeroText>
                </View>
              </AppCard>
            </Pressable>
          ))}
        </View>
      </View>
    </AuthShell>
  );
}
