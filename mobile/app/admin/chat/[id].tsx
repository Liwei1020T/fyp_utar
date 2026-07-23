import React, { useState } from 'react';
import { View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { ChatBubble } from '../../../components/chat/ChatBubble';
import { formatBookingOrderCode } from '../../../lib/formatters';
import { getBookingById, getPlayerById, getStringById } from '../../../services/mockAppService';
import { useAppStore, useConversations } from '../../../store/appStore';

export default function AdminChatDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const conversations = useConversations();
  const appendChatMessage = useAppStore((state) => state.appendChatMessage);
  const resolveConversation = useAppStore((state) => state.resolveConversation);
  const conversation = conversations.find((item) => item.id === params.id);
  const [draft, setDraft] = useState(
    'We can keep your requested timing. Please drop off before 6 PM.'
  );

  if (!conversation) {
    return null;
  }

  const player = getPlayerById(conversation.playerId);
  const booking = getBookingById(conversation.bookingId);
  const stringItem = getStringById(conversation.stringId ?? booking?.stringId);
  const orderCode = booking
    ? booking.orderCode ?? formatBookingOrderCode(booking.id)
    : null;

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title="Admin chat detail"
      subtitle="Reply as the shop, review linked booking context, and close the conversation when it is resolved."
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppSection eyebrow="Customer" title={player?.name ?? 'Player'}>
        <AppCard variant="highlighted" padding="md">
          <View className="flex-row flex-wrap gap-2">
            <AppChip label={conversation.statusLabel} variant="primary" />
            {orderCode ? <AppChip label={orderCode} variant="secondary" /> : null}
          </View>
          <HeroText className="mt-3 text-sm leading-6 text-neutral-600">
            {stringItem ? `${stringItem.brand} ${stringItem.model}` : 'String not linked'} •{' '}
            {booking ? `${booking.dropOffDate} at ${booking.dropOffTime}` : 'General support thread'}
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Messages" title={conversation.title}>
        <View className="gap-4">
          {conversation.messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Reply" title="Send admin response" className="mb-8">
        <AppInput value={draft} onChangeText={setDraft} multiline inputClassName="min-h-24" />
        <View className="mt-3 gap-3">
          <AppButton
            label="Send admin reply"
            onPress={() =>
              appendChatMessage(conversation.id, {
                role: 'admin',
                senderName: 'Daniel Tan',
                body: draft,
              })
            }
          />
          <AppButton
            label="Resolve conversation"
            variant="outline"
            onPress={() => resolveConversation(conversation.id)}
          />
        </View>
      </AppSection>
    </AppScreen>
  );
}
