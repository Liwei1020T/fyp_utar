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
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { useAppStore } from '../../store/appStore';
import { getRoleHome } from '../../lib/navigation';
import { BackendApiError, backendApi } from '../../services/backendApi';
import {
  mapBackendUserToAdminProfile,
  mapBackendUserToPlayerProfile,
} from '../../services/backendMappers';

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

export default function LoginScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ identifier?: string }>();
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const setBackendAdminSession = useAppStore(
    (state) => state.setBackendAdminSession,
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

      if (auth.role === 'admin') {
        setBackendAdminSession({
          accessToken: auth.access_token,
          admin: mapBackendUserToAdminProfile(auth.user),
        });
        router.replace(getRoleHome('admin') as never);
        return;
      }

      if (auth.role !== 'customer') {
        setFormError('This account type is not supported by the mobile app.');
        return;
      }

      const profile = await backendApi.fetchProfile(auth.access_token);

      setBackendPlayerSession({
        accessToken: auth.access_token,
        player: mapBackendUserToPlayerProfile(auth.user, profile),
      });

      router.replace(
        (profile ? '/player' : '/player/profile/edit?onboarding=1') as never,
      );
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
      title="Welcome back"
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
        <Controller
          control={control}
          name="phoneNumber"
          render={({ field: { onChange, value } }) => (
            <PhoneNumberField
              countryCode={countryCodeValue}
              value={value}
              onChangePhoneNumber={(nextValue) => {
                onChange(nextValue);
                setFormError(null);
              }}
              onChangeCountryCode={(nextCode) =>
                setValue('countryCode', nextCode, { shouldValidate: true })
              }
              placeholder="123456789"
              error={
                errors.countryCode?.message ??
                errors.phoneNumber?.message
              }
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
              onChangeText={(nextValue) => {
                onChange(nextValue);
                setFormError(null);
              }}
              error={errors.password?.message}
              leftAdornment={<LockKeyhole size={18} color="#64748B" />}
            />
          )}
        />

        {formError ? (
          <HeroText
            accessibilityLiveRegion="polite"
            className="text-sm font-medium leading-5 text-red-600"
          >
            {formError}
          </HeroText>
        ) : null}

        <AppButton
          label="Sign in"
          size="lg"
          onPress={handleSubmit(onSubmit)}
          isLoading={isSubmitting}
        />

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
            Forgot player password?
          </HeroText>
        </Pressable>
      </View>
    </AuthShell>
  );
}
