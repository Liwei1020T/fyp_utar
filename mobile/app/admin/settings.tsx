import React, { useEffect, useState } from 'react';
import { useRouter } from 'expo-router';
import { Search } from 'lucide-react-native';
import { Alert, Platform, View } from 'react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { HeroText } from '../../components/ui/heroui';
import { useAppStore, useBackendAccessToken, useCurrentUser, useStrings } from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';

function normalizeStorePolicyText(value: string) {
  if (/payment is completed|payment completes|full payment/i.test(value)) {
    return 'Reschedule or cancellation is allowed before the admin starts work on the racket.';
  }
  return value;
}

export default function AdminSettingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const settings = useAppStore((state) => {
    const byUser = state.adminSettings.find((item) => item.adminId === user?.id);
    return byUser ?? state.adminSettings.find((item) => item.adminId === 'main');
  });
  const updateAdminSettings = useAppStore((state) => state.updateAdminSettings);
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
  const [trendingSearch, setTrendingSearch] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

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
    setTrendingStringIds(settings.trendingStringIds ?? []);
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

    if (Platform.OS !== 'web') {
      Alert.alert('Store settings saved', message);
    }
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
        updateAdminSettings(user.id, {
          storeName: response.store_name,
          storeContact: response.store_contact,
          address: response.address,
          supportText: response.support_text,
          paymentNotes: response.payment_notes,
          bookingNotes: response.booking_notes,
          storePolicyText: normalizeStorePolicyText(response.store_policy_text),
          trendingStringIds: response.trending_string_ids ?? [],
        });
        updateAdminSettings('main', {
          storeName: response.store_name,
          storeContact: response.store_contact,
          address: response.address,
          supportText: response.support_text,
          paymentNotes: response.payment_notes,
          bookingNotes: response.booking_notes,
          storePolicyText: normalizeStorePolicyText(response.store_policy_text),
          trendingStringIds: response.trending_string_ids ?? [],
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
  }, [token, updateAdminSettings, user]);

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
      });
      updateAdminSettings(user.id, {
        storeName: response.store_name,
        storeContact: response.store_contact,
        address: response.address,
        supportText: response.support_text,
        paymentNotes: response.payment_notes,
        bookingNotes: response.booking_notes,
        storePolicyText: normalizeStorePolicyText(response.store_policy_text),
        trendingStringIds: response.trending_string_ids ?? trendingStringIds,
      });
      updateAdminSettings('main', {
        storeName: response.store_name,
        storeContact: response.store_contact,
        address: response.address,
        supportText: response.support_text,
        paymentNotes: response.payment_notes,
        bookingNotes: response.booking_notes,
        storePolicyText: normalizeStorePolicyText(response.store_policy_text),
        trendingStringIds: response.trending_string_ids ?? trendingStringIds,
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

  if (!user || user.role !== 'admin') {
    return null;
  }

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title="Store settings"
      subtitle="Manage public contact details, support copy, booking policy, and featured strings."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection eyebrow="Store" title="Public-facing details">
        <AppInput label="Store name" value={storeName} onChangeText={setStoreName} />
        <AppInput label="Store contact" value={storeContact} onChangeText={setStoreContact} />
        <AppInput label="Address" value={address} onChangeText={setAddress} multiline inputClassName="min-h-24" />
      </AppSection>

      <AppSection eyebrow="Messaging" title="Support and policy copy">
        <AppInput label="Support text" value={supportText} onChangeText={setSupportText} multiline inputClassName="min-h-24" />
        <AppInput label="Booking notes" value={bookingNotes} onChangeText={setBookingNotes} multiline inputClassName="min-h-24" />
        <AppInput label="Store policy text" value={policyText} onChangeText={setPolicyText} multiline inputClassName="min-h-24" />
      </AppSection>

      <AppSection
        eyebrow="Homepage"
        title="Trending strings"
        subtitle="Pick the exact strings that should appear on the player home screen."
      >
        <AppCard variant="subtle" padding="md">
          <View className="gap-4">
            <View>
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                Selected {trendingStringIds.length}/5
              </HeroText>
              <HeroText className="mt-1 text-[13px] leading-5 text-slate-600">
                These strings are the only items shown in the player Trending Strings carousel.
              </HeroText>
            </View>

            {selectedTrendingStrings.length > 0 ? (
              <View className="flex-row flex-wrap gap-2">
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
              <View className="rounded-[16px] border border-[#DCE6F7] bg-white px-3 py-3">
                <HeroText className="text-[13px] font-semibold text-slate-900">
                  No homepage strings selected
                </HeroText>
                <HeroText className="mt-1 text-[12px] leading-5 text-slate-600">
                  Select up to 5 strings below. Player home will stay empty until at least one is saved.
                </HeroText>
              </View>
            )}

            <AppInput
              variant="minimal"
              className="mb-0"
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
            </View>
          </View>
        </AppCard>
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

      <AppButton
        label="Save store settings"
        className="mt-6"
        onPress={saveSettings}
        isLoading={isSaving}
      />
    </AppScreen>
  );
}
