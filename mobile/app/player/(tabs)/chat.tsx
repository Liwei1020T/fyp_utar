import React, { useCallback, useState } from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { ChevronRight, MessageCircleMore } from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppButton } from '../../../components/ui/AppButton';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { HeroText } from '../../../components/ui/heroui';
import { ConversationCard } from '../../../components/chat/ConversationCard';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useConversations,
  useCurrentUser,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendConversationToConversation } from '../../../services/backendMappers';

const quickPrompts = [
  {
    label: 'Ask about my booking',
    message: 'Can you help me with my booking?',
  },
  {
    label: 'Ask about pickup',
    message: 'Can you confirm my pickup or drop-off details?',
  },
  {
    label: 'Get payment help',
    message: 'I need help with my booking payment.',
  },
] as const;

export default function PlayerChatThreadsScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(18);
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const conversations = useConversations();
  const setLiveConversations = useAppStore((state) => state.setLiveConversations);
  const upsertLiveConversation = useAppStore(
    (state) => state.upsertLiveConversation,
  );
  const [isRefreshing, setIsRefreshing] = useState(Boolean(token));
  const [isRequestingSupport, setIsRequestingSupport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshConversations = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsRefreshing(true);
    setError(null);
    try {
      const response = await backendApi.listPlayerConversations(token);
      setLiveConversations(
        response.map((conversation) =>
          mapBackendConversationToConversation(
            conversation,
            bookings.find((booking) => booking.id === conversation.booking_id),
          ),
        ),
      );
    } catch (loadError) {
      setError(
        loadError instanceof BackendApiError
          ? loadError.message
          : 'Failed to load human support conversations.',
      );
    } finally {
      setIsRefreshing(false);
    }
  }, [bookings, setLiveConversations, token]);

  useFocusEffect(
    useCallback(() => {
      void refreshConversations();
    }, [refreshConversations]),
  );

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerConversations = conversations.filter((item) => item.playerId === user.id);
  const openConversation = playerConversations.find(
    (item) => item.mode !== 'resolved' && item.mode !== 'closed',
  );

  const routeToConversation = (conversationId: string, message?: string) => {
    const draft = message?.trim();
    router.push(
      draft
        ? `/player/chat/${conversationId}?draft=${encodeURIComponent(draft)}`
        : `/player/chat/${conversationId}`,
    );
  };

  const openSupportThread = async (message?: string) => {
    if (openConversation) {
      routeToConversation(openConversation.id, message);
      return;
    }
    if (!token) {
      setError('Sign in again to contact human support.');
      return;
    }
    setIsRequestingSupport(true);
    setError(null);
    try {
      const response = await backendApi.requestGeneralSupport(token);
      const mapped = mapBackendConversationToConversation(response, undefined);
      upsertLiveConversation(mapped);
      routeToConversation(mapped.id, message);
    } catch (supportError) {
      setError(
        supportError instanceof BackendApiError
          ? supportError.message
          : 'Failed to open human support.',
      );
    } finally {
      setIsRequestingSupport(false);
    }
  };

  return (
    <AppScreen
      headerVariant="primary"
      title="Human support"
      subtitle="Message the shop with or without an existing booking."
      scrollable={false}
    >
      <FlatList
        className="flex-1"
        data={playerConversations}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        refreshing={isRefreshing}
        onRefresh={() => void refreshConversations()}
        ListHeaderComponent={
          <View className="gap-6 pb-6">
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

            <AppCard variant="dark" padding="lg">
              <View className="flex-row items-start justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
                    Persisted support
                  </HeroText>
                  <HeroText className="mt-2 text-[26px] font-bold tracking-tight text-white">
                    Get help from the shop desk.
                  </HeroText>
                  <HeroText className="mt-2 text-sm leading-6 text-primary-100">
                    Existing booking questions keep their order context. General questions stay in a separate support thread.
                  </HeroText>
                </View>
                <View className="h-12 w-12 items-center justify-center rounded-2xl bg-white/12">
                  <MessageCircleMore size={22} color="white" />
                </View>
              </View>
              <AppButton
                label={openConversation ? 'Open support thread' : 'Contact human support'}
                variant="secondary"
                size="sm"
                className="mt-6 self-start"
                isLoading={isRequestingSupport}
                onPress={() => void openSupportThread()}
              />
            </AppCard>

            <AppSection eyebrow="Quick start" title="Prompt ideas" variant="compact" className="mt-0">
              <AppCard variant="subtle" padding="none">
                {quickPrompts.map((prompt, index) => (
                  <View
                    key={prompt.label}
                    className={index < quickPrompts.length - 1 ? 'border-b border-separator' : ''}
                  >
                    <Pressable
                      accessibilityRole="button"
                      accessibilityLabel={prompt.label}
                      accessibilityHint="Open support with this message ready to review"
                      disabled={isRequestingSupport}
                      onPress={() => void openSupportThread(prompt.message)}
                      className="min-h-12 flex-row items-center gap-3 px-3 py-2"
                    >
                      <View className="h-8 w-8 items-center justify-center rounded-full bg-primary-50">
                        <MessageCircleMore size={16} color="#2F64B6" />
                      </View>
                      <HeroText className="flex-1 text-sm font-semibold text-neutral-800">
                        {prompt.label}
                      </HeroText>
                      <ChevronRight size={18} color="#94A3B8" />
                    </Pressable>
                  </View>
                ))}
              </AppCard>
            </AppSection>
          </View>
        }
        renderItem={({ item }) => (
          <View className="mb-4">
            <ConversationCard conversation={item} onPress={() => router.push(`/player/chat/${item.id}`)} />
          </View>
        )}
        ListEmptyComponent={
          <AppCard variant="subtle" className="mb-4" padding="md">
            <HeroText className="text-base font-semibold text-neutral-900">
              {isRefreshing ? 'Loading human support...' : 'No support threads yet'}
            </HeroText>
            <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
              {error
                ? 'Retry to load your persisted support threads.'
                : 'Use Contact human support to start a conversation with the shop desk.'}
            </HeroText>
          </AppCard>
        }
      />
    </AppScreen>
  );
}
