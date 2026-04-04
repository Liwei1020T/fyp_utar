import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { ChevronLeft, LockKeyhole, Mail, UserRound, UserRoundPlus } from 'lucide-react-native';
import { HeroText } from '../../components/ui/heroui';
import { AppButton } from '../../components/ui/AppButton';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { AppScreen } from '../../components/shared/AppScreen';
import { useAppStore } from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendUserToPlayerProfile } from '../../services/backendMappers';

const registerSchema = z
  .object({
    username: z.string().min(3, 'Username must be at least 3 characters'),
    phoneNumber: z.string().min(9, 'Phone number must be at least 9 digits'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
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
    <AppScreen
      tone="auth"
      eyebrow="New player"
      title="Create account"
      subtitle="Set up your profile and continue into the player experience."
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
              Join StringSense
            </HeroText>
            <HeroText className="mt-2 text-[27px] font-bold tracking-tight text-[#122018]">
              Build your badminton profile from the first session.
            </HeroText>
            <HeroText className="mt-3 text-sm leading-6 text-[#607266]">
              Only players can self-register. Admin access stays pre-created for the single-store shop workspace.
            </HeroText>
          </View>
          <View className="h-14 w-14 items-center justify-center rounded-[22px] bg-[#E1EDF9]">
            <UserRoundPlus size={22} color="#2F64B6" />
          </View>
        </View>
      </View>

      <View className="mt-6 rounded-[32px] border border-[#D9E5F1] bg-white p-5 shadow-soft">
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
              placeholder="Minimum 8 characters"
              secureTextEntry
              value={value}
              onChangeText={onChange}
              error={errors.password?.message}
              helperText={
                formError ??
                'Player registration now creates a live backend account.'
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
          className="mt-2 border-[#2F64B6] bg-[#2F64B6] shadow-float"
          onPress={handleSubmit(onSubmit)}
          isLoading={isSubmitting}
        />
      </View>

      <View className="mt-7 flex-row justify-center pb-6">
        <HeroText className="text-[#607266]">Already have an account? </HeroText>
        <Pressable onPress={() => router.push('/auth/login')}>
          <HeroText className="font-semibold text-[#254E90]">Log in</HeroText>
        </Pressable>
      </View>
    </AppScreen>
  );
}
