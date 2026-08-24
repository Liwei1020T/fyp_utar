import React from 'react';
import { Pressable, View } from 'react-native';
import { ChevronRight, MessageSquareText } from 'lucide-react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import { formatDateTime } from '../../lib/formatters';
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
  const updatedLabel = formatDateTime(conversation.updatedAt);
  const summaryLabel = conversation.summary.replace(/[.!?]+$/, '');

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${conversation.title}. ${summaryLabel}. ${conversation.statusLabel}. Updated ${updatedLabel}`}
      accessibilityHint="Open this conversation"
    >
      <AppCard variant="elevated" padding="sm">
        <View className="flex-row items-start gap-3">
          <View className="h-10 w-10 items-center justify-center rounded-[10px] bg-primary-50">
            <MessageSquareText size={20} color="#2F64B6" />
          </View>
          <View className="flex-1">
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1">
                <HeroText className="text-[15px] font-bold leading-5 tracking-tight text-neutral-950">
                  {conversation.title}
                </HeroText>
                <HeroText className="mt-0.5 text-[13px] leading-[18px] text-neutral-500" numberOfLines={3}>
                  {conversation.summary}
                </HeroText>
              </View>
              <ChevronRight size={18} color="#94A3B8" />
            </View>
            <View className="mt-2 flex-row flex-wrap gap-2">
              <AppChip label={conversation.statusLabel} variant={statusVariant} />
            </View>
            <HeroText className="mt-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-neutral-400">
              Updated {updatedLabel}
            </HeroText>
          </View>
        </View>
      </AppCard>
    </Pressable>
  );
}
