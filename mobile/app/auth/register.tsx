import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { LockKeyhole, UserRound } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import {
  composePhoneIdentifier,
  countryDialCodes,
  PhoneNumberField,
} from '../../components/auth/PhoneNumberField';
import { AppButton } from '../../components/ui/AppButton';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { useAppStore } from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendUserToPlayerProfile } from '../../services/backendMappers';

const registerSchema = z
  .object({
    username: z.string().min(3, 'Username must be at least 3 characters'),
    countryCode: z.string().min(2, 'Choose a country code'),
    phoneNumber: z
      .string()
      .trim()
      .min(7, 'Enter your phone number')
      .regex(/^\d[\d\s-]*$/, 'Use numbers only'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Za-z]/, 'Password must include at least one letter')
      .regex(/\d/, 'Password must include at least one number'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterScreen() {
  const router = useRouter();
  const setBackendPlayerSession = useAppStore(
    (state) => state.setBackendPlayerSession,
  );
  const [formError, setFormError] = React.useState<string | null>(null);
  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      countryCode: countryDialCodes[0].value,
      phoneNumber: '',
      password: '',
      confirmPassword: '',
    },
  });
  const countryCodeValue = watch('countryCode');

  const onSubmit = async (data: RegisterForm) => {
    setFormError(null);
    try {
      const auth = await backendApi.registerPlayer({
        username: data.username,
        phone_number: composePhoneIdentifier(data.countryCode, data.phoneNumber),
        password: data.password,
      });

      setBackendPlayerSession({
        accessToken: auth.access_token,
        player: mapBackendUserToPlayerProfile(auth.user, null),
      });

      router.replace('/player/profile/edit');
    } catch (error) {
      setFormError(
        error instanceof BackendApiError
          ? error.message
          : 'Registration failed. Please try again.',
      );
    }
  };

  return (
    <AuthShell
      eyebrow="New player"
      title="Create your account"
      subtitle="Set up a player login and continue straight into your profile."
      onBack={() => {
        if (router.canGoBack()) {
          router.back();
        } else {
          router.replace('/auth/welcome');
        }
      }}
      footer={
        <View className="items-center">
          <Pressable onPress={() => router.push('/auth/login')}>
            <HeroText className="text-sm font-semibold text-primary-700">
              Already have an account? Log in
            </HeroText>
          </Pressable>
        </View>
      }
    >
      <Controller
        control={control}
        name="username"
        render={({ field: { onChange, value } }) => (
          <AppInput
            label="Username"
            placeholder="e.g. SmashMaster"
            value={value}
            onChangeText={onChange}
            error={errors.username?.message}
            leftAdornment={<UserRound size={18} color="#64748B" />}
          />
        )}
      />

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
            placeholder="123456789"
            error={
              errors.countryCode?.message ??
              errors.phoneNumber?.message ??
              formError
            }
            helperText={`We will create your account with ${composePhoneIdentifier(
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
            placeholder="Minimum 8 characters"
            secureTextEntry
            value={value}
            onChangeText={onChange}
            error={errors.password?.message}
            helperText={
              'Use at least 8 characters with at least one letter and one number.'
            }
            leftAdornment={<LockKeyhole size={18} color="#64748B" />}
          />
        )}
      />

      <Controller
        control={control}
        name="confirmPassword"
        render={({ field: { onChange, value } }) => (
          <AppInput
            label="Confirm password"
            placeholder="Repeat your password"
            secureTextEntry
            value={value}
            onChangeText={onChange}
            error={errors.confirmPassword?.message}
            leftAdornment={<LockKeyhole size={18} color="#64748B" />}
          />
        )}
      />

      <AppButton
        label="Create account"
        size="lg"
        className="mt-2"
        onPress={handleSubmit(onSubmit)}
        isLoading={isSubmitting}
      />
    </AuthShell>
  );
}
