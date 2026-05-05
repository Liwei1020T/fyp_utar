import React, { useMemo, useState } from 'react';
import { FlatList, ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { CalendarDays, Search } from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { getBookingStatusVariant } from '../../../components/ui/theme';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { useBookings, useCurrentUser } from '../../../store/appStore';
import { getStringById } from '../../../services/mockAppService';
import type { Booking, BookingStatus } from '../../../types/domain';
import {
  formatBookingOrderCode,
  formatBookingStatus,
  formatCurrency,
  formatDateLabel,
  formatLocalDateInputValue,
} from '../../../lib/formatters';

const FILTER_OPTIONS = [
  { value: 'all' as const, label: 'All' },
  { value: 'awaiting_dropoff' as const, label: 'Awaiting' },
  { value: 'in_progress' as const, label: 'In Progress' },
  { value: 'ready_for_collection' as const, label: 'Ready' },
  { value: 'completed' as const, label: 'Completed' },
];

const STATUS_PRIORITY: Record<BookingStatus, number> = {
  pending: 4,
  pending_payment: 4,
  confirmed: 1,
  awaiting_dropoff: 0,
  in_progress: 1,
  ready_for_collection: 2,
  completed: 3,
  cancelled: 5,
};

function getAdminActionLabel(status: BookingStatus) {
  switch (status) {
    case 'awaiting_dropoff':
    case 'confirmed':
      return 'Action: Receive racket at counter';
    case 'in_progress':
      return 'Action: Continue stringing';
    case 'ready_for_collection':
      return 'Action: Prepare for collection';
    case 'completed':
    case 'cancelled':
      return 'Action: No further action';
    case 'pending':
    case 'pending_payment':
      return 'Action: Follow up on booking confirmation';
    default:
      return 'Action: Review booking';
  }
}

function getQueueMetaLabel(booking: Booking) {
  if (booking.status === 'completed') {
    return 'Collected';
  }

  if (booking.status === 'ready_for_collection') {
    return 'Pickup ready';
  }

  if (booking.queuePosition > 0) {
    return `Queue #${booking.queuePosition}`;
  }

  return 'Queue open';
}

function compareBookings(a: Booking, b: Booking) {
  const priorityDelta = STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status];

  if (priorityDelta !== 0) {
    return priorityDelta;
  }

  return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
}

function AdminQueueCard({
  booking,
  onPress,
}: {
  booking: Booking;
  onPress: () => void;
}) {
  const stringItem = getStringById(booking.stringId);
  const orderCode = booking.orderCode ?? formatBookingOrderCode(booking.id);
  const stringLabel = stringItem
    ? `${stringItem.brand} ${stringItem.model}`
    : 'Selected string';
  const stringSpec = `${stringLabel} · ${booking.requestedTension} lbs`;

  return (
    <View className="mb-3.5">
      <AppCard variant="elevated" padding="sm" onPress={onPress}>
        <View className="gap-3">
          <View className="flex-row items-start justify-between gap-3">
            <View className="flex-1">
              <HeroText className="text-[10px] font-semibold uppercase tracking-[0.14em] text-neutral-400">
                Order {orderCode}
              </HeroText>
            </View>
            <AppChip
              label={formatBookingStatus(booking.status)}
              variant={getBookingStatusVariant(booking.status)}
              size="sm"
              className="shrink-0"
            />
          </View>

          <View className="gap-1.5">
            <HeroText className="text-[17px] font-bold tracking-tight text-neutral-950">
              {booking.racketBrand} {booking.racketModel}
            </HeroText>
            <HeroText className="text-[12px] font-medium leading-5 text-neutral-600">
              {stringSpec}
            </HeroText>
            <View className="flex-row flex-wrap items-center gap-x-2 gap-y-1">
              <HeroText className="text-[12px] font-semibold text-neutral-800">
                {formatCurrency(booking.totalAmount)}
              </HeroText>
              <HeroText className="text-[11px] font-semibold text-neutral-300">
                ·
              </HeroText>
              <CalendarDays size={12} color="#94A3B8" />
              <HeroText className="text-[11px] font-semibold text-neutral-500">
                {formatDateLabel(booking.dropOffDate)}
              </HeroText>
            </View>
          </View>

          <View className="flex-row items-center gap-3 rounded-[18px] border border-[#D9E6F4] bg-[#F4F8FD] px-3.5 py-2.5">
            <View className="flex-1 gap-0.5">
              <HeroText className="text-[11px] font-semibold text-primary-800">
                {getAdminActionLabel(booking.status)}
              </HeroText>
              <HeroText className="text-[10px] font-medium text-neutral-500">
                {getQueueMetaLabel(booking)}
              </HeroText>
            </View>
            <HeroText className="text-[11px] font-semibold text-primary-700">
              Open
            </HeroText>
          </View>
        </View>
      </AppCard>
    </View>
  );
}

