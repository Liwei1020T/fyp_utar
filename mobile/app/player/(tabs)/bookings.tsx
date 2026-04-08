import React, { useMemo, useState } from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Plus, Search, ChevronLeft } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { BookingCard } from '../../../components/booking/BookingCard';
import { useBookings, useCurrentUser } from '../../../store/appStore';
import { getAdminById, getStringById } from '../../../services/mockAppService';
import type { BookingStatus } from '../../../types/domain';
import { formatBookingStatus } from '../../../lib/formatters';

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
  const bottomContentInset = useBottomContentInset(18);
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
        const matchesFilter = filter === 'all' || item.status === filter;
        const matchesSearch =
          `${item.id} ${item.racketBrand} ${item.racketModel}`.toLowerCase().includes(search.toLowerCase());
        return matchesFilter && matchesSearch;
      }),
    [bookings, filter, search, user.id]
  );

  return (
    <AppScreen
      title="My bookings"
      subtitle="Track drop-off windows, admin updates, and service progress from one list."
      headerLeft={
        router.canGoBack() ? (
          <AppIconButton
            icon={<ChevronLeft size={20} color="#111827" />}
            accessibilityLabel="Go back"
            onPress={() => router.back()}
          />
        ) : undefined
      }
      headerRight={
        <AppIconButton
          icon={<Plus size={20} color="white" />}
          accessibilityLabel="Create a new booking"
          variant="primary"
          onPress={() => router.push('/player/bookings/new')}
        />
      }
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={filteredBookings}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        scrollIndicatorInsets={{ bottom: bottomContentInset }}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="gap-6 pb-6">
            <AppCard variant="highlighted" padding="lg">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
                Booking center
              </HeroText>
              <HeroText className="mt-2 text-[24px] font-bold tracking-tight text-neutral-950">
                Keep every drop-off and service status in view.
              </HeroText>
              <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
                Filter by stage and jump into booking detail or tracking pages without losing context.
              </HeroText>
            </AppCard>

            <AppInput
              className="mb-0"
              placeholder="Search by booking ID or racket..."
              value={search}
              onChangeText={setSearch}
              leftAdornment={<Search size={18} color="#94A3B8" />}
              containerClassName="shadow-none"
            />

            <View className="flex-row flex-wrap gap-2">
              {filters.map((item) => (
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
          const stringItem = getStringById(item.stringId);
          const admin = getAdminById(item.adminId);

          return (
            <View className="mb-4">
              <BookingCard
                booking={item}
                stringLabel={stringItem ? `${stringItem.brand} ${stringItem.model}` : 'Selected string'}
                adminLabel={admin?.businessName}
                onPress={() => router.push(`/player/bookings/${item.id}`)}
              />
            </View>
          );
        }}
        ListEmptyComponent={
          <AppCard variant="subtle" className="mt-4 items-center" padding="lg">
            <HeroText className="text-base font-semibold text-neutral-800">
              No bookings in this view
            </HeroText>
            <HeroText className="mt-2 text-center text-sm leading-6 text-neutral-500">
              Adjust your filters or start a new booking to build the next restring flow.
            </HeroText>
          </AppCard>
        }
      />
    </AppScreen>
  );
}
