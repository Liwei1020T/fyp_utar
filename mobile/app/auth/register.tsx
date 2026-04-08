import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { LockKeyhole, Smartphone, UserRound } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import { AppButton } from '../../components/ui/AppButton';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { useAppStore } from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendUserToPlayerProfile } from '../../services/backendMappers';

const registerSchema = z
  .object({
    username: z.string().min(3, 'Username must be at least 3 characters'),
    phoneNumber: z.string().min(9, 'Phone number must be at least 9 digits'),
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
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      phoneNumber: '',
      password: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: RegisterForm) => {
    setFormError(null);
    try {
      const auth = await backendApi.registerPlayer({
        username: data.username,
        phone_number: data.phoneNumber,
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
          <AppInput
            label="Phone number"
            placeholder="e.g. +60123456789"
            keyboardType="phone-pad"
            value={value}
            onChangeText={onChange}
            error={errors.phoneNumber?.message}
            leftAdornment={<Smartphone size={18} color="#64748B" />}
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
              formError
                ?? 'Use at least 8 characters with at least one letter and one number.'
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
