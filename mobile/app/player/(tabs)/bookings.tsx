import * as React from 'react';
import { useMemo, useState } from 'react';
import { FlatList, View, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Plus, Search, ChevronLeft, Info } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppSegmentedControl } from '../../../components/ui/AppSegmentedControl';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { BookingCard } from '../../../components/booking/BookingCard';
import { useBookings, useCurrentUser } from '../../../store/appStore';
import { getAdminById, getStringById } from '../../../services/mockAppService';
import type { BookingStatus } from '../../../types/domain';
import { formatBookingOrderCode, formatBookingStatus } from '../../../lib/formatters';

const filters: Array<BookingStatus | 'all'> = [
  'all',
  'awaiting_dropoff',
  'in_progress',
  'ready_for_collection',
  'completed',
];

export default function BookingsListScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();
  const bottomContentInset = useBottomContentInset(24);
  const [filter, setFilter] = useState<BookingStatus | 'all'>('all');
  const [search, setSearch] = useState('');

  if (!user || user.role !== 'player') {
    return null;
  }

  const filteredBookings = useMemo(
    () =>
      bookings.filter((item) => {
        if (item.playerId !== user.id) {
          return false;
        }

        // Apply status filter
        const matchesFilter = filter === 'all' || item.status === filter;

        // Apply search
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
          <View className="gap-3 pb-4">
            <View className="flex-row items-center gap-2 rounded-2xl bg-primary-50 px-4 py-2 border border-primary-100">
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

            <ScrollView 
              horizontal 
              showsHorizontalScrollIndicator={false}
              className="-mx-5 px-5"
              contentContainerStyle={{ gap: 8, paddingRight: 40 }}
            >
              {filters.map((item) => (
                <AppChip
                  key={item}
                  label={item === 'all' ? 'All' : formatBookingStatus(item)}
                  size="sm"
                  variant={filter === item ? 'primary' : 'neutral'}
                  onPress={() => setFilter(item)}
                />
              ))}
            </ScrollView>
          </View>
        }
        renderItem={({ item }) => {
          const stringItem = getStringById(item.stringId);
          const admin = getAdminById(item.adminId);

          return (
            <BookingCard
              booking={item}
              stringLabel={stringItem ? `${stringItem.brand} ${stringItem.model}` : 'Selected string'}
              adminLabel={admin?.businessName}
              onPress={() => router.push(`/player/bookings/${item.id}`)}
            />
          );
        }}
        ListEmptyComponent={
          <AppCard variant="subtle" className="mt-4 items-center" padding="lg">
            <HeroText className="text-base font-semibold text-neutral-800">
              No bookings found
            </HeroText>
            <HeroText className="mt-2 text-center text-sm leading-6 text-neutral-500">
              Adjust your filters or start a new booking.
            </HeroText>
          </AppCard>
        }
      />
    </AppScreen>
  );
}
