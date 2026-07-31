import React, { useCallback, useState } from 'react';
import { Alert, FlatList, Platform, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { AlertCircle, CheckCircle2, Clock3 } from 'lucide-react-native';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppButton } from '../../components/ui/AppButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../components/shared/AppScreen';
import {
  formatCurrency,
  formatBookingStatus,
  formatDateTime,
  formatPaymentMethod,
  formatPaymentStatus,
} from '../../lib/formatters';
import { getPaymentStatusVariant } from '../../components/ui/theme';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
  usePayments,
} from '../../store/appStore';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { mapBackendPaymentToPayment } from '../../services/backendMappers';
import type { Payment } from '../../types/domain';

type PaymentDecision = 'paid' | 'failed' | 'cancelled';

export default function AdminPaymentsScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(16);
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const payments = usePayments();
  const setLivePayments = useAppStore((state) => state.setLivePayments);
  const upsertLivePayment = useAppStore((state) => state.upsertLivePayment);
  const [updating, setUpdating] = useState<{
    paymentId: string;
    status: PaymentDecision;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refreshPayments = useCallback(async () => {
    if (!token) {
      return;
    }
    setIsRefreshing(true);
    setError(null);
    try {
      const records = await backendApi.adminListPayments(token);
      setLivePayments(records.map(mapBackendPaymentToPayment));
    } catch (refreshError) {
      setError(
        refreshError instanceof BackendApiError
          ? refreshError.message
          : 'Failed to refresh payments.',
      );
    } finally {
      setIsRefreshing(false);
    }
  }, [setLivePayments, token]);

  useFocusEffect(
    useCallback(() => {
      void refreshPayments();
    }, [refreshPayments]),
  );

  if (!user || user.role !== 'admin') {
    return null;
  }

  const updatePayment = async (paymentId: string, status: PaymentDecision) => {
    if (!token) {
      setError('A live admin login is required to update payment records.');
      return;
    }
    setUpdating({ paymentId, status });
    setError(null);
    try {
      const response = await backendApi.adminUpdatePayment(
        token,
        paymentId,
        status,
      );
      const updated = mapBackendPaymentToPayment(response);
      upsertLivePayment(updated);
    } catch (updateError) {
      setError(
        updateError instanceof BackendApiError
          ? updateError.message
          : 'Failed to update payment.',
      );
    } finally {
      setUpdating(null);
    }
  };

  const confirmPaymentUpdate = (payment: Payment, status: PaymentDecision) => {
    const booking = payment.bookingId
      ? bookings.find((item) => item.id === payment.bookingId)
      : undefined;
    const customerBooking =
      booking ?? bookings.find((item) => item.playerId === payment.playerId);
    const customer = customerBooking?.customerName ?? `customer ${payment.playerId}`;
    const amount = formatCurrency(payment.amount);
    const isTopUp = payment.type === 'wallet_top_up';
    let consequence: string;
    if (status === 'paid') {
      consequence = isTopUp
        ? `This immediately adds ${amount} to ${customer}'s wallet balance.`
        : 'This records the payment as paid. It does not advance the booking status.';
    } else if (status === 'failed') {
      consequence = isTopUp
        ? `No wallet credit will be added for ${customer}.`
        : 'The payment will be marked failed and the booking status will not change.';
    } else {
      consequence = isTopUp
        ? `The top-up request will be cancelled without crediting ${customer}.`
        : 'The payment request will be cancelled without changing the booking status.';
    }
    const message = `${consequence} This decision cannot be changed in the app.`;

    if (Platform.OS === 'web') {
      if (typeof globalThis.confirm !== 'function') {
        setError('Confirmation is unavailable. No payment was changed.');
      } else if (globalThis.confirm(message)) {
        void updatePayment(payment.id, status);
      }
      return;
    }

    Alert.alert(
      status === 'paid'
        ? 'Verify payment as paid?'
        : status === 'failed'
          ? 'Mark payment as failed?'
          : 'Cancel payment request?',
      message,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text:
            status === 'paid'
              ? 'Verify paid'
              : status === 'failed'
                ? 'Mark failed'
                : 'Cancel request',
          style: status === 'paid' ? 'default' : 'destructive',
          onPress: () => void updatePayment(payment.id, status),
        },
      ],
    );
  };

  const pendingCount = payments.filter((item) => item.status === 'pending').length;
  const screenError =
    error ??
    (!token && pendingCount > 0
      ? 'A live admin login is required to update pending payments.'
      : null);

  return (
    <AppScreen
      tone="admin"
      headerVariant="primary"
      title="Payments monitor"
      subtitle="Verify pending external payments and wallet top-up requests."
      showBackButton
      onBackPress={() => router.back()}
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={payments}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        refreshing={isRefreshing}
        onRefresh={() => void refreshPayments()}
        renderItem={({ item }) => {
          const booking = item.bookingId
            ? bookings.find((candidate) => candidate.id === item.bookingId)
            : undefined;
          const customerBooking =
            booking ??
            bookings.find((candidate) => candidate.playerId === item.playerId);
          const customerName = customerBooking?.customerName;
          const customerPhone = customerBooking?.customerPhone;
          const orderLabel = booking?.orderCode ?? item.bookingId;
          const isPending = item.status === 'pending';
          const isTopUp = item.type === 'wallet_top_up';
          const isUpdating = updating?.paymentId === item.id;

          return (
            <AppCard variant="elevated" className="mb-4" padding="md">
              <View className="flex-row items-start justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-base font-semibold text-neutral-900">
                    {isTopUp
                      ? 'Wallet top-up'
                      : `Order ${orderLabel ?? 'unavailable'}`}
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                    {customerName ?? `Customer ID: ${item.playerId}`}
                    {customerPhone ? ` • ${customerPhone}` : ''}
                  </HeroText>
                  {booking ? (
                    <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                      {booking.racketBrand} {booking.racketModel} •{' '}
                      {formatBookingStatus(booking.status)}
                    </HeroText>
                  ) : null}
                </View>
                <View className="items-end gap-2">
                  <AppChip
                    label={formatPaymentStatus(item.status)}
                    variant={getPaymentStatusVariant(item.status)}
                  />
                  <HeroText className="text-base font-bold text-neutral-900">
                    {formatCurrency(item.amount)}
                  </HeroText>
                </View>
              </View>
              <View className="mt-3 rounded-[18px] bg-neutral-50 px-3.5 py-3">
                <HeroText className="text-sm font-semibold text-neutral-700">
                  {formatPaymentMethod(item.method)} • {item.reference}
                </HeroText>
                <HeroText className="mt-1 text-xs leading-5 text-neutral-500">
                  {formatDateTime(item.createdAt)}
                </HeroText>
              </View>
              {isPending ? (
                <>
                  <HeroText className="mt-3 text-xs leading-5 text-neutral-500">
                    {isTopUp
                      ? 'Verify paid to credit the wallet immediately. Mark failed to reject the top-up without credit.'
                      : 'Verify paid to record payment only; the booking workflow stays unchanged. Mark failed to reject this payment.'}
                  </HeroText>
                  <View className="mt-4 flex-row gap-3">
                    <AppButton
                      label="Verify paid"
                      size="sm"
                      className="flex-1"
                      isLoading={isUpdating && updating.status === 'paid'}
                      isDisabled={!token || updating !== null}
                      accessibilityHint={
                        isTopUp
                          ? 'Requires confirmation and then credits the customer wallet'
                          : 'Requires confirmation and records payment without changing the booking'
                      }
                      onPress={() => confirmPaymentUpdate(item, 'paid')}
                    />
                    <AppButton
                      label="Mark failed"
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      isLoading={isUpdating && updating.status === 'failed'}
                      isDisabled={!token || updating !== null}
                      accessibilityHint="Requires confirmation and permanently marks this payment failed"
                      onPress={() => confirmPaymentUpdate(item, 'failed')}
                    />
                  </View>
                  <AppButton
                    label="Cancel request"
                    variant="ghost"
                    size="sm"
                    className="mt-2"
                    isLoading={isUpdating && updating.status === 'cancelled'}
                    isDisabled={!token || updating !== null}
                    accessibilityHint="Requires confirmation and cancels this pending request without credit or booking changes"
                    onPress={() => confirmPaymentUpdate(item, 'cancelled')}
                  />
                </>
              ) : item.note ? (
                <HeroText className="mt-3 text-xs leading-5 text-neutral-500">
                  {item.note}
                </HeroText>
              ) : null}
            </AppCard>
          );
        }}
        ListHeaderComponent={
          <View className="mb-4 gap-3">
            <AppCard
              variant={pendingCount > 0 ? 'highlighted' : 'subtle'}
              padding="md"
            >
              <View className="flex-row items-start gap-3">
                {pendingCount > 0 ? (
                  <Clock3 size={20} color="#2F64B6" />
                ) : (
                  <CheckCircle2 size={20} color="#15803D" />
                )}
                <View className="flex-1">
                  <HeroText className="text-base font-semibold text-neutral-900">
                    {pendingCount > 0
                      ? `${pendingCount} pending ${pendingCount === 1 ? 'request' : 'requests'}`
                      : 'No pending requests'}
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                    {pendingCount > 0
                      ? 'Confirm each decision after checking the payment evidence.'
                      : 'All loaded payments have a final status.'}
                  </HeroText>
                </View>
              </View>
            </AppCard>
            {screenError ? (
              <AppCard
                variant="subtle"
                padding="md"
                accessibilityRole="alert"
                accessibilityLiveRegion="polite"
              >
                <View className="flex-row items-start gap-3">
                  <AlertCircle size={20} color="#DC2626" />
                  <HeroText className="flex-1 text-sm font-medium leading-6 text-red-600">
                    {screenError}
                  </HeroText>
                </View>
              </AppCard>
            ) : null}
          </View>
        }
        ListEmptyComponent={
          <AppCard variant="subtle" padding="lg">
            <HeroText className="text-base font-semibold text-neutral-900">
              No payment records
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              New booking payments and wallet top-up requests will appear here.
            </HeroText>
          </AppCard>
        }
      />
    </AppScreen>
  );
}
