import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Bot, SendHorizontal, UserRound } from 'lucide-react-native';
import { AgentAnswerCard } from '../../components/agent/AgentAnswerCard';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { backendApi, BackendApiError } from '../../services/backendApi';
import {
  useBackendAccessToken,
  useCurrentUser,
} from '../../store/appStore';
import type {
  BackendAgentAction,
  BackendAgentMessage,
  BackendAgentResponse,
} from '../../types/backend';

const starterQuestions = [
  'Help me choose a string step by step.',
  'What are the store opening hours?',
  'Compare Yonex BG80 and Yonex BG65.',
  // Deferred FYP scope; uncomment with the matching backend tools.
  // 'Which string best suits my saved profile?',
  // 'Explain my latest recommendation.',
] as const;

type ConversationEntry =
  | { id: string; role: 'user'; content: string }
  | { id: string; role: 'assistant'; response: BackendAgentResponse };

export default function PlayerAgentScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const [entries, setEntries] = useState<ConversationEntry[]>([]);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user || user.role !== 'player') {
    return null;
  }

  const sendQuestion = async (rawQuestion: string) => {
    const question = rawQuestion.trim();
    if (!question || !token || isSending) {
      return;
    }

    const history: BackendAgentMessage[] = entries
      .map((entry): BackendAgentMessage =>
        entry.role === 'user'
          ? { role: 'user', content: entry.content }
          : { role: 'assistant', content: entry.response.answer },
      )
      .slice(-12);
    const requestId = `${Date.now()}-${entries.length}`;
    setEntries((current) => [
      ...current,
      { id: `${requestId}-user`, role: 'user', content: question },
    ]);
    setDraft('');
    setError(null);
    setIsSending(true);
    try {
      const response = await backendApi.queryAgent(token, {
        message: question,
        context: { surface: 'chatbot' },
        conversation_history: history,
      });
      setEntries((current) => [
        ...current,
        { id: `${requestId}-assistant`, role: 'assistant', response },
      ]);
    } catch (sendError) {
      setError(
        sendError instanceof BackendApiError
          ? sendError.message
          : 'The assistant is temporarily unavailable.',
      );
    } finally {
      setIsSending(false);
    }
  };

  const handleAction = (action: BackendAgentAction) => {
    if (action.action === 'open_string' && action.parameters.catalog_id) {
      router.push(`/player/strings/${action.parameters.catalog_id}`);
      return;
    }

    /* Deferred FYP scope; re-enable with ACTIVE_AGENT_ACTIONS.
    if (action.action === 'open_booking' && action.parameters.booking_id) {
      router.push(`/player/bookings/${action.parameters.booking_id}`);
      return;
    }
    if (
      action.action === 'open_recommendation' &&
      action.parameters.catalog_id &&
      action.parameters.run_id
    ) {
      router.push(
        `/player/recommend/explain/${action.parameters.catalog_id}?runId=${action.parameters.run_id}`,
      );
      return;
    }
    if (action.action !== 'request_human_handoff') {
      return;
    }
    const bookingId = action.parameters.booking_id;
    if (!bookingId || !token) {
      router.push('/player/chat');
      return;
    }
    setError(null);
    try {
      const conversation = await backendApi.requestBookingSupport(token, bookingId);
      router.push(`/player/chat/${conversation.id}`);
    } catch (handoffError) {
      setError(
        handoffError instanceof BackendApiError
          ? handoffError.message
          : 'Unable to request human support.',
      );
    }
    */
  };

  return (
    <AppScreen
      headerVariant="secondary"
      title="StringSense AI"
      subtitle="Guided selection, string comparisons, and live stock."
      showBackButton
      onBackPress={() => router.back()}
      footer={
        <View className="gap-2 border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          <AppInput
            className="mb-0"
            placeholder="Answer the current selection question..."
            accessibilityLabel="Question for StringSense AI"
            value={draft}
            onChangeText={setDraft}
            multiline
            inputClassName="min-h-20"
            isDisabled={isSending || !token}
          />
          <AppButton
            label="Send"
            isLoading={isSending}
            isDisabled={!draft.trim() || !token}
            leadingIcon={<SendHorizontal size={17} color="white" />}
            onPress={() => void sendQuestion(draft)}
          />
        </View>
      }
    >
      <AppCard variant="dark" padding="lg" className="rounded-[28px]">
        <View className="flex-row items-start gap-3">
          <View className="h-11 w-11 items-center justify-center rounded-full bg-white/12">
            <Bot size={22} color="white" />
          </View>
          <View className="flex-1">
            <HeroText className="text-xl font-black text-white">
              Choose with evidence.
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-primary-100">
              Answer four short questions for recommendations, or compare two approved strings.
            </HeroText>
          </View>
        </View>
      </AppCard>

      <View className="mt-4">
        <AppButton
          label="Contact human support"
          variant="outline"
          onPress={() => router.push('/player/chat')}
        />
      </View>

      {entries.length === 0 ? (
        <View className="mt-5 flex-row flex-wrap gap-2">
          {starterQuestions.map((question) => (
            <AppChip
              key={question}
              label={question}
              size="md"
              variant="primary"
              onPress={() => void sendQuestion(question)}
            />
          ))}
        </View>
      ) : null}

      <View className="mt-5 gap-4 pb-8">
        {entries.map((entry) =>
          entry.role === 'user' ? (
            <View key={entry.id} className="items-end">
              <View className="max-w-[90%] rounded-[24px] bg-primary-600 px-4 py-3">
                <View className="mb-2 flex-row items-center gap-2">
                  <UserRound size={15} color="white" />
                  <HeroText className="text-[11px] font-bold uppercase tracking-wider text-white/75">
                    You
                  </HeroText>
                </View>
                <HeroText className="text-sm leading-6 text-white">
                  {entry.content}
                </HeroText>
              </View>
            </View>
          ) : (
            <AgentAnswerCard
              key={entry.id}
              response={entry.response}
              onQuestion={(question) => void sendQuestion(question)}
              onAction={(action) => void handleAction(action)}
            />
          ),
        )}

        {isSending ? (
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm text-neutral-600">
              Retrieving verified StringSense evidence...
            </HeroText>
          </AppCard>
        ) : null}

        {error ? (
          <AppCard variant="subtle" padding="md" className="border border-red-100">
            <HeroText className="text-sm leading-6 text-red-700">{error}</HeroText>
          </AppCard>
        ) : null}
      </View>
    </AppScreen>
  );
}
