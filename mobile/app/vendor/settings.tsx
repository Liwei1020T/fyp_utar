import React, { useState } from 'react';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { useAppStore, useCurrentUser } from '../../store/appStore';

export default function AdminSettingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const settings = useAppStore((state) =>
    state.adminSettings.find((item) => item.adminId === user?.id)
  );
  const updateAdminSettings = useAppStore((state) => state.updateAdminSettings);
  const [storeName, setStoreName] = useState(settings?.storeName ?? '');
  const [storeContact, setStoreContact] = useState(settings?.storeContact ?? '');
  const [supportText, setSupportText] = useState(settings?.supportText ?? '');
  const [paymentNotes, setPaymentNotes] = useState(settings?.paymentNotes ?? '');
  const [bookingNotes, setBookingNotes] = useState(settings?.bookingNotes ?? '');
  const [policyText, setPolicyText] = useState(settings?.storePolicyText ?? '');

  if (!user || user.role !== 'admin' || !settings) {
    return null;
  }

  return (
    <AppScreen
      tone="admin"
      title="Store settings"
      subtitle="Single-store settings for contact info, support copy, payment notes, and booking policy text."
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
      </AppSection>

      <AppSection eyebrow="Messaging" title="Support and policy copy">
        <AppInput label="Support text" value={supportText} onChangeText={setSupportText} multiline inputClassName="min-h-24" />
        <AppInput label="Payment notes" value={paymentNotes} onChangeText={setPaymentNotes} multiline inputClassName="min-h-24" />
        <AppInput label="Booking notes" value={bookingNotes} onChangeText={setBookingNotes} multiline inputClassName="min-h-24" />
        <AppInput label="Store policy text" value={policyText} onChangeText={setPolicyText} multiline inputClassName="min-h-24" />
      </AppSection>

      <AppButton
        label="Save mock settings"
        className="mt-6"
        onPress={() =>
          updateAdminSettings(user.id, {
            storeName,
            storeContact,
            supportText,
            paymentNotes,
            bookingNotes,
            storePolicyText: policyText,
          })
        }
      />
    </AppScreen>
  );
}
