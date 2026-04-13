import React, { useEffect, useState } from 'react';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { View } from 'react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppChip } from '../../components/ui/AppChip';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { HeroText } from '../../components/ui/heroui';
import { useAppStore, useBackendAccessToken, useCurrentUser, useStrings } from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';

function normalizeFyp1PolicyText(value: string) {
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
  const settings = useAppStore((state) =>
    state.adminSettings.find((item) => item.adminId === user?.id)
  );
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
  const [error, setError] = useState<string | null>(null);
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
    setPolicyText(normalizeFyp1PolicyText(settings.storePolicyText));
    setPaymentNotes(settings.paymentNotes);
    setTrendingStringIds(settings.trendingStringIds ?? []);
  }, [settings]);

  const toggleTrendingString = (stringId: string) => {
    setTrendingStringIds((current) => {
      if (current.includes(stringId)) {
        return current.filter((id) => id !== stringId);
      }

      if (current.length >= 5) {
        return [...current.slice(1), stringId];
      }

      return [...current, stringId];
    });
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
          storePolicyText: normalizeFyp1PolicyText(response.store_policy_text),
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

    setError(null);
    setIsSaving(true);
    try {
      if (token) {
        const response = await backendApi.adminUpdateStoreSettings(token, {
          store_name: storeName,
          store_contact: storeContact,
          support_text: supportText,
          payment_notes: paymentNotes || 'Payments are deferred for FYP2.',
          booking_notes: bookingNotes,
          store_policy_text: policyText,
          address,
        });
        updateAdminSettings(user.id, {
          storeName: response.store_name,
          storeContact: response.store_contact,
          address: response.address,
          supportText: response.support_text,
          paymentNotes: response.payment_notes,
          bookingNotes: response.booking_notes,
          storePolicyText: normalizeFyp1PolicyText(response.store_policy_text),
          trendingStringIds,
        });
      } else {
        updateAdminSettings(user.id, {
          storeName,
          storeContact,
          address,
          supportText,
          paymentNotes,
          bookingNotes,
          storePolicyText: policyText,
          trendingStringIds,
        });
      }
    } catch (saveError) {
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
      subtitle="FYP1 store settings for contact info, support copy, address, and booking policy text."
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
        subtitle="Choose up to 5 strings to feature on the player home screen."
      >
        <HeroText className="mb-3 text-xs font-semibold text-slate-500">
          Selected: {trendingStringIds.length}/5
        </HeroText>
        <View className="flex-row flex-wrap gap-2">
          {strings.map((item) => {
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
      </AppSection>

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
