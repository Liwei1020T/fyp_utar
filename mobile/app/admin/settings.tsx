import React, { useEffect, useState } from 'react';
import { useRouter } from 'expo-router';
import { Search } from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import { Alert, Image, Modal, Platform, Pressable, Switch, View } from 'react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { HeroText } from '../../components/ui/heroui';
import { showAlert } from '../../lib/alerts';
import { useAppStore, useBackendAccessToken, useCurrentUser, useStrings } from '../../store/appStore';
import {
  BackendApiError,
  backendApi,
  resolveBackendMediaUrl,
} from '../../services/backendApi';
import type { BackendUploadFile } from '../../services/backendApi';
import type { StoreSettings } from '../../types/domain';

function normalizeStorePolicyText(value: string) {
  if (/payment is completed|payment completes|full payment/i.test(value)) {
    return 'Reschedule or cancellation is allowed before the admin starts work on the racket.';
  }
  return value;
}

const NOTIFICATION_CATEGORIES = [
  'booking',
  'payment',
  'service',
  'chat',
  'system',
] as const;

function normalizeNotificationSettings(
  value: StoreSettings['notificationSettings'] | undefined,
): StoreSettings['notificationSettings'] {
  return Object.fromEntries(
    Object.entries(value ?? {}).map(([category, config]) => [
      category,
      { enabled: config.enabled },
    ]),
  );
}

