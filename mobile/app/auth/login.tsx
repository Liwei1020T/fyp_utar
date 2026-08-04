import React, { useEffect, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { LockKeyhole } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import {
  composePhoneIdentifier,
  countryDialCodes,
  PhoneNumberField,
  splitPhoneIdentifier,
} from '../../components/auth/PhoneNumberField';
import { AppButton } from '../../components/ui/AppButton';
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
  countryCode: z.string().min(2, 'Choose a country code'),
  phoneNumber: z
    .string()
    .trim()
    .min(7, 'Enter your phone number')
    .regex(/^\d[\d\s-]*$/, 'Use numbers only'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginForm = z.infer<typeof loginSchema>;

const roleOptions: {
  role: UserRole;
  label: string;
  description: string;
}[] = [
  {
    role: 'player',
    label: 'Player',
    description: 'Use the phone number and password from your registered player account.',
  },
  {
    role: 'admin',
    label: 'Admin',
    description: 'Use an admin account configured by the backend operator.',
  },
];

export default function LoginScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ role?: UserRole; identifier?: string }>();
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const setBackendAdminSession = useAppStore(
    (state) => state.setBackendAdminSession,
  );
  const [selectedRole, setSelectedRole] = useState<UserRole>(
    params.role === 'admin' ? 'admin' : 'player',
  );
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
      countryCode: countryDialCodes[0].value,
      phoneNumber: '',
      password: '',
    },
  });

  const activeRole =
    roleOptions.find((item) => item.role === selectedRole) ?? roleOptions[0];
  const countryCodeValue = watch('countryCode');
  const phoneNumberValue = watch('phoneNumber');
  const identifierValue = composePhoneIdentifier(countryCodeValue, phoneNumberValue);

  useEffect(() => {
    if (!params.identifier) {
      return;
    }
    const phoneParts = splitPhoneIdentifier(params.identifier);
    setValue('countryCode', phoneParts.countryCode);
    setValue('phoneNumber', phoneParts.phoneNumber);
  }, [params.identifier, setValue]);

  const onSubmit = async (data: LoginForm) => {
    setFormError(null);
    const phoneIdentifier = composePhoneIdentifier(data.countryCode, data.phoneNumber);

    try {
      const auth = await backendApi.login({
        phone_number: phoneIdentifier,
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

      const profile = await backendApi.fetchProfile(auth.access_token);

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
          : 'Use your backend-configured admin phone and password to enter the operations workspace.'
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
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Create a player account"
            className="min-h-11 justify-center"
            onPress={() => router.push('/auth/register')}
          >
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
            {roleOptions.map((item) => (
              <AppChip
                key={item.role}
                label={item.label}
                size="md"
                variant={selectedRole === item.role ? 'primary' : 'neutral'}
                accessibilityState={{ selected: selectedRole === item.role }}
                onPress={() => {
                  setSelectedRole(item.role);
                  setFormError(null);
                  setValue('phoneNumber', '');
                  setValue('password', '');
                }}
              />
            ))}
          </View>
          <HeroText className="text-sm leading-5 text-neutral-500">
            {activeRole.description}
          </HeroText>
        </View>

        <Controller
          control={control}
          name="phoneNumber"
          render={({ field: { onChange, value } }) => (
            <PhoneNumberField
              countryCode={countryCodeValue}
              value={value}
              onChangePhoneNumber={onChange}
              onChangeCountryCode={(nextCode) =>
                setValue('countryCode', nextCode, { shouldValidate: true })
              }
              placeholder={selectedRole === 'player' ? '123456789' : '190000000'}
              error={
                errors.countryCode?.message ??
                errors.phoneNumber?.message ??
                formError
              }
              helperText={`We will sign in with ${composePhoneIdentifier(
                countryCodeValue,
                value || '',
              )}.`}
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
                  : 'Use the admin password configured by the backend operator.'
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
            accessibilityRole="button"
            accessibilityLabel="Reset player password"
            className="min-h-11 self-end justify-center"
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

      </View>
    </AuthShell>
  );
}
