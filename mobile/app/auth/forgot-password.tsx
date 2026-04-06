import React, { useEffect, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { LockKeyhole, MessageSquareMore, Smartphone } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
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
    <AuthShell
      eyebrow="Player recovery"
      title={stage === 'request' ? 'Reset your password' : 'Enter your verification code'}
      subtitle={
        stage === 'request'
          ? 'Request a 6-digit code for your phone-based player account.'
          : 'Use the code you received and set a new password.'
      }
      onBack={() => router.back()}
      footer={
        <View className="items-center">
          <Pressable onPress={() => router.replace('/auth/login?role=player')}>
            <HeroText className="text-sm font-semibold text-primary-700">
              Back to login
            </HeroText>
          </Pressable>
        </View>
      }
    >
      <View className="gap-4">
        <AppChip
          label={stage === 'request' ? 'Step 1 of 2' : 'Step 2 of 2'}
          variant="secondary"
          className="self-start"
        />

        {formError ? (
          <AppCard variant="subtle" className="border border-red-100" padding="sm">
            <HeroText className="text-sm font-medium text-red-600">
              {formError}
            </HeroText>
          </AppCard>
        ) : null}

        {stage === 'request' ? (
          <View>
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
                  helperText="Use the same phone number as your player login."
                  leftAdornment={<Smartphone size={18} color="#64748B" />}
                />
              )}
            />

            <AppButton
              label="Send verification code"
              size="lg"
              onPress={handleRequestSubmit(requestCode)}
              isLoading={isRequestingCode}
            />
          </View>
        ) : (
          <View>
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
                  helperText="This can later be delivered through WhatsApp."
                  leftAdornment={<MessageSquareMore size={18} color="#64748B" />}
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

            <View className="gap-3">
              <AppButton
                label="Reset password"
                size="lg"
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
          </View>
        )}

        {devCodePreview ? (
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-500">
              Development preview
            </HeroText>
            <HeroText className="mt-2 text-[28px] font-bold tracking-[0.22em] text-primary-700">
              {devCodePreview}
            </HeroText>
          </AppCard>
        ) : null}
      </View>
    </AuthShell>
  );
}