export default function AdminSettingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const settings = useAppStore((state) => state.storeSettings);
  const logout = useAppStore((state) => state.logout);
  const updateStoreSettings = useAppStore((state) => state.updateStoreSettings);
  const [storeName, setStoreName] = useState(settings?.storeName ?? '');
  const [storeContact, setStoreContact] = useState(settings?.storeContact ?? '');
  const [address, setAddress] = useState(settings?.address ?? '');
  const [supportText, setSupportText] = useState(settings?.supportText ?? '');
  const [bookingNotes, setBookingNotes] = useState(settings?.bookingNotes ?? '');
  const [policyText, setPolicyText] = useState(settings?.storePolicyText ?? '');
  const [paymentNotes, setPaymentNotes] = useState(settings?.paymentNotes ?? '');
  const [trendingStringIds, setTrendingStringIds] = useState<string[]>(
    settings?.trendingStringIds ?? []
  );
  const [notificationSettings, setNotificationSettings] = useState(
    settings?.notificationSettings ?? {},
  );
  const [paymentQrUrl, setPaymentQrUrl] = useState(settings?.paymentQrUrl);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [trendingSearch, setTrendingSearch] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isQrUpdating, setIsQrUpdating] = useState(false);
  const [isQrPreviewOpen, setIsQrPreviewOpen] = useState(false);

  useEffect(() => {
    if (!settings) {
      return;
    }
    setStoreName(settings.storeName);
    setStoreContact(settings.storeContact);
    setAddress(settings.address);
    setSupportText(settings.supportText);
    setBookingNotes(settings.bookingNotes);
    setPolicyText(normalizeStorePolicyText(settings.storePolicyText));
    setPaymentNotes(settings.paymentNotes);
    setPaymentQrUrl(settings.paymentQrUrl);
    setTrendingStringIds(settings.trendingStringIds ?? []);
    setNotificationSettings(normalizeNotificationSettings(settings.notificationSettings));
  }, [settings]);

  const toggleTrendingString = (stringId: string) => {
    setSaveSuccessMessage(null);
    setTrendingStringIds((current) => {
      if (current.includes(stringId)) {
        return current.filter((id) => id !== stringId);
      }

      if (current.length >= 5) {
        setError('Remove one selected string before adding another homepage feature.');
        return current;
      }

      setError(null);
      return [...current, stringId];
    });
  };

  const selectedTrendingStrings = trendingStringIds
    .map((id) => strings.find((item) => item.id === id))
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
  const normalizedTrendingSearch = trendingSearch.trim().toLowerCase();
  const filteredTrendingStrings = strings.filter((item) => {
    if (!normalizedTrendingSearch) {
      return true;
    }

    return `${item.brand} ${item.model} ${item.mainTrait}`
      .toLowerCase()
      .includes(normalizedTrendingSearch);
  });

  const showSaveSuccess = () => {
    const message = 'Your store details and homepage trending strings have been updated.';
    setSaveSuccessMessage(message);

    showAlert('Store settings saved', message);
  };

  useEffect(() => {
    if (!token || !user || user.role !== 'admin') {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      setError(null);
      try {
        const response = await backendApi.adminFetchStoreSettings(token);
        if (cancelled) {
          return;
        }
        updateStoreSettings({
          storeName: response.store_name,
          storeContact: response.store_contact,
          address: response.address,
          supportText: response.support_text,
          paymentNotes: response.payment_notes,
          paymentQrUrl: resolveBackendMediaUrl(response.payment_qr_url),
          bookingNotes: response.booking_notes,
          storePolicyText: normalizeStorePolicyText(response.store_policy_text),
          trendingStringIds: response.trending_string_ids ?? [],
          notificationSettings: normalizeNotificationSettings(
            response.notification_settings,
          ),
        });
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof BackendApiError
              ? loadError.message
              : 'Failed to load store settings.',
          );
        }
      }
    };

    void hydrate();

    return () => {
      cancelled = true;
    };
  }, [token, updateStoreSettings, user]);

  const saveSettings = async () => {
    if (!user || user.role !== 'admin') {
      return;
    }
    if (!token) {
      setError('Your admin session expired. Sign in again before saving.');
      return;
    }

    setError(null);
    setIsSaving(true);
    try {
      const response = await backendApi.adminUpdateStoreSettings(token, {
        store_name: storeName,
        store_contact: storeContact,
        support_text: supportText,
        payment_notes:
          paymentNotes || 'External payments require shop verification.',
        booking_notes: bookingNotes,
        store_policy_text: policyText,
        address,
        trending_string_ids: trendingStringIds,
        notification_settings: normalizeNotificationSettings(notificationSettings),
      });
      updateStoreSettings({
        storeName: response.store_name,
        storeContact: response.store_contact,
        address: response.address,
        supportText: response.support_text,
        paymentNotes: response.payment_notes,
        paymentQrUrl: resolveBackendMediaUrl(response.payment_qr_url),
        bookingNotes: response.booking_notes,
        storePolicyText: normalizeStorePolicyText(response.store_policy_text),
        trendingStringIds: response.trending_string_ids ?? trendingStringIds,
        notificationSettings: normalizeNotificationSettings(
          response.notification_settings,
        ),
      });
      showSaveSuccess();
    } catch (saveError) {
      setSaveSuccessMessage(null);
      setError(
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to save store settings.',
      );
    } finally {
      setIsSaving(false);
    }
  };

  const uploadPaymentQr = async () => {
    if (!token) {
      setError('Your admin session expired. Sign in again before changing the payment QR.');
      return;
    }
    setIsQrUpdating(true);
    setError(null);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        quality: 0.9,
        allowsEditing: false,
      });
      if (result.canceled || !result.assets[0]) {
        return;
      }
      const asset = result.assets[0];
      const photo: BackendUploadFile = {
        uri: asset.uri,
        name: asset.fileName ?? `payment-qr-${Date.now()}.png`,
        type: asset.mimeType ?? 'image/png',
      };
      const response = await backendApi.adminUploadPaymentQr(token, photo);
      const nextUrl = resolveBackendMediaUrl(response.payment_qr_url);
      setPaymentQrUrl(nextUrl);
      updateStoreSettings({ paymentQrUrl: nextUrl });
      setSaveSuccessMessage('The payment QR is ready for new QR-transfer requests.');
    } catch (uploadError) {
      setError(
        uploadError instanceof BackendApiError
          ? uploadError.message
          : 'Failed to upload the payment QR.',
      );
    } finally {
      setIsQrUpdating(false);
    }
  };

  const removePaymentQr = async () => {
    if (!token) {
      setError('Your admin session expired. Sign in again before changing the payment QR.');
      return;
    }
    setIsQrUpdating(true);
    setError(null);
    try {
      const response = await backendApi.adminDeletePaymentQr(token);
      const nextUrl = resolveBackendMediaUrl(response.payment_qr_url);
      setPaymentQrUrl(nextUrl);
      updateStoreSettings({ paymentQrUrl: nextUrl });
      setSaveSuccessMessage('The payment QR was removed. Existing pending reviews are unchanged.');
    } catch (deleteError) {
      setError(
        deleteError instanceof BackendApiError
          ? deleteError.message
          : 'Failed to remove the payment QR.',
      );
    } finally {
      setIsQrUpdating(false);
    }
  };

  const confirmRemovePaymentQr = () => {
    const message = 'Remove the QR? New QR-transfer requests will be unavailable until another QR is uploaded.';
    if (Platform.OS === 'web') {
      if (typeof globalThis.confirm !== 'function') {
        setError('Confirmation is unavailable. The payment QR was not changed.');
      } else if (globalThis.confirm(message)) {
        void removePaymentQr();
      }
      return;
    }
    Alert.alert('Remove payment QR?', message, [
      { text: 'Keep QR', style: 'cancel' },
      { text: 'Remove', style: 'destructive', onPress: () => void removePaymentQr() },
    ]);
  };

  if (!user || user.role !== 'admin') {
    return null;
  }

  const changePassword = async () => {
    if (!token || !currentPassword || !newPassword) return;
    setIsChangingPassword(true);
    setError(null);
    try {
      await backendApi.changePassword(token, {
        current_password: currentPassword,
        new_password: newPassword,
      });
      logout();
      router.replace('/auth/login');
    } catch (passwordError) {
      setError(
        passwordError instanceof BackendApiError
          ? passwordError.message
          : 'Failed to update admin password.',
      );
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title="Store settings"
      subtitle="Manage public contact details, support copy, booking policy, and featured strings."
      showBackButton
      onBackPress={() => router.back()}
      footer={
        <View className="border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          <AppButton
            label="Save store settings"
            onPress={saveSettings}
            isLoading={isSaving}
          />
        </View>
      }
    >
      <AppSection eyebrow="Store" title="Public-facing details">
        <AppInput label="Store name" value={storeName} onChangeText={setStoreName} />
        <AppInput label="Store contact" value={storeContact} onChangeText={setStoreContact} />
        <AppInput label="Address" value={address} onChangeText={setAddress} multiline inputClassName="min-h-24" />
      </AppSection>

      <AppSection eyebrow="Payments" title="Payment QR">
        <HeroText className="text-sm leading-6 text-neutral-600">
          Players use this QR for top-ups and booking payments. Upload a real shop QR before enabling QR-transfer requests.
        </HeroText>
        {paymentQrUrl ? (
          <Pressable
            className="mt-4 items-center rounded-[20px] border border-[#DCE6F7] bg-white p-4"
            onPress={() => setIsQrPreviewOpen(true)}
            accessibilityRole="button"
            accessibilityLabel="Preview payment QR"
          >
            <Image
              source={{ uri: paymentQrUrl }}
              className="h-56 w-56"
              resizeMode="contain"
              accessible={false}
            />
            <HeroText className="mt-2 text-xs font-semibold text-primary-700">
              Tap to preview
            </HeroText>
          </Pressable>
        ) : (
          <View className="mt-4 rounded-[16px] border border-warning-100 bg-warning-50 px-3 py-3">
            <HeroText className="text-sm font-semibold text-warning-700">
              No payment QR configured
            </HeroText>
          </View>
        )}
        <View className="mt-3 flex-row gap-2">
          <AppButton
            label={paymentQrUrl ? 'Replace QR' : 'Upload QR'}
            variant="outline"
            className="flex-1"
            isLoading={isQrUpdating}
            onPress={() => void uploadPaymentQr()}
          />
          {paymentQrUrl ? (
            <AppButton
              label="Delete"
              variant="danger"
              className="flex-1"
              isLoading={isQrUpdating}
              onPress={confirmRemovePaymentQr}
            />
          ) : null}
        </View>
      </AppSection>

      <AppSection eyebrow="Messaging" title="Support and policy copy">
        <AppInput label="Support text" value={supportText} onChangeText={setSupportText} multiline inputClassName="min-h-24" />
        <AppInput label="Booking notes" value={bookingNotes} onChangeText={setBookingNotes} multiline inputClassName="min-h-24" />
        <AppInput label="Store policy text" value={policyText} onChangeText={setPolicyText} multiline inputClassName="min-h-24" />
      </AppSection>

      <AppSection
        eyebrow="Notifications"
        title="Notification category switches"
      >
        <View className="gap-3">
          {NOTIFICATION_CATEGORIES.map((category) => {
            const config = notificationSettings[category] ?? {};
            const enabled = config.enabled ?? true;
            return (
              <AppCard key={category} variant="elevated" padding="md">
                <View className="mb-3 flex-row items-center justify-between">
                  <HeroText className="text-sm font-bold capitalize text-neutral-900">
                    {category}
                  </HeroText>
                  <Switch
                    value={enabled}
                    onValueChange={() =>
                      setNotificationSettings((current) => ({
                        ...current,
                        [category]: { enabled: !enabled },
                      }))
                    }
                    accessibilityLabel={`${category} notifications`}
                  />
                </View>
              </AppCard>
            );
          })}
        </View>
      </AppSection>

      <AppSection eyebrow="Admin account" title="Update password">
        <AppInput
          label="Current password"
          value={currentPassword}
          onChangeText={setCurrentPassword}
          secureTextEntry
        />
        <AppInput
          label="New password"
          value={newPassword}
          onChangeText={setNewPassword}
          secureTextEntry
        />
        <AppButton
          label="Update admin password"
          variant="outline"
          isLoading={isChangingPassword}
          isDisabled={!currentPassword || newPassword.length < 8}
          onPress={() => void changePassword()}
        />
      </AppSection>

      <AppSection
        eyebrow="Homepage"
        title="Featured strings"
        subtitle="Pick the exact strings that should appear on the player home screen."
      >
        <View className="gap-4">
          <AppCard variant="highlighted" padding="md">
            <View className="flex-row items-start justify-between gap-3">
              <View className="min-w-0 flex-1">
                <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                  On player home
                </HeroText>
                <HeroText className="mt-1 text-[13px] leading-5 text-slate-600">
                  Choose up to 5 strings for the Featured strings carousel.
                </HeroText>
              </View>
              <AppChip
                label={`${trendingStringIds.length}/5 selected`}
                variant="primary"
                size="md"
              />
            </View>

            {selectedTrendingStrings.length > 0 ? (
              <View className="mt-4 flex-row flex-wrap gap-2">
                {selectedTrendingStrings.map((item) => (
                  <AppChip
                    key={item.id}
                    label={`${item.brand} ${item.model}`}
                    size="md"
                    variant="primary"
                    onPress={() => toggleTrendingString(item.id)}
                  />
                ))}
              </View>
            ) : (
              <HeroText className="mt-4 text-[13px] leading-5 text-slate-600">
                Nothing selected yet. Choose a string from the catalog below.
              </HeroText>
            )}
          </AppCard>

          <View>
            <View className="mb-2 flex-row items-center justify-between gap-3">
              <HeroText className="text-sm font-semibold text-slate-900">
                Choose from catalog
              </HeroText>
              <HeroText className="text-[12px] text-slate-500">
                {filteredTrendingStrings.length} available
              </HeroText>
            </View>
            <AppInput
              variant="minimal"
              className="mb-3"
              value={trendingSearch}
              onChangeText={setTrendingSearch}
              placeholder="Search string or brand"
              leftAdornment={<Search size={16} color="#94A3B8" />}
            />

            <View className="flex-row flex-wrap gap-2">
              {filteredTrendingStrings.map((item) => {
                const isSelected = trendingStringIds.includes(item.id);

                return (
                  <AppChip
                    key={item.id}
                    label={`${item.brand} ${item.model}`}
                    size="md"
                    variant={isSelected ? 'primary' : 'neutral'}
                    onPress={() => toggleTrendingString(item.id)}
                  />
                );
              })}
              {filteredTrendingStrings.length === 0 ? (
                <HeroText className="text-[13px] leading-5 text-slate-600">
                  No strings match “{trendingSearch.trim()}”.
                </HeroText>
              ) : null}
            </View>
          </View>
        </View>
      </AppSection>

      {saveSuccessMessage ? (
        <View className="mt-4 rounded-[20px] border border-success-100 bg-success-50 px-4 py-3">
          <HeroText className="text-[13px] font-semibold text-success-700">
            Store settings saved
          </HeroText>
          <HeroText className="mt-1 text-[12px] leading-5 text-success-700">
            {saveSuccessMessage}
          </HeroText>
        </View>
      ) : null}

      {error ? (
        <HeroText className="mt-4 text-sm font-semibold text-danger-600">
          {error}
        </HeroText>
      ) : null}

      <Modal
        visible={isQrPreviewOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setIsQrPreviewOpen(false)}
      >
        <View className="flex-1 items-center justify-center bg-black/80 p-6">
          <Pressable
            className="absolute inset-0"
            onPress={() => setIsQrPreviewOpen(false)}
            accessibilityRole="button"
            accessibilityLabel="Close QR preview"
          />
          {paymentQrUrl ? (
            <Image
              source={{ uri: paymentQrUrl }}
              className="h-[80%] w-full"
              resizeMode="contain"
              accessibilityLabel="Shop payment QR code"
            />
          ) : null}
          <AppButton
            label="Close preview"
            variant="secondary"
            className="mt-5"
            onPress={() => setIsQrPreviewOpen(false)}
          />
        </View>
      </Modal>

    </AppScreen>
  );
}
