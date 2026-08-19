import React, { useState } from 'react';
import { Alert, Platform, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Bot, SendHorizontal, ShieldCheck, UserRound } from 'lucide-react-native';
import { AgentAnswerCard } from '../../components/agent/AgentAnswerCard';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { backendApi, BackendApiError } from '../../services/backendApi';
import {
  mapBackendBookingToBooking,
  mapBackendConversationToConversation,
  mapBackendInventoryStringToStringItem,
} from '../../services/backendMappers';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
  useCurrentUser,
} from '../../store/appStore';
import type {
  BackendAgentAction,
  BackendAgentMessage,
  BackendAgentResponse,
} from '../../types/backend';

const starterQuestions = [
  "Summarize today's operations.",
  // Deferred FYP scope; uncomment with the matching admin tool.
  // 'Show low-stock strings.',
  // 'Which bookings need attention?',
  // 'Show support conversations waiting for admin.',
  // 'Show pending payments.',
] as const;

type ConversationEntry =
  | { id: string; role: 'user'; content: string }
  | { id: string; role: 'assistant'; response: BackendAgentResponse };

const writeActions = new Set<BackendAgentAction['action']>([
  // Deferred FYP scope; uncomment with ACTIVE_AGENT_ACTIONS and admin tools.
  // 'update_booking_status',
  // 'update_inventory_stock',
  // 'send_admin_message',
]);

export default function AdminAgentScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const upsertLiveBooking = useAppStore((state) => state.upsertLiveBooking);
  const upsertLiveConversation = useAppStore(
    (state) => state.upsertLiveConversation,
  );
  const updateStringItem = useAppStore((state) => state.updateStringItem);
  const [entries, setEntries] = useState<ConversationEntry[]>([]);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isActing, setIsActing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  if (!user || user.role !== 'admin') {
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
    setNotice(null);
    setIsSending(true);
    try {
      const response = await backendApi.queryAgent(token, {
        message: question,
        context: { surface: 'admin_assistant' },
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
          : 'The admin assistant is temporarily unavailable.',
      );
    } finally {
      setIsSending(false);
    }
  };

  const executeAction = async (action: BackendAgentAction) => {
    if (!token || isActing) {
      return;
    }
    setError(null);
    setNotice(null);
    setIsActing(true);
    try {
      if (action.action === 'update_booking_status') {
        const bookingId = action.parameters.booking_id;
        const status = action.parameters.status;
        if (!bookingId || !status) throw new Error('Invalid booking action');
        const updated = await backendApi.adminUpdateBookingStatus(token, bookingId, {
          status,
          note: action.parameters.note?.trim() || undefined,
        });
        upsertLiveBooking(mapBackendBookingToBooking(updated, user.id));
      } else if (action.action === 'update_inventory_stock') {
        const catalogId = action.parameters.catalog_id;
        const currentStock = Number(action.parameters.current_stock);
        if (!catalogId || !Number.isInteger(currentStock) || currentStock < 0) {
          throw new Error('Invalid inventory action');
        }
        const updated = await backendApi.adminUpdateInventoryString(token, catalogId, {
          current_stock: currentStock,
          admin_note: action.parameters.note?.trim() || 'Confirmed through Admin AI',
          movement_type: 'admin_agent_confirmed',
          reference_type: 'admin_agent',
        });
        const mapped = mapBackendInventoryStringToStringItem(updated);
        updateStringItem(mapped.id, mapped);
      } else if (action.action === 'send_admin_message') {
        const conversationId = action.parameters.conversation_id;
        const body = action.parameters.body?.trim();
        if (!conversationId || !body) throw new Error('Invalid message action');
        const updated = await backendApi.adminSendConversationMessage(
          token,
          conversationId,
          { body },
        );
        upsertLiveConversation(
          mapBackendConversationToConversation(
            updated,
            bookings.find((booking) => booking.id === updated.booking_id),
            user.id,
          ),
        );
      }
      setNotice(`Completed: ${action.label.replace(/\*\*/g, '')}`);
    } catch (actionError) {
      setError(
        actionError instanceof BackendApiError
          ? actionError.message
          : 'The confirmed action could not be completed.',
      );
    } finally {
      setIsActing(false);
    }
  };

  const confirmAction = (action: BackendAgentAction) => {
    const message = `${action.label.replace(/\*\*/g, '')}\n\nThis will update live store data.`;
    if (Platform.OS === 'web' && typeof globalThis.confirm === 'function') {
      if (globalThis.confirm(message)) void executeAction(action);
      return;
    }
    Alert.alert('Confirm admin action', message, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Confirm', onPress: () => void executeAction(action) },
    ]);
  };

  const handleAction = (action: BackendAgentAction) => {
    if (action.action === 'open_admin_booking' && action.parameters.booking_id) {
      router.push(`/admin/bookings/${action.parameters.booking_id}`);
      return;
    }
    if (action.action === 'open_admin_inventory' && action.parameters.catalog_id) {
      router.push(`/admin/inventory/${action.parameters.catalog_id}`);
      return;
    }
    if (
      action.action === 'open_admin_conversation' &&
      action.parameters.conversation_id
    ) {
      router.push(`/admin/chat/${action.parameters.conversation_id}`);
      return;
    }
    if (action.action === 'open_admin_payments') {
      router.push('/admin/payments');
      return;
    }
    if (writeActions.has(action.action)) {
      confirmAction(action);
    }
  };

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      title="Admin AI"
      subtitle="Read-only daily operations summary."
      showBackButton
      onBackPress={() => router.back()}
      footer={
        <View className="gap-2 border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          <AppInput
            className="mb-0"
            placeholder="Ask for today's operations summary..."
            accessibilityLabel="Question for Admin AI"
            value={draft}
            onChangeText={setDraft}
            multiline
            inputClassName="min-h-20"
            isDisabled={isSending || isActing || !token}
          />
          <AppButton
            label="Send"
            isLoading={isSending}
            isDisabled={!draft.trim() || !token || isActing}
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
              Review today&apos;s operations.
            </HeroText>
            <HeroText className="mt-2 text-sm leading-6 text-primary-100">
              Admin AI summarizes current workload without changing store data.
            </HeroText>
          </View>
          <ShieldCheck size={21} color="#DCE8FF" />
        </View>
      </AppCard>

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
                    Admin
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
              onAction={handleAction}
            />
          ),
        )}

        {isSending ? (
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm text-neutral-600">
              Retrieving current admin records...
            </HeroText>
          </AppCard>
        ) : null}
        {notice ? (
          <AppCard variant="subtle" padding="md" className="border border-green-200">
            <HeroText className="text-sm leading-6 text-green-700">{notice}</HeroText>
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
