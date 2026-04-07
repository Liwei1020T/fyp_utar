import React, { useEffect, useState } from 'react';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { HeroText } from '../../components/ui/heroui';
import { useAppStore, useBackendAccessToken, useCurrentUser } from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';

export default function AdminSettingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
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
    setPolicyText(settings.storePolicyText);
    setPaymentNotes(settings.paymentNotes);
  }, [settings]);

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
          storePolicyText: response.store_policy_text,
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
          storePolicyText: response.store_policy_text,
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
      title="Store settings"
      subtitle="FYP1 store settings for contact info, support copy, address, and booking policy text."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
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
