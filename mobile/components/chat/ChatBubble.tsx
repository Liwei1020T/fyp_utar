import React from 'react';
import { View } from 'react-native';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import { formatDateTime, formatMessageRole } from '../../lib/formatters';
import type { ChatMessage } from '../../types/domain';

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <View className={isUser ? 'items-end' : 'items-start'}>
      <View
        className={[
          'max-w-[90%] rounded-[26px] px-4 py-3',
          isSystem
            ? 'bg-neutral-100'
            : isUser
              ? 'bg-primary-600'
              : message.role === 'ai'
                ? 'bg-primary-50'
                : 'bg-[#E4F2F0]',
        ].join(' ')}
      >
        <View className="mb-2 flex-row items-center gap-2">
          <AppChip
            label={formatMessageRole(message.role)}
            variant={
              message.role === 'user'
                ? 'secondary'
                : message.role === 'admin'
                  ? 'success'
                  : message.role === 'system'
                    ? 'neutral'
                    : 'primary'
            }
          />
          <HeroText className={`text-[11px] ${isUser ? 'text-white/75' : 'text-neutral-400'}`}>
            {message.senderName}
          </HeroText>
        </View>
        <HeroText className={`text-sm leading-6 ${isUser ? 'text-white' : 'text-neutral-800'}`}>
          {message.body}
        </HeroText>
      </View>
      <HeroText className="mt-2 text-[11px] font-medium text-neutral-400">
        {formatDateTime(message.sentAt)}
      </HeroText>
    </View>
  );
}
