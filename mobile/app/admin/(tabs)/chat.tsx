import React, { useMemo, useState } from 'react';
import { FlatList, View } from 'react-native';
import { useRouter } from 'expo-router';
import { AppChip } from '../../../components/ui/AppChip';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { ConversationCard } from '../../../components/chat/ConversationCard';
import { useConversations, useCurrentUser } from '../../../store/appStore';
import { formatConversationMode } from '../../../lib/formatters';

export default function AdminChatQueueScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const conversations = useConversations();
  const bottomContentInset = useBottomContentInset(16);
  const [filter, setFilter] = useState<'all' | 'waiting_admin' | 'admin_joined' | 'resolved' | 'closed'>('all');

  if (!user || user.role !== 'admin') {
    return null;
  }

  const adminConversations = useMemo(
    () =>
      conversations.filter((item) => {
        if (item.adminId !== user.id) {
          return false;
        }
        return filter === 'all' ? true : item.mode === filter;
      }),
    [conversations, filter, user.id]
  );

  return (
    <AppScreen headerVariant="primary" title="Chat queue" subtitle="Service-related conversations assigned to the shop admin desk." scrollable={false}>
      <FlatList
        className="flex-1"
        data={adminConversations}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="flex-row flex-wrap gap-2 pb-6">
            {(['all', 'waiting_admin', 'admin_joined', 'resolved', 'closed'] as const).map((item) => (
                <AppChip
                  key={item}
                  label={item === 'all' ? 'All' : formatConversationMode(item)}
                  size="md"
                  variant={filter === item ? 'primary' : 'neutral'}
                  onPress={() => setFilter(item)}
              />
            ))}
          </View>
        }
        renderItem={({ item }) => (
          <View className="mb-4">
            <ConversationCard conversation={item} onPress={() => router.push(`/admin/chat/${item.id}`)} />
          </View>
        )}
      />
    </AppScreen>
  );
}
