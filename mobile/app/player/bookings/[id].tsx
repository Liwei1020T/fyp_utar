import React from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft, MessageSquareText, QrCode, TimerReset } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppDetailList } from '../../../components/shared/AppDetailList';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { useAppStore, useBookings, usePayments } from '../../../store/appStore';
import { getAdminById, getStringById } from '../../../services/mockAppService';
import {
  formatBookingStatus,
  formatCurrency,
  formatPaymentMethod,
  formatPaymentStatus,
} from '../../../lib/formatters';
import { getBookingStatusVariant, getPaymentStatusVariant } from '../../../components/ui/theme';

export default function PlayerBookingDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const bookings = useBookings();
  const payments = usePayments();
  const cancelBooking = useAppStore((state) => state.cancelBooking);
  const booking = bookings.find((item) => item.id === params.id);

  if (!booking) {
    return (
      <AppScreen title="Booking not found">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            We couldn&apos;t find this booking.
          </HeroText>
          <AppButton
            label="Back to bookings"
            className="mt-6"
            onPress={() => router.replace('/player/bookings')}
          />
        </AppCard>
      </AppScreen>
    );
  }

  const stringItem = getStringById(booking.stringId);
  const admin = getAdminById(booking.adminId);
  const bookingPayments = payments.filter((item) => item.bookingId === booking.id);
  const canEditBeforePayment = booking.paymentStatus !== 'paid';

  return (
    <AppScreen
      title={`Booking ${booking.id}`}
      subtitle="Booking info, payment info, drop-off details, and service actions in one player view."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
              Service status
            </HeroText>
            <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-white">
              {formatBookingStatus(booking.status)}
            </HeroText>
            <HeroText className="mt-2 text-sm text-primary-100">
              Drop-off on {booking.dropOffDate} at {booking.dropOffTime}
            </HeroText>
          </View>
          <AppChip
            label={formatPaymentStatus(booking.paymentStatus)}
            variant={getPaymentStatusVariant(booking.paymentStatus)}
          />
        </View>
      </AppCard>

      <AppSection eyebrow="Overview" title="Quick facts">
        <View className="flex-row gap-3">
          <AppCard variant="elevated" className="flex-1" padding="md">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
              Booking
            </HeroText>
            <AppChip
              label={formatBookingStatus(booking.status)}
              variant={getBookingStatusVariant(booking.status)}
              className="mt-3 self-start"
            />
          </AppCard>
          <AppCard variant="elevated" className="flex-1" padding="md">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
              Payment
            </HeroText>
            <AppChip
              label={formatPaymentStatus(booking.paymentStatus)}
              variant={getPaymentStatusVariant(booking.paymentStatus)}
              className="mt-3 self-start"
            />
          </AppCard>
        </View>
      </AppSection>

      <AppSection eyebrow="Booking info" title="String and racket setup">
        <AppDetailList
          items={[
            {
              label: 'String',
              value: `${stringItem?.brand ?? ''} ${stringItem?.model ?? ''}`.trim(),
            },
            {
              label: 'Racket',
              value: `${booking.racketBrand} ${booking.racketModel}`,
            },
            {
              label: 'Requested tension',
              value: `${booking.requestedTension} lbs`,
            },
            {
              label: 'Admin desk',
              value: admin?.businessName ?? 'Assigned shop',
            },
          ]}
        />
      </AppSection>

      <AppSection eyebrow="Drop-off" title="Arrival and check-in">
        <View className="gap-3">
          <AppCard variant="subtle" padding="md">
            <View className="flex-row items-center gap-3">
              <QrCode size={18} color="#2F64B6" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                Check-in reference: {booking.checkInReference}. Show this or the booking QR at the counter during drop-off.
              </HeroText>
            </View>
          </AppCard>
          <AppCard variant="subtle" padding="md">
            <View className="flex-row items-center gap-3">
              <TimerReset size={18} color="#22766D" />
              <HeroText className="flex-1 text-sm leading-6 text-neutral-600">
                Queue position is currently #{booking.queuePosition}. Service updates appear on the tracking timeline as the admin desk updates your order.
              </HeroText>
            </View>
          </AppCard>
        </View>
      </AppSection>

      <AppSection eyebrow="Payment info" title="Pricing breakdown">
        <AppDetailList
          items={[
            { label: 'String fee', value: formatCurrency(booking.stringFee) },
            { label: 'Service fee', value: formatCurrency(booking.serviceFee) },
            { label: 'Wallet used', value: formatCurrency(booking.walletUsed) },
            { label: 'Amount paid', value: formatCurrency(booking.amountPaid) },
            { label: 'Total amount', value: formatCurrency(booking.totalAmount) },
            {
              label: 'Payment records',
              value: (
                <View className="mt-1 gap-2 md:items-end">
                  {bookingPayments.map((payment) => (
                    <HeroText key={payment.id} className="text-sm leading-6 text-neutral-700 md:text-right">
                      {formatPaymentMethod(payment.method)} • {formatCurrency(payment.amount)} •{' '}
                      {formatPaymentStatus(payment.status)}
                    </HeroText>
                  ))}
                </View>
              ),
            },
          ]}
        />
      </AppSection>

      <AppSection eyebrow="Rule" title="Booking policy">
        <AppCard variant="highlighted" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-700">
            {booking.paymentRuleNote}
          </HeroText>
        </AppCard>
      </AppSection>

      {booking.notes ? (
        <AppSection eyebrow="Notes" title="Service instructions">
          <AppCard variant="highlighted" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-700">{booking.notes}</HeroText>
          </AppCard>
        </AppSection>
      ) : null}

      <View className="mb-12 mt-8 gap-3">
        {canEditBeforePayment ? (
          <>
            <AppButton
              label="Continue payment"
              size="lg"
              onPress={() => router.push(`/player/payments/${booking.id}`)}
            />
            <View className="flex-row gap-3">
              <AppButton
                label="Reschedule"
                variant="outline"
                size="lg"
                className="flex-1"
                onPress={() => router.push(`/player/bookings/new?stringId=${booking.stringId}`)}
              />
              <AppButton
                label="Cancel booking"
                variant="ghost"
                size="lg"
                className="flex-1"
                onPress={() => cancelBooking(booking.id)}
              />
            </View>
          </>
        ) : null}

        <View className="flex-row gap-3">
          <AppButton
            label="View tracking"
            variant={canEditBeforePayment ? 'outline' : 'primary'}
            size="lg"
            className="flex-1"
            onPress={() => router.push(`/player/bookings/${booking.id}/tracking`)}
          />
          <AppButton
            label="Check-in"
            variant="ghost"
            size="lg"
            className="flex-1"
            onPress={() => router.push('/player/check-in')}
          />
        </View>

        <AppButton
          label="Request admin support"
          variant="ghost"
          size="lg"
          leadingIcon={<MessageSquareText size={18} color="#475569" />}
          onPress={() => router.push('/player/chat/chat-001')}
        />
      </View>
    </AppScreen>
  );
}
