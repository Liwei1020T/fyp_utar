import React, { useMemo, useState } from 'react';
import { FlatList, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Search, SlidersHorizontal } from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { BookingCard } from '../../../components/booking/BookingCard';
import { useBookings, useCurrentUser } from '../../../store/appStore';
import { getStringById, getUserById } from '../../../services/mockAppService';
import type { BookingStatus } from '../../../types/domain';
import { formatBookingStatus } from '../../../lib/formatters';

export default function AdminBookingsScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const bottomContentInset = useBottomContentInset(16);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<BookingStatus | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);

  if (!user || user.role !== 'admin') {
    return null;
  }

  const filtered = useMemo(
    () =>
      bookings.filter((item) => {
        if (item.adminId !== user.id) {
          return false;
        }
        const matchesFilter = filter === 'all' || item.status === filter;
        const matchesSearch = `${item.id} ${item.racketBrand} ${item.racketModel}`.toLowerCase().includes(search.toLowerCase());
        return matchesFilter && matchesSearch;
      }),
    [bookings, filter, search, user.id]
  );

  return (
    <AppScreen headerVariant="primary" title="Admin bookings" subtitle="Operational list of shop bookings with filters, search, and quick drill-in." scrollable={false}>
      <FlatList
        className="flex-1"
        data={filtered}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="gap-4 pb-6">
            <AppCard variant="highlighted" padding="md">
              <View className="flex-row items-center justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-base font-bold tracking-tight text-neutral-950">
                    Booking operations
                  </HeroText>
                  <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
                    Search quickly, filter by status, and drill into the counter queue.
                  </HeroText>
                </View>
                <View className="h-11 w-11 items-center justify-center rounded-[18px] bg-primary-50">
                  <SlidersHorizontal size={18} color="#2F64B6" />
                </View>
              </View>
            </AppCard>
            <View className="flex-row items-center gap-3">
              <AppInput
                variant="minimal"
                className="mb-0 flex-1"
                placeholder="Search by booking or racket..."
                value={search}
                onChangeText={setSearch}
                leftAdornment={<Search size={18} color="#94A3B8" strokeWidth={2.5} />}
                inputClassName="text-[15px] font-medium"
              />
              <AppIconButton
                icon={<SlidersHorizontal size={20} color="#475569" />}
                accessibilityLabel={showFilters ? 'Hide filters' : 'Show filters'}
                onPress={() => setShowFilters((current) => !current)}
                className="h-11 w-11 rounded-full border border-neutral-200 shadow-sm"
              />
            </View>
            {showFilters ? (
              <View className="flex-row flex-wrap gap-2">
                {(['all', 'awaiting_dropoff', 'in_progress', 'ready_for_collection', 'completed'] as const).map((item) => (
                  <AppChip
                    key={item}
                    label={item === 'all' ? 'All' : formatBookingStatus(item)}
                    size="md"
                    variant={filter === item ? 'primary' : 'neutral'}
                    onPress={() => setFilter(item)}
                  />
                ))}
              </View>
            ) : (
              <AppCard variant="subtle" padding="sm">
                <HeroText className="text-sm leading-5 text-neutral-600">
                  Showing {filter === 'all' ? 'all bookings' : formatBookingStatus(filter)}
                </HeroText>
              </AppCard>
            )}
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
                adminLabel={player?.name}
                onPress={() => router.push(`/admin/bookings/${item.id}`)}
              />
            </View>
          );
        }}
      />
    </AppScreen>
  );
}
