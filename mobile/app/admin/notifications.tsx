import { useFocusEffect, useRouter } from 'expo-router';
import React, { useCallback, useMemo, useState } from 'react';
import { View } from 'react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { formatDateTime } from '../../lib/formatters';
import { BackendApiError, backendApi } from '../../services/backendApi';
import {
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
} from '../../store/appStore';
import type {
  BackendAdminDeviceToken,
  BackendAdminNotification,
  BackendNotificationCategory,
} from '../../types/backend';

const CATEGORIES: BackendNotificationCategory[] = [
  'booking',
  'payment',
  'service',
  'chat',
  'system',
];

export default function AdminNotificationsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const [notifications, setNotifications] = useState<BackendAdminNotification[]>(
    [],
  );
  const [devices, setDevices] = useState<BackendAdminDeviceToken[]>([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [category, setCategory] =
    useState<BackendNotificationCategory>('service');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const recipients = useMemo(() => {
    const byId = new Map<
      string,
      { id: string; name: string; phone: string }
    >();
    bookings.forEach((booking) => {
      if (!booking.playerId) return;
      byId.set(booking.playerId, {
        id: booking.playerId,
        name: booking.customerName ?? 'Player',
        phone: booking.customerPhone ?? '',
      });
    });
    devices.forEach((device) => {
      byId.set(device.user_id, {
        id: device.user_id,
        name: device.customer_username,
        phone: device.customer_phone_number,
      });
    });
    return [...byId.values()];
  }, [bookings, devices]);

  const load = useCallback(async () => {
    if (!token || user?.role !== 'admin') return;
    setIsBusy(true);
    setMessage(null);
    try {
      const [deliveryRows, deviceRows] = await Promise.all([
        backendApi.adminListNotifications(token),
        backendApi.adminListDeviceTokens(token),
      ]);
      setNotifications(deliveryRows);
      setDevices(deviceRows);
    } catch (error) {
      setMessage(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to load notification records.',
      );
    } finally {
      setIsBusy(false);
    }
  }, [token, user?.role]);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  if (!user || user.role !== 'admin') return null;

  const send = async () => {
    if (!token || !selectedUserId || !title.trim() || !body.trim()) return;
    setIsBusy(true);
    setMessage(null);
    try {
      const created = await backendApi.adminSendNotification(token, {
        user_id: selectedUserId,
        category,
        title: title.trim(),
        body: body.trim(),
      });
      setNotifications((current) => [created, ...current]);
      setTitle('');
      setBody('');
      setMessage(`In-app saved. Remote delivery status: ${created.status}.`);
    } catch (error) {
      setMessage(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to send notification.',
      );
    } finally {
      setIsBusy(false);
    }
  };

  const resend = async (notificationId: string) => {
    if (!token) return;
    setIsBusy(true);
    try {
      const updated = await backendApi.adminResendNotification(
        token,
        notificationId,
      );
      setNotifications((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setMessage(`In-app retained. Remote delivery status: ${updated.status}.`);
    } catch (error) {
      setMessage(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to retry notification.',
      );
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <AppScreen
      tone="admin"
      headerVariant="flow"
      title="Notification management"
      subtitle="Save an in-app update and attempt the configured remote delivery channel."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection eyebrow="Compose" title="Send player update">
        <View className="flex-row flex-wrap gap-2">
          {recipients.map((recipient) => (
            <AppChip
              key={recipient.id}
              label={`${recipient.name}${recipient.phone ? ` • ${recipient.phone}` : ''}`}
              variant={
                selectedUserId === recipient.id ? 'primary' : 'neutral'
              }
              onPress={() => setSelectedUserId(recipient.id)}
            />
          ))}
        </View>
        <View className="mt-3 flex-row flex-wrap gap-2">
          {CATEGORIES.map((item) => (
            <AppChip
              key={item}
              label={item}
              variant={category === item ? 'secondary' : 'neutral'}
              onPress={() => setCategory(item)}
            />
          ))}
        </View>
        <View className="mt-3 gap-3">
          <AppInput label="Title" value={title} onChangeText={setTitle} />
          <AppInput
            label="Message"
            value={body}
            onChangeText={setBody}
            multiline
            inputClassName="min-h-24"
          />
          <AppButton
            label="Send notification"
            isLoading={isBusy}
            isDisabled={!selectedUserId || !title.trim() || !body.trim()}
            onPress={() => void send()}
          />
        </View>
      </AppSection>

      {message ? (
        <AppCard variant="subtle" className="mb-4" padding="sm">
          <HeroText className="text-sm text-neutral-700">{message}</HeroText>
        </AppCard>
      ) : null}

      <AppSection eyebrow="Delivery log" title="Recent notifications">
        <View className="gap-3">
          {notifications.map((item) => (
            <AppCard key={item.id} variant="elevated" padding="md">
              <View className="flex-row items-start justify-between gap-3">
                <View className="flex-1">
                  <HeroText className="text-sm font-bold text-neutral-950">
                    {item.title}
                  </HeroText>
                  <HeroText className="mt-1 text-xs text-neutral-500">
                    {item.customer_username} • {formatDateTime(item.created_at)}
                  </HeroText>
                </View>
                <AppChip
                  label={item.status}
                  variant={item.status === 'sent' ? 'success' : 'warning'}
                />
              </View>
              <HeroText className="mt-3 text-sm leading-6 text-neutral-700">
                {item.body}
              </HeroText>
              {item.provider_message ? (
                <HeroText className="mt-2 text-xs text-neutral-500">
                  {item.provider_message}
                </HeroText>
              ) : null}
              {item.status !== 'sent' ? (
                <AppButton
                  label="Retry delivery"
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  isDisabled={isBusy}
                  onPress={() => void resend(item.id)}
                />
              ) : null}
            </AppCard>
          ))}
        </View>
      </AppSection>
    </AppScreen>
  );
}
