import React, { useCallback, useState } from 'react';
import { View } from 'react-native';
import {
  useFocusEffect,
  useLocalSearchParams,
  useRouter,
} from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { ChatBubble } from '../../../components/chat/ChatBubble';
import { formatBookingOrderCode } from '../../../lib/formatters';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useConversations,
  useCurrentUser,
  useStrings,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendConversationToConversation } from '../../../services/backendMappers';
import type { BackendBookingConversation } from '../../../types/backend';

const POLL_INTERVAL_MS = 15_000;

function hasUnreadPlayerMessages(conversation: BackendBookingConversation) {
  return conversation.messages.some(
    (message) =>
      message.author_role !== 'admin' &&
      (conversation.admin_last_read_at === null ||
        message.created_at === null ||
        message.created_at > conversation.admin_last_read_at),
  );
}

export default function AdminChatDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const conversationId = params.id;
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const conversations = useConversations();
  const bookings = useBookings();
  const strings = useStrings();
  const upsertLiveConversation = useAppStore(
    (state) => state.upsertLiveConversation,
  );
  const conversation = conversations.find(
    (item) =>
      item.id === conversationId &&
      (Boolean(token) || item.adminId === user?.id),
  );
  const [draft, setDraft] = useState('');
  const [isLoading, setIsLoading] = useState(
    Boolean(token && conversationId && !conversation),
  );
  const [activeAction, setActiveAction] = useState<
    'send' | 'resolve' | 'close' | null
  >(null);
  const [error, setError] = useState<string | null>(null);

  const cacheConversation = useCallback(
    (response: BackendBookingConversation) => {
      const mapped = mapBackendConversationToConversation(
        response,
        bookings.find((booking) => booking.id === response.booking_id),
        user?.id,
      );
      upsertLiveConversation(mapped);
    },
    [bookings, upsertLiveConversation, user?.id],
  );

  const refreshConversation = useCallback(
    async (showLoading = false) => {
      if (!token || !conversationId || user?.role !== 'admin') {
        return;
      }

      if (showLoading) {
        setIsLoading(true);
      }
      setError(null);
      try {
        let response = await backendApi.adminFetchConversation(
          token,
          conversationId,
        );
        if (hasUnreadPlayerMessages(response)) {
          response = await backendApi.adminMarkConversationRead(
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
      if (!token || !conversationId || user?.role !== 'admin') {
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

  if (!user || user.role !== 'admin') {
    return null;
  }

  const sendAdminReply = async () => {
    const body = draft.trim();
    if (!body || !token || !conversationId || !conversation) {
      return;
    }
    if (conversation.mode === 'resolved' || conversation.mode === 'closed') {
      setError('This conversation is no longer open for replies.');
      return;
    }

    setActiveAction('send');
    setError(null);
    try {
      const response = await backendApi.adminSendConversationMessage(
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
          : 'Failed to send admin reply.',
      );
    } finally {
      setActiveAction(null);
    }
  };

  const updateConversationState = async (action: 'resolve' | 'close') => {
    if (!token || !conversationId) {
      return;
    }

    setActiveAction(action);
    setError(null);
    try {
      const response =
        action === 'resolve'
          ? await backendApi.adminResolveConversation(token, conversationId)
          : await backendApi.adminCloseConversation(token, conversationId);
      cacheConversation(response);
    } catch (actionError) {
      setError(
        actionError instanceof BackendApiError
          ? actionError.message
          : `Failed to ${action} the conversation.`,
      );
    } finally {
      setActiveAction(null);
    }
  };

  if (!conversation) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="secondary"
        title="Conversation unavailable"
        subtitle="Return to the chat queue or retry this exact conversation link."
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
                  ? 'This conversation does not exist or is no longer available.'
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
              label="Back to chat queue"
              onPress={() => router.replace('/admin/chat')}
            />
          </View>
        </AppCard>
      </AppScreen>
    );
  }

  const booking = bookings.find((item) => item.id === conversation.bookingId);
  const stringItem = strings.find(
    (item) => item.id === (conversation.stringId ?? booking?.stringId),
  );
  const orderCode = booking
    ? booking.orderCode ?? formatBookingOrderCode(booking.id)
    : 'General support';
  const isClosed =
    conversation.mode === 'resolved' || conversation.mode === 'closed';

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title="Admin chat detail"
      subtitle={
        booking
          ? 'Reply as the shop, review booking context, and finish the persisted support thread.'
          : 'Reply as the shop and finish the persisted general support thread.'
      }
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection eyebrow="Customer" title={booking?.customerName ?? 'Player'}>
        <AppCard variant="highlighted" padding="md">
          <View className="flex-row flex-wrap gap-2">
            <AppChip label={conversation.statusLabel} variant="primary" />
            <AppChip label={orderCode} variant="secondary" />
          </View>
          <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
            {stringItem ? `${stringItem.brand} ${stringItem.model}` : 'String not linked'} •{' '}
            {booking
              ? `${booking.dropOffDate} at ${booking.dropOffTime}`
              : 'General support thread'}
          </HeroText>
        </AppCard>
      </AppSection>

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
            label="Refresh conversation"
            variant="outline"
            className="mt-4"
            onPress={() => void refreshConversation()}
          />
        </AppCard>
      ) : null}

      <AppSection eyebrow="Messages" title={conversation.title}>
        <View className="gap-4">
          {conversation.messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))}
          {conversation.messages.length === 0 ? (
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-600">
                No messages have been sent in this support thread yet.
              </HeroText>
            </AppCard>
          ) : null}
        </View>
      </AppSection>

      {!token ? (
        <AppCard variant="subtle" className="mb-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Your admin session expired. Sign in again to manage this support thread.
          </HeroText>
        </AppCard>
      ) : (
        <>
          {!isClosed ? (
            <AppSection eyebrow="Reply" title="Send admin response">
              <AppInput
                accessibilityLabel="Admin reply"
                value={draft}
                onChangeText={setDraft}
                multiline
                inputClassName="min-h-24"
              />
              <AppButton
                className="mt-3"
                label="Send admin reply"
                isLoading={activeAction === 'send'}
                isDisabled={!draft.trim() || activeAction !== null}
                onPress={() => void sendAdminReply()}
              />
            </AppSection>
          ) : null}

          <AppSection
            eyebrow="Thread status"
            title="Resolve or close support"
            className="mb-8"
          >
            <View className="gap-3">
              {conversation.mode !== 'resolved' &&
              conversation.mode !== 'closed' ? (
                <AppButton
                  label="Resolve conversation"
                  variant="outline"
                  isLoading={activeAction === 'resolve'}
                  isDisabled={activeAction !== null}
                  onPress={() => void updateConversationState('resolve')}
                />
              ) : null}
              {conversation.mode !== 'closed' ? (
                <AppButton
                  label="Close conversation"
                  variant="danger"
                  isLoading={activeAction === 'close'}
                  isDisabled={activeAction !== null}
                  onPress={() => void updateConversationState('close')}
                />
              ) : (
                <AppCard variant="subtle" padding="md">
                  <HeroText className="text-sm leading-6 text-neutral-600">
                    This conversation is closed.
                  </HeroText>
                </AppCard>
              )}
            </View>
          </AppSection>
        </>
      )}
    </AppScreen>
  );
}
