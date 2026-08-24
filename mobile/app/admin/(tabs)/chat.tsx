import React, { useCallback, useMemo, useState } from 'react';
import { FlatList, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppSelect } from '../../../components/ui/AppSelect';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { ConversationCard } from '../../../components/chat/ConversationCard';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useConversations,
  useCurrentUser,
} from '../../../store/appStore';
import { formatConversationMode } from '../../../lib/formatters';
import type { AdminProfile } from '../../../types/domain';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendConversationToConversation } from '../../../services/backendMappers';

export default function AdminChatQueueScreen() {
  const user = useCurrentUser();

  if (!user || user.role !== 'admin') {
    return null;
  }

  return <AdminChatQueueContent user={user} />;
}

function AdminChatQueueContent({ user }: { user: AdminProfile }) {
  const router = useRouter();
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const conversations = useConversations();
  const setLiveConversations = useAppStore((state) => state.setLiveConversations);
  const bottomContentInset = useBottomContentInset(16);
  const [filter, setFilter] = useState<'all' | 'waiting_admin' | 'admin_joined' | 'resolved' | 'closed'>('all');
  const [isRefreshing, setIsRefreshing] = useState(Boolean(token));
  const [error, setError] = useState<string | null>(null);

  const refreshConversations = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsRefreshing(true);
    setError(null);
    try {
      const response = await backendApi.adminListConversations(token);
      setLiveConversations(
        response.map((conversation) =>
          mapBackendConversationToConversation(
            conversation,
            bookings.find((booking) => booking.id === conversation.booking_id),
            user.id,
          ),
        ),
      );
    } catch (loadError) {
      setError(
        loadError instanceof BackendApiError
          ? loadError.message
          : 'Failed to load the admin chat queue.',
      );
    } finally {
      setIsRefreshing(false);
    }
  }, [bookings, setLiveConversations, token, user.id]);

  useFocusEffect(
    useCallback(() => {
      void refreshConversations();
    }, [refreshConversations]),
  );

  const adminConversations = useMemo(
    () =>
      conversations.filter((item) => {
        if (item.adminId !== user.id) {
          return false;
        }
        return filter === 'all' || item.mode === filter;
      }),
    [conversations, filter, user.id]
  );

  return (
    <AppScreen tone="admin" headerVariant="primary" compactHeader title="Chat queue" subtitle="Booking and general support conversations for the shop admin desk." scrollable={false}>
      <FlatList
        className="flex-1"
        data={adminConversations}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        refreshing={isRefreshing}
        onRefresh={() => void refreshConversations()}
        ListHeaderComponent={
          <View className="gap-3 pb-4">
            {error ? (
              <AppCard
                variant="subtle"
                className="border border-red-100"
                padding="md"
              >
                <HeroText className="text-sm font-medium leading-6 text-red-600">
                  {error}
                </HeroText>
                <AppButton
                  label="Retry"
                  variant="outline"
                  className="mt-4"
                  onPress={() => void refreshConversations()}
                />
              </AppCard>
            ) : null}
            <AppSelect
              label="Conversation status"
              value={filter}
              options={(['all', 'waiting_admin', 'admin_joined', 'resolved', 'closed'] as const).map((item) => ({
                id: item,
                label: item === 'all' ? 'All conversations' : formatConversationMode(item),
              }))}
              onChange={(id) => setFilter(id as typeof filter)}
            />
          </View>
        }
        renderItem={({ item }) => (
          <View className="mb-2">
            <ConversationCard conversation={item} onPress={() => router.push(`/admin/chat/${item.id}`)} />
          </View>
        )}
        ListEmptyComponent={
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-base font-semibold text-neutral-900">
              {isRefreshing ? 'Loading chat queue...' : 'No conversations found'}
            </HeroText>
            <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
              {error
                ? 'Retry to load persisted player conversations.'
                : filter === 'all'
                  ? 'Player support requests will appear here.'
                  : `No ${formatConversationMode(filter).toLowerCase()} conversations.`}
            </HeroText>
          </AppCard>
        }
      />
    </AppScreen>
  );
}
