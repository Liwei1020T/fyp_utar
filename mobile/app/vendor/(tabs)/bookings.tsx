import React, { useMemo, useState } from 'react';
import { FlatList, View } from 'react-native';
import { useRouter } from 'expo-router';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { BookingCard } from '../../../components/booking/BookingCard';
import { useBookings, useCurrentUser } from '../../../store/appStore';
import { getStringById, getUserById } from '../../../services/mockAppService';
import type { BookingStatus } from '../../../types/domain';
import { formatBookingStatus } from '../../../lib/formatters';

export default function VendorBookingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const bottomContentInset = useBottomContentInset(16);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<BookingStatus | 'all'>('all');

  if (!user || user.role !== 'vendor') {
    return null;
  }

  const filtered = useMemo(
    () =>
      bookings.filter((item) => {
        if (item.vendorId !== user.id) {
          return false;
        }
        const matchesFilter = filter === 'all' || item.status === filter;
        const matchesSearch = `${item.id} ${item.racketBrand} ${item.racketModel}`.toLowerCase().includes(search.toLowerCase());
        return matchesFilter && matchesSearch;
      }),
    [bookings, filter, search, user.id]
  );

  return (
    <AppScreen title="Vendor bookings" subtitle="Operational list of shop bookings with filters, search, and quick drill-in." scrollable={false}>
      <FlatList
        className="flex-1"
        data={filtered}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="gap-4 pb-6">
            <AppInput
              className="mb-0"
              placeholder="Search by booking or racket..."
              value={search}
              onChangeText={setSearch}
              containerClassName="shadow-none"
            />
            <View className="flex-row flex-wrap gap-2">
              {(['all', 'pending_payment', 'awaiting_dropoff', 'in_progress', 'ready_for_collection', 'completed'] as const).map((item) => (
                <AppChip
                  key={item}
                  label={item === 'all' ? 'All' : formatBookingStatus(item)}
                  size="md"
                  variant={filter === item ? 'primary' : 'neutral'}
                  onPress={() => setFilter(item)}
                />
              ))}
            </View>
          </View>
        }
        renderItem={({ item }) => {
          const player = getUserById(item.playerId);
          const stringItem = getStringById(item.stringId);

          return (
            <View className="mb-4">
              <BookingCard
                booking={item}
                stringLabel={stringItem ? `${stringItem.brand} ${stringItem.model}` : 'Selected string'}
                vendorLabel={player?.name}
                onPress={() => router.push(`/vendor/bookings/${item.id}`)}
              />
            </View>
          );
        }}
      />
    </AppScreen>
  );
}