export default function AdminBookingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const bottomContentInset = useBottomContentInset(16);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<BookingStatus | 'all'>('all');

  if (!user || user.role !== 'admin') {
    return null;
  }

  const adminBookings = useMemo(
    () => bookings.filter((item) => item.adminId === user.id && item.status !== 'cancelled'),
    [bookings, user.id]
  );

  const filtered = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return adminBookings
      .filter((item) => {
        const matchesFilter = filter === 'all' || item.status === filter;

        if (!matchesFilter) {
          return false;
        }

        if (!normalizedSearch) {
          return true;
        }

        const stringItem = getStringById(item.stringId);
        const haystack = [
          item.id,
          item.orderCode,
          item.racketBrand,
          item.racketModel,
          stringItem?.brand,
          stringItem?.model,
          formatBookingStatus(item.status),
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();

        return haystack.includes(normalizedSearch);
      })
      .sort(compareBookings);
  }, [adminBookings, filter, search]);

  const today = formatLocalDateInputValue(new Date());
  const todayCount = adminBookings.filter((item) => formatLocalDateInputValue(item.createdAt) === today).length;
  const inProgressCount = adminBookings.filter((item) => item.status === 'in_progress').length;
  const readyCount = adminBookings.filter((item) => item.status === 'ready_for_collection').length;

  return (
    <AppScreen
      tone="admin"
      headerVariant="primary"
      title="Admin bookings"
      subtitle="Mobile queue for counter and stringing operations."
      compactHeader
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={filtered}
        keyExtractor={(item) => item.id}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="gap-3 pb-4">
            <AppCard variant="subtle" padding="sm">
              <HeroText className="text-[13px] font-semibold tracking-tight text-neutral-700">
                Today: {todayCount} bookings · {inProgressCount} in progress · {readyCount} ready for collection
              </HeroText>
            </AppCard>

            <AppInput
              variant="minimal"
              className="mb-0"
              placeholder="Search order, racket, or string..."
              value={search}
              onChangeText={setSearch}
              leftAdornment={<Search size={18} color="#94A3B8" strokeWidth={2.5} />}
              inputClassName="text-[15px] font-medium"
            />

            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={{ gap: 8, paddingRight: 4 }}
            >
              {FILTER_OPTIONS.map((option) => (
                <AppChip
                  key={option.value}
                  label={option.label}
                  size="md"
                  variant={filter === option.value ? 'primary' : 'neutral'}
                  onPress={() => setFilter(option.value)}
                />
              ))}
            </ScrollView>
          </View>
        }
        ListEmptyComponent={
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-[15px] font-semibold tracking-tight text-neutral-900">
              No queue items found
            </HeroText>
            <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
              Try another search term or switch the status filter.
            </HeroText>
          </AppCard>
        }
        renderItem={({ item }) => (
          <AdminQueueCard
            booking={item}
            onPress={() => router.push(`/admin/bookings/${item.id}`)}
          />
        )}
      />
    </AppScreen>
  );
}
