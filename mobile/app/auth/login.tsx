import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, TextInput, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Check, ChevronDown, LockKeyhole, Phone } from 'lucide-react-native';
import { AuthShell } from '../../components/auth/AuthShell';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { appChromeColors } from '../../components/ui/theme';
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

const countryDialCodes = [
  { value: '+60', label: '+60', caption: 'Malaysia' },
  { value: '+65', label: '+65', caption: 'Singapore' },
  { value: '+62', label: '+62', caption: 'Indonesia' },
] as const;

function normalizePhoneNumber(value: string) {
  return value.replace(/\D/g, '');
}

function splitPhoneIdentifier(identifier: string) {
  const cleanedIdentifier = identifier.trim();
  const matchedCode = countryDialCodes.find((item) =>
    cleanedIdentifier.startsWith(item.value),
  );

  if (!matchedCode) {
    return {
      countryCode: countryDialCodes[0].value,
      phoneNumber: normalizePhoneNumber(cleanedIdentifier),
    };
  }

  return {
    countryCode: matchedCode.value,
    phoneNumber: normalizePhoneNumber(cleanedIdentifier.slice(matchedCode.value.length)),
  };
}

function composePhoneIdentifier(countryCode: string, phoneNumber: string) {
  const normalizedNumber = normalizePhoneNumber(phoneNumber).replace(/^0+/, '');
  return `${countryCode}${normalizedNumber}`;
}

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
  const [isCountryPickerOpen, setIsCountryPickerOpen] = useState(false);

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

  const activeDemo = useMemo(
    () => demoUsers.find((item) => item.role === selectedRole) ?? demoUsers[0],
    [selectedRole]
  );
  const countryCodeValue = watch('countryCode');
  const phoneNumberValue = watch('phoneNumber');
  const identifierValue = composePhoneIdentifier(countryCodeValue, phoneNumberValue);
  const selectedCountry =
    countryDialCodes.find((item) => item.value === countryCodeValue) ?? countryDialCodes[0];

  useEffect(() => {
    const phoneParts = splitPhoneIdentifier(params.identifier ?? activeDemo.identifier);
    setValue('countryCode', phoneParts.countryCode);
    setValue('phoneNumber', phoneParts.phoneNumber);
    setValue('password', activeDemo.password);
  }, [activeDemo.identifier, activeDemo.password, params.identifier, setValue]);

  const onSubmit = async (data: LoginForm) => {
    setFormError(null);
    await new Promise((resolve) => setTimeout(resolve, 250));
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

      const profile = await backendApi.fetchProfile(auth.access_token).catch(() => null);

      setBackendPlayerSession({
        accessToken: auth.access_token,
        player: mapBackendUserToPlayerProfile(auth.user, profile),
      });

      router.replace((profile ? '/player' : '/player/profile/edit') as never);
    } catch (error) {
      if (selectedRole === 'admin') {
        const role = login(phoneIdentifier);
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
          name="phoneNumber"
          render={({ field: { onChange, value } }) => (
            <View className="relative z-20 gap-2">
              <HeroText className="ml-1 text-sm font-semibold text-foreground">
                Phone number
              </HeroText>
              <View
                className={`flex-row items-center rounded-lg border bg-white shadow-soft ${
                  isCountryPickerOpen ? 'border-primary-600' : 'border-[#D2D2D7]'
                }`}
              >
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Choose country code"
                  onPress={() => setIsCountryPickerOpen((current) => !current)}
                  className="h-14 min-w-[94px] flex-row items-center justify-center gap-1.5 border-r border-[#D2D2D7] px-3"
                >
                  <HeroText className="text-[15px] font-semibold text-[#1D1D1F]">
                    {selectedCountry.value}
                  </HeroText>
                  <ChevronDown
                    size={15}
                    color="#1D1D1F"
                    strokeWidth={2}
                    style={{ transform: [{ rotate: isCountryPickerOpen ? '180deg' : '0deg' }] }}
                  />
                </Pressable>
                <Phone size={17} color="rgba(29,29,31,0.48)" strokeWidth={2} className="ml-3" />
                <TextInput
                  placeholder={
                    selectedRole === 'player'
                      ? '123456789'
                      : '190000000'
                  }
                  keyboardType="phone-pad"
                  value={value}
                  onChangeText={(nextValue) => onChange(normalizePhoneNumber(nextValue))}
                  placeholderTextColor="rgba(29,29,31,0.48)"
                  selectionColor={appChromeColors.primary}
                  className="h-14 flex-1 border-0 bg-transparent px-3 text-[15px] text-[#1D1D1F] outline-none"
                />
              </View>
              {isCountryPickerOpen ? (
                <View className="absolute left-0 right-0 top-[78px] z-30 overflow-hidden rounded-lg border border-[#D2D2D7] bg-white shadow-float">
                  {countryDialCodes.map((item) => {
                    const isSelected = countryCodeValue === item.value;

                    return (
                      <Pressable
                        key={item.value}
                        accessibilityRole="button"
                        onPress={() => {
                          setValue('countryCode', item.value, { shouldValidate: true });
                          setIsCountryPickerOpen(false);
                        }}
                        className={`min-h-14 flex-row items-center justify-between px-4 py-3 ${
                          isSelected ? 'bg-primary-50' : 'bg-white'
                        }`}
                      >
                        <View>
                          <HeroText
                            className={`text-[15px] font-semibold ${
                              isSelected ? 'text-primary-700' : 'text-[#1D1D1F]'
                            }`}
                          >
                            {item.caption}
                          </HeroText>
                          <HeroText className="mt-0.5 text-[12px] text-[rgba(29,29,31,0.52)]">
                            {item.value}
                          </HeroText>
                        </View>
                        {isSelected ? (
                          <Check size={17} color="#0071E3" strokeWidth={2.2} />
                        ) : null}
                      </Pressable>
                    );
                  })}
                </View>
              ) : null}
              {(errors.countryCode?.message || errors.phoneNumber?.message || formError) ? (
                <HeroText
                  className={`ml-1 text-xs leading-5 ${
                    errors.countryCode?.message || errors.phoneNumber?.message || formError
                      ? 'text-danger'
                      : 'text-muted'
                  }`}
                >
                  {errors.countryCode?.message ?? errors.phoneNumber?.message ?? formError}
                </HeroText>
              ) : (
                <HeroText className="ml-1 text-xs leading-5 text-muted">
                  We will sign in with {composePhoneIdentifier(countryCodeValue, value || '')}.
                </HeroText>
              )}
            </View>
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
                const phoneParts = splitPhoneIdentifier(item.identifier);
                setSelectedRole(item.role);
                setValue('countryCode', phoneParts.countryCode);
                setValue('phoneNumber', phoneParts.phoneNumber);
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
