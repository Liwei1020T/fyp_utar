import * as React from 'react';
import { useMemo, useState } from 'react';
import { FlatList, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Search, Info } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppCard } from '../../../components/ui/AppCard';
import { AppButton } from '../../../components/ui/AppButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppSelect } from '../../../components/ui/AppSelect';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { BookingCard } from '../../../components/booking/BookingCard';
import {
  useAppStore,
  useBookings,
  useCurrentUser,
  useStrings,
} from '../../../store/appStore';
import type { BookingStatus, PlayerProfile } from '../../../types/domain';
import { formatBookingOrderCode, formatBookingStatus } from '../../../lib/formatters';

const filters: (BookingStatus | 'all')[] = [
  'all',
  'awaiting_dropoff',
  'in_progress',
  'ready_for_collection',
  'completed',
];

function normalizeStoreText(value: unknown) {
  return typeof value === 'string' ? value.trim() : '';
}

export default function BookingsListScreen() {
  const user = useCurrentUser();

  if (!user || user.role !== 'player') {
    return null;
  }

  return <BookingsListContent user={user} />;
}

function BookingsListContent({ user }: { user: PlayerProfile }) {
  const router = useRouter();
  const bookings = useBookings();
  const strings = useStrings();
  const storeSettings = useAppStore((state) => state.storeSettings);
  const bottomContentInset = useBottomContentInset(24);
  const [filter, setFilter] = useState<BookingStatus | 'all'>('all');
  const [search, setSearch] = useState('');

  const filteredBookings = useMemo(
    () =>
      bookings.filter((item) => {
        if (item.playerId !== user.id) {
          return false;
        }

        const matchesFilter = filter === 'all' || item.status === filter;

        const matchesSearch =
          `${item.id} ${item.orderCode ?? formatBookingOrderCode(item.id)} ${item.racketBrand} ${item.racketModel}`
            .toLowerCase()
            .includes(search.toLowerCase());

        return matchesFilter && matchesSearch;
      }),
    [bookings, filter, search, user.id]
  );

  const activeCount = useMemo(
    () => bookings.filter((b) => b.playerId === user.id && ['awaiting_dropoff', 'in_progress'].includes(b.status)).length,
    [bookings, user.id]
  );

  const readyCount = useMemo(
    () => bookings.filter((b) => b.playerId === user.id && b.status === 'ready_for_collection').length,
    [bookings, user.id]
  );
  const hasActiveFilters = filter !== 'all' || search.trim().length > 0;

  return (
    <AppScreen
      headerVariant="primary"
      title="My bookings"
      subtitle="Track your racket services and status updates."
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={filteredBookings}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        scrollIndicatorInsets={{ bottom: bottomContentInset }}
        contentContainerStyle={{ paddingBottom: bottomContentInset }}
        ListHeaderComponent={
          <View className="gap-2 pb-3">
            <View className="flex-row items-center gap-2 rounded-[14px] border border-secondary-100 bg-secondary-50 px-3 py-1.5">
              <Info size={14} color="#2F64B6" />
              <HeroText className="text-[11px] font-semibold text-primary-900">
                {activeCount} active bookings • {readyCount} ready for collection
              </HeroText>
            </View>

            <AppInput
              variant="minimal"
              className="mb-0"
              placeholder="Search ID or racket..."
              value={search}
              onChangeText={setSearch}
              leftAdornment={<Search size={18} color="#94A3B8" strokeWidth={2.5} />}
              inputClassName="text-[15px] font-medium"
            />

            <AppSelect
              label="Booking status"
              value={filter}
              options={filters.map((item) => ({
                id: item,
                label: item === 'all' ? 'All bookings' : formatBookingStatus(item),
              }))}
              onChange={(value) => setFilter(value as typeof filter)}
            />
          </View>
        }
        renderItem={({ item }) => {
          const stringItem = strings.find((entry) => entry.id === item.stringId);
          const adminLabel =
            normalizeStoreText(storeSettings?.storeName) ||
            'Assigned shop';

          return (
            <BookingCard
              booking={item}
              stringLabel={stringItem ? `${stringItem.brand} ${stringItem.model}` : 'Selected string'}
              adminLabel={adminLabel}
              onPress={() => router.push(`/player/bookings/${item.id}`)}
              onNextStepPress={
                item.status === 'confirmed' || item.status === 'awaiting_dropoff'
                  ? () => router.push(`/player/check-in?bookingId=${item.id}`)
                  : undefined
              }
            />
          );
        }}
        ListEmptyComponent={
            <AppCard variant="subtle" className="mt-3 items-center" padding="lg">
            <HeroText className="text-base font-semibold text-neutral-800">
              {hasActiveFilters ? 'No bookings match these filters' : 'No bookings yet'}
            </HeroText>
            <HeroText className="mt-2 text-center text-sm leading-6 text-neutral-500">
              {hasActiveFilters
                ? 'Clear a filter or search for another booking.'
                : 'Start a booking to see your service progress here.'}
            </HeroText>
            {hasActiveFilters ? (
              <AppButton
                label="Clear filters"
                variant="outline"
                className="mt-4"
                onPress={() => {
                  setFilter('all');
                  setSearch('');
                }}
              />
            ) : (
              <AppButton
                label="Start a booking"
                className="mt-4"
                onPress={() => router.push('/player/bookings/new')}
              />
            )}
          </AppCard>
        }
      />
    </AppScreen>
  );
}
