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
import {
  mapBackendUserToAdminProfile,
  mapBackendUserToPlayerProfile,
} from '../../services/backendMappers';
import type { UserRole } from '../../types/domain';

const loginSchema = z.object({
  identifier: z.string().min(3, 'Enter your email or phone number'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginForm = z.infer<typeof loginSchema>;

const demoUsers: Array<{
  role: UserRole;
  label: string;
  identifier: string;
  password: string;
  description: string;
}> = [
  {
    role: 'player',
    label: 'Player',
    identifier: '+60123456789',
    password: 'password',
    description: 'Use your phone-based player login.',
  },
  {
    role: 'admin',
    label: 'Admin',
    identifier: '+60190000000',
    password: 'admin1234',
    description: 'Use the seeded backend admin login for shop operations.',
  },
];

export default function LoginScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ role?: UserRole; identifier?: string }>();
  const login = useAppStore((state) => state.login);
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const setBackendAdminSession = useAppStore(
    (state) => state.setBackendAdminSession,
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
    setValue('identifier', params.identifier ?? activeDemo.identifier);
    setValue('password', activeDemo.password);
  }, [activeDemo.identifier, activeDemo.password, params.identifier, setValue]);

  const onSubmit = async (data: LoginForm) => {
    setFormError(null);
    await new Promise((resolve) => setTimeout(resolve, 250));

    try {
      const auth = await backendApi.login({
        phone_number: data.identifier,
        password: data.password,
      });

      if (selectedRole === 'admin') {
        if (auth.role !== 'admin') {
          setFormError('This account is not an admin account.');
          return;
        }

        setBackendAdminSession({
          accessToken: auth.access_token,
          admin: mapBackendUserToAdminProfile(auth.user),
        });
        router.replace(getRoleHome('admin') as never);
        return;
      }

      if (auth.role !== 'customer') {
        setFormError('This account is not a player account.');
        return;
      }

      const profile = await backendApi.fetchProfile(auth.access_token).catch(() => null);

      setBackendPlayerSession({
        accessToken: auth.access_token,
        player: mapBackendUserToPlayerProfile(auth.user, profile),
      });

      router.replace((profile ? '/player' : '/player/profile/edit') as never);
    } catch (error) {
      if (selectedRole === 'admin') {
        const role = login(data.identifier);
        if (role === 'admin') {
          router.replace(getRoleHome(role) as never);
          return;
        }
      }

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
          : 'Use the seeded backend admin phone and password to enter the operations workspace.'
      }
      onBack={() => {
        if (router.canGoBack()) {
          router.back();
        } else {
          router.replace('/auth/welcome');
        }
      }}
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
              label="Phone number"
              placeholder={
                selectedRole === 'player'
                  ? 'e.g. +60123456789'
                  : 'e.g. +60190000000'
              }
              keyboardType="phone-pad"
              value={value}
              onChangeText={onChange}
              error={errors.identifier?.message}
              helperText={
                formError
                  ?? (selectedRole === 'player'
                    ? 'Player accounts authenticate against the live backend.'
                    : 'Admin accounts authenticate against the live backend.')
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
                  : 'Use the seeded admin password from the backend environment.'
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
                setValue('identifier', item.identifier);
                setValue('password', item.password);
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
                    {item.identifier}
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
