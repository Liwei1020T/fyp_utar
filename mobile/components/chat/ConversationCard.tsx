import React from 'react';
import { Pressable, View } from 'react-native';
import { ChevronRight, MessageSquareText } from 'lucide-react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import { formatConversationMode, formatDateTime } from '../../lib/formatters';
import type { ChatConversation } from '../../types/domain';

interface ConversationCardProps {
  conversation: ChatConversation;
  onPress: () => void;
}

export function ConversationCard({ conversation, onPress }: ConversationCardProps) {
  const statusVariant =
    conversation.mode === 'admin_joined'
      ? 'success'
      : conversation.mode === 'waiting_admin'
        ? 'warning'
        : conversation.mode === 'resolved'
          ? 'info'
          : conversation.mode === 'closed'
            ? 'neutral'
            : 'primary';

  return (
    <Pressable onPress={onPress}>
      <AppCard variant="elevated" padding="md">
        <View className="flex-row items-start gap-4">
          <View className="h-12 w-12 items-center justify-center rounded-[18px] bg-primary-50">
            <MessageSquareText size={20} color="#2F64B6" />
          </View>
          <View className="flex-1">
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1">
                <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                  {conversation.title}
                </HeroText>
                <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                  {conversation.summary}
                </HeroText>
              </View>
              <ChevronRight size={18} color="#94A3B8" />
            </View>
            <View className="mt-4 flex-row flex-wrap gap-2">
              <AppChip label={conversation.statusLabel} variant={statusVariant} />
            </View>
            <HeroText className="mt-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
              Updated {formatDateTime(conversation.updatedAt)}
            </HeroText>
          </View>
        </View>
      </AppCard>
    </Pressable>
  );
}
