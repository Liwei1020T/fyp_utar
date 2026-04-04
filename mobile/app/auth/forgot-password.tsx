import React, { useEffect, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  ChevronLeft,
  KeyRound,
  LockKeyhole,
  MessageSquareMore,
  Smartphone,
} from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { BackendApiError, backendApi } from '../../services/backendApi';

const requestCodeSchema = z.object({
  phoneNumber: z.string().min(9, 'Phone number must be at least 9 digits'),
});

const resetPasswordSchema = z
  .object({
    phoneNumber: z.string().min(9, 'Phone number must be at least 9 digits'),
    verificationCode: z.string().regex(/^\d{6}$/, 'Enter the 6-digit code'),
    newPassword: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Za-z]/, 'Password must include at least one letter')
      .regex(/\d/, 'Password must include at least one number'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type RequestCodeForm = z.infer<typeof requestCodeSchema>;
type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;

export default function ForgotPasswordScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ identifier?: string }>();
  const initialIdentifier =
    typeof params.identifier === 'string' ? params.identifier : '';
  const [stage, setStage] = useState<'request' | 'reset'>('request');
  const [formError, setFormError] = useState<string | null>(null);
  const [requestMessage, setRequestMessage] = useState<string | null>(null);
  const [devCodePreview, setDevCodePreview] = useState<string | null>(null);

  const {
    control: requestControl,
    handleSubmit: handleRequestSubmit,
    setValue: setRequestValue,
    formState: { errors: requestErrors, isSubmitting: isRequestingCode },
  } = useForm<RequestCodeForm>({
    resolver: zodResolver(requestCodeSchema),
    defaultValues: {
      phoneNumber: initialIdentifier,
    },
  });

  const {
    control: resetControl,
    handleSubmit: handleResetSubmit,
    setValue: setResetValue,
    reset: resetResetForm,
    formState: { errors: resetErrors, isSubmitting: isResettingPassword },
  } = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      phoneNumber: initialIdentifier,
      verificationCode: '',
      newPassword: '',
      confirmPassword: '',
    },
  });

  useEffect(() => {
    if (!initialIdentifier) {
      return;
    }

    setRequestValue('phoneNumber', initialIdentifier);
    setResetValue('phoneNumber', initialIdentifier);
  }, [initialIdentifier, setRequestValue, setResetValue]);

  const requestCode = async (data: RequestCodeForm) => {
    setFormError(null);
    try {
      const response = await backendApi.requestPasswordResetCode({
        phone_number: data.phoneNumber,
      });

      setRequestMessage(response.message);
      setDevCodePreview(response.dev_code_preview);
      resetResetForm({
        phoneNumber: data.phoneNumber,
        verificationCode: response.dev_code_preview ?? '',
        newPassword: '',
        confirmPassword: '',
      });
      setStage('reset');
    } catch (error) {
      setFormError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to request a verification code.',
      );
    }
  };

  const resetPassword = async (data: ResetPasswordForm) => {
    setFormError(null);
    try {
      await backendApi.resetPasswordWithCode({
        phone_number: data.phoneNumber,
        verification_code: data.verificationCode,
        new_password: data.newPassword,
      });

      router.replace(
        `/auth/login?role=player&identifier=${encodeURIComponent(
          data.phoneNumber,
        )}`,
      );
    } catch (error) {
      setFormError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to reset password.',
      );
    }
  };

  return (
    <AppScreen
      tone="auth"
      eyebrow="Player recovery"
      title={stage === 'request' ? 'Forgot password' : 'Reset password'}
      subtitle={
        stage === 'request'
          ? 'Request a 6-digit recovery code for your phone-based player account.'
          : 'Enter the verification code and choose a new password for the live player backend.'
      }
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#122018" />}
          accessibilityLabel="Go back"
          variant="auth"
          onPress={() => router.back()}
        />
      }
    >
      <AppCard variant="highlighted" className="rounded-[32px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
              Recovery flow
            </HeroText>
            <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-neutral-950">
              Keep phone-first sign-in simple for the FYP demo.
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              Recovery codes are generated by the live backend now. WhatsApp delivery through WAHA can plug into the same request step later.
            </HeroText>
          </View>
          <View className="h-12 w-12 items-center justify-center rounded-2xl bg-primary-600">
            <KeyRound size={20} color="white" />
          </View>
        </View>
      </AppCard>

      {formError ? (
        <AppCard variant="subtle" className="mt-5 border border-red-100" padding="md">
          <HeroText className="text-sm font-medium text-red-600">
            {formError}
          </HeroText>
        </AppCard>
      ) : null}

      {stage === 'request' ? (
        <AppSection eyebrow="Step 1" title="Request verification code">
          <AppCard variant="elevated" padding="lg">
            <Controller
              control={requestControl}
              name="phoneNumber"
              render={({ field: { onChange, value } }) => (
                <AppInput
                  label="Phone number"
                  placeholder="e.g. +60123456789"
                  keyboardType="phone-pad"
                  value={value}
                  onChangeText={onChange}
                  error={requestErrors.phoneNumber?.message}
                  helperText="Use the same phone number you use for the player login."
                  leftAdornment={<Smartphone size={18} color="#64748B" />}
                />
              )}
            />

            <AppButton
              label="Send verification code"
              size="lg"
              className="mt-2 border-[#2F64B6] bg-[#2F64B6] shadow-float"
              onPress={handleRequestSubmit(requestCode)}
              isLoading={isRequestingCode}
            />
          </AppCard>
        </AppSection>
      ) : (
        <>
          <AppSection eyebrow="Step 2" title="Enter the generated code">
            <AppCard variant="elevated" padding="lg">
              {requestMessage ? (
                <HeroText className="mb-4 text-sm leading-6 text-neutral-500">
                  {requestMessage}
                </HeroText>
              ) : null}

              <Controller
                control={resetControl}
                name="phoneNumber"
                render={({ field: { onChange, value } }) => (
                  <AppInput
                    label="Phone number"
                    placeholder="e.g. +60123456789"
                    keyboardType="phone-pad"
                    value={value}
                    onChangeText={onChange}
                    error={resetErrors.phoneNumber?.message}
                    leftAdornment={<Smartphone size={18} color="#64748B" />}
                  />
                )}
              />

              <Controller
                control={resetControl}
                name="verificationCode"
                render={({ field: { onChange, value } }) => (
                  <AppInput
                    label="Verification code"
                    placeholder="6-digit code"
                    keyboardType="number-pad"
                    value={value}
                    onChangeText={onChange}
                    error={resetErrors.verificationCode?.message}
                    helperText="Future WAHA delivery will send this code to the player's WhatsApp inbox."
                    leftAdornment={
                      <MessageSquareMore size={18} color="#64748B" />
                    }
                  />
                )}
              />

              <Controller
                control={resetControl}
                name="newPassword"
                render={({ field: { onChange, value } }) => (
                  <AppInput
                    label="New password"
                    placeholder="Minimum 8 characters"
                    secureTextEntry
                    value={value}
                    onChangeText={onChange}
                    error={resetErrors.newPassword?.message}
                    leftAdornment={<LockKeyhole size={18} color="#64748B" />}
                  />
                )}
              />

              <Controller
                control={resetControl}
                name="confirmPassword"
                render={({ field: { onChange, value } }) => (
                  <AppInput
                    label="Confirm password"
                    placeholder="Repeat your new password"
                    secureTextEntry
                    value={value}
                    onChangeText={onChange}
                    error={resetErrors.confirmPassword?.message}
                    leftAdornment={<LockKeyhole size={18} color="#64748B" />}
                  />
                )}
              />

              <View className="mt-2 gap-3">
                <AppButton
                  label="Reset password"
                  size="lg"
                  className="border-[#2F64B6] bg-[#2F64B6] shadow-float"
                  onPress={handleResetSubmit(resetPassword)}
                  isLoading={isResettingPassword}
                />
                <AppButton
                  label="Request another code"
                  variant="outline"
                  size="lg"
                  onPress={() => setStage('request')}
                />
              </View>
            </AppCard>
          </AppSection>

          {devCodePreview ? (
            <AppSection eyebrow="Development only" title="Code preview">
              <AppCard variant="subtle" padding="lg">
                <HeroText className="text-sm leading-6 text-neutral-500">
                  This preview is shown only while WAHA delivery is not connected in the dev environment.
                </HeroText>
                <HeroText className="mt-3 text-[32px] font-bold tracking-[0.24em] text-primary-700">
                  {devCodePreview}
                </HeroText>
              </AppCard>
            </AppSection>
          ) : null}
        </>
      )}

      <View className="mt-6 flex-row justify-center pb-6">
        <HeroText className="text-[#607266]">Remembered it? </HeroText>
        <Pressable onPress={() => router.replace('/auth/login?role=player')}>
          <HeroText className="font-semibold text-[#254E90]">Back to login</HeroText>
        </Pressable>
      </View>
    </AppScreen>
  );
}
