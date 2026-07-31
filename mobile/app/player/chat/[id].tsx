import React, { useCallback, useState } from 'react';
import { View } from 'react-native';
import {
  useFocusEffect,
  useLocalSearchParams,
  useRouter,
} from 'expo-router';
import { SendHorizontal } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { ChatBubble } from '../../../components/chat/ChatBubble';
import { formatConversationMode } from '../../../lib/formatters';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useConversations,
  useCurrentUser,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendConversationToConversation } from '../../../services/backendMappers';
import type { BackendBookingConversation } from '../../../types/backend';

const POLL_INTERVAL_MS = 15_000;

function hasUnreadAdminMessages(conversation: BackendBookingConversation) {
  return conversation.messages.some(
    (message) =>
      message.author_role === 'admin' &&
      (conversation.player_last_read_at === null ||
        message.created_at === null ||
        message.created_at > conversation.player_last_read_at),
  );
}

export default function PlayerChatDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const conversationId = params.id;
  const user = useCurrentUser();
  const conversations = useConversations();
  const bookings = useBookings();
  const token = useBackendAccessToken();
  const upsertLiveConversation = useAppStore(
    (state) => state.upsertLiveConversation,
  );
  const conversation = conversations.find(
    (item) => item.id === conversationId && item.playerId === user?.id,
  );
  const [draft, setDraft] = useState('');
  const [isLoading, setIsLoading] = useState(
    Boolean(token && conversationId && !conversation),
  );
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheConversation = useCallback(
    (response: BackendBookingConversation) => {
      const mapped = mapBackendConversationToConversation(
        response,
        bookings.find((booking) => booking.id === response.booking_id),
      );
      upsertLiveConversation(mapped);
    },
    [bookings, upsertLiveConversation],
  );

  const refreshConversation = useCallback(
    async (showLoading = false) => {
      if (!token || !conversationId || user?.role !== 'player') {
        return;
      }

      if (showLoading) {
        setIsLoading(true);
      }
      setError(null);
      try {
        let response = await backendApi.fetchPlayerConversation(
          token,
          conversationId,
        );
        if (hasUnreadAdminMessages(response)) {
          response = await backendApi.markPlayerConversationRead(
            token,
            conversationId,
          );
        }
        cacheConversation(response);
      } catch (loadError) {
        setError(
          loadError instanceof BackendApiError
            ? loadError.message
            : 'Failed to load this conversation.',
        );
      } finally {
        if (showLoading) {
          setIsLoading(false);
        }
      }
    },
    [cacheConversation, conversationId, token, user?.role],
  );

  useFocusEffect(
    useCallback(() => {
      if (!token || !conversationId || user?.role !== 'player') {
        return;
      }

      void refreshConversation(true);
      const intervalId = setInterval(
        () => void refreshConversation(),
        POLL_INTERVAL_MS,
      );
      return () => clearInterval(intervalId);
    }, [conversationId, refreshConversation, token, user?.role]),
  );

  if (!user || user.role !== 'player') {
    return null;
  }

  const sendMessage = async (message: string) => {
    const body = message.trim();
    if (!body || !token || !conversationId || !conversation) {
      return;
    }
    if (conversation.mode === 'resolved' || conversation.mode === 'closed') {
      setError('This conversation is no longer open for replies.');
      return;
    }

    setIsSending(true);
    setError(null);
    try {
      const response = await backendApi.sendPlayerConversationMessage(
        token,
        conversationId,
        { body },
      );
      cacheConversation(response);
      setDraft('');
    } catch (sendError) {
      setError(
        sendError instanceof BackendApiError
          ? sendError.message
          : 'Failed to send message.',
      );
    } finally {
      setIsSending(false);
    }
  };

  if (!conversation) {
    return (
      <AppScreen
        headerVariant="secondary"
        title="Conversation unavailable"
        subtitle="Return to booking support or retry this exact conversation link."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-base font-semibold text-neutral-900">
            {isLoading ? 'Loading conversation...' : 'Conversation not found'}
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            {isLoading
              ? 'Fetching the persisted player and shop message history.'
              : error ??
                (conversationId
                  ? 'This conversation does not exist or is not available to this player.'
                  : 'The conversation link is missing its booking identifier.')}
          </HeroText>
          <View className="mt-4 gap-3">
            {!isLoading && token && conversationId ? (
              <AppButton
                label="Retry"
                variant="outline"
                onPress={() => void refreshConversation(true)}
              />
            ) : null}
            <AppButton
              label="Back to booking support"
              onPress={() => router.replace('/player/chat')}
            />
          </View>
        </AppCard>
      </AppScreen>
    );
  }

  const isClosed =
    conversation.mode === 'resolved' || conversation.mode === 'closed';
  const canReply = Boolean(token && !isClosed && !isSending);

  return (
    <AppScreen
      headerVariant="secondary"
      title={conversation.title}
      subtitle="Player and shop replies are persisted in the linked booking."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="dark" padding="lg">
        <View className="flex-row items-center justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-100">
              Conversation mode
            </HeroText>
            <HeroText className="mt-2 text-2xl font-bold text-white">
              {formatConversationMode(conversation.mode)}
            </HeroText>
          </View>
          <AppChip label={conversation.statusLabel} variant="secondary" />
        </View>
      </AppCard>

      {error ? (
        <AppCard
          variant="subtle"
          className="border border-red-100"
          padding="md"
        >
          <HeroText className="text-sm font-medium leading-6 text-red-600">
            {error}
          </HeroText>
          {token ? (
            <AppButton
              label="Refresh conversation"
              variant="outline"
              className="mt-4"
              onPress={() => void refreshConversation()}
            />
          ) : null}
        </AppCard>
      ) : null}

      <AppSection
        eyebrow="Quick prompts"
        title="Suggested next messages"
        variant="compact"
      >
        <View className="flex-row flex-wrap gap-2">
          {conversation.quickPrompts.map((item) => (
            <AppChip
              key={item}
              label={item}
              size="md"
              variant="neutral"
              onPress={canReply ? () => void sendMessage(item) : undefined}
            />
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Messages" title="Thread activity">
        <View className="gap-4">
          {conversation.messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))}
          {conversation.messages.length === 0 ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-600">
                No messages yet. Send the first booking support message below.
              </HeroText>
            </AppCard>
          ) : null}
        </View>
      </AppSection>

      {!token || isClosed ? (
        <AppCard variant="subtle" className="mb-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            {!token
              ? 'Your player session expired. Sign in again to send messages.'
              : 'This conversation is closed for player replies.'}
          </HeroText>
        </AppCard>
      ) : (
        <AppSection eyebrow="Composer" title="Reply in this thread" className="mb-8">
          <AppInput
            className="mb-2"
            placeholder="Type a message to the shop desk..."
            accessibilityLabel="Message to the shop desk"
            value={draft}
            onChangeText={setDraft}
            multiline
            inputClassName="min-h-24"
          />
          <AppButton
            label="Send message"
            size="lg"
            isLoading={isSending}
            isDisabled={!draft.trim()}
            leadingIcon={<SendHorizontal size={18} color="white" />}
            onPress={() => void sendMessage(draft)}
          />
        </AppSection>
      )}
    </AppScreen>
  );
}
