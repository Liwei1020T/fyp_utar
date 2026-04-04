import React, { useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft, SendHorizontal } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { ChatBubble } from '../../../components/chat/ChatBubble';
import { formatConversationMode } from '../../../lib/formatters';
import { useAppStore, useConversations } from '../../../store/appStore';

export default function PlayerChatDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const conversations = useConversations();
  const appendChatMessage = useAppStore((state) => state.appendChatMessage);
  const requestVendorSupport = useAppStore((state) => state.requestVendorSupport);
  const resolveConversation = useAppStore((state) => state.resolveConversation);
  const [draft, setDraft] = useState('');
  const conversation = useMemo(
    () => conversations.find((item) => item.id === params.id) ?? conversations[0],
    [conversations, params.id]
  );

  if (!conversation) {
    return null;
  }

  const sendMessage = (message: string) => {
    if (!message.trim()) {
      return;
    }

    appendChatMessage(conversation.id, {
      role: 'user',
      senderName: 'You',
      body: message,
    });

    const responder =
      conversation.mode === 'vendor_joined'
        ? {
            role: 'vendor' as const,
            senderName: 'Daniel Tan',
            body: 'Admin note received. We can adjust timing, service notes, or drop-off details directly from the shop desk.',
          }
        : conversation.mode === 'waiting_vendor'
          ? {
              role: 'system' as const,
              senderName: 'System',
              body: 'Admin support request is queued. The next reply will come from the shop once the admin joins.',
            }
          : {
              role: 'ai' as const,
              senderName: 'StringSense AI',
              body: 'Based on your profile, I would keep the current shortlist and use a slightly safer tension if comfort matters today.',
            };

    appendChatMessage(conversation.id, responder);
    setDraft('');
  };

  return (
    <AppScreen
      title={conversation.title}
      subtitle="Conversation modes show whether AI or the vendor is currently leading the thread."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
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

      <AppSection eyebrow="Quick prompts" title="Suggested next messages" variant="compact">
        <View className="flex-row flex-wrap gap-2">
          {conversation.quickPrompts.map((item) => (
            <AppChip
              key={item}
              label={item}
              size="md"
              variant="neutral"
              onPress={() => sendMessage(item)}
            />
          ))}
        </View>
      </AppSection>

      {conversation.mode !== 'vendor_joined' && conversation.mode !== 'resolved' ? (
        <AppSection eyebrow="Handoff" title="Need the shop to take over?" variant="compact">
          <View className="gap-3">
            <AppCard variant="subtle" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-600">
                AI replies first by default. Tap below when the thread needs a real vendor response for booking, timing, or after-sales support.
              </HeroText>
            </AppCard>
            <AppButton
              label={
                conversation.mode === 'waiting_vendor'
                  ? 'Admin request sent'
                  : 'Request Admin Support'
              }
              variant={conversation.mode === 'waiting_vendor' ? 'outline' : 'secondary'}
              size="lg"
              onPress={() => requestVendorSupport(conversation.id)}
            />
          </View>
        </AppSection>
      ) : null}

      <AppSection eyebrow="Messages" title="Thread activity">
        <View className="gap-4">
          {conversation.messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Composer" title="Reply in this thread" className="mb-8">
        <AppInput
          className="mb-2"
          placeholder="Type a message to AI or the vendor..."
          value={draft}
          onChangeText={setDraft}
          multiline
          inputClassName="min-h-24"
        />
        <View className="gap-3">
          <AppButton
            label="Send message"
            size="lg"
            leadingIcon={<SendHorizontal size={18} color="white" />}
            onPress={() => sendMessage(draft)}
          />
          {conversation.mode !== 'resolved' ? (
            <AppButton
              label="Mark resolved"
              variant="outline"
              size="lg"
              onPress={() => resolveConversation(conversation.id)}
            />
          ) : null}
        </View>
      </AppSection>
    </AppScreen>
  );
}
