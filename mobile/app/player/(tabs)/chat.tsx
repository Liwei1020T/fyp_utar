import React from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Bot, Sparkles } from 'lucide-react-native';
import { AppCard } from '../../../components/ui/AppCard';
import { AppButton } from '../../../components/ui/AppButton';
import { AppScreen, useBottomContentInset } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { HeroText } from '../../../components/ui/heroui';
import { ConversationCard } from '../../../components/chat/ConversationCard';
import { useConversations, useCurrentUser } from '../../../store/appStore';

export default function PlayerChatThreadsScreen() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(18);
  const user = useCurrentUser();
  const conversations = useConversations();

  if (!user || user.role !== 'player') {
    return null;
  }

  const playerConversations = conversations.filter((item) => item.playerId === user.id);

  return (
    <AppScreen title="Chat and support" subtitle="Start with AI, then request admin support when you need the shop to step in." scrollable={false}>
      <FlatList
        className="flex-1"
        data={playerConversations}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: bottomContentInset, paddingTop: 2 }}
        ListHeaderComponent={
          <View className="gap-6 pb-6">
            <AppCard variant="dark" padding="lg">
              <View className="flex-row items-start justify-between gap-4">
                <View className="flex-1">
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
                    AI-first support
                  </HeroText>
                  <HeroText className="mt-2 text-[26px] font-bold tracking-tight text-white">
                    Ask setup questions, then escalate only when you need a human.
                  </HeroText>
                  <HeroText className="mt-2 text-sm leading-6 text-primary-100">
                    The prototype now flows from AI guidance into admin handoff, booking support, and after-sales follow-up in one clean chat experience.
                  </HeroText>
                </View>
                <View className="h-12 w-12 items-center justify-center rounded-2xl bg-white/12">
                  <Bot size={22} color="white" />
                </View>
              </View>
              <AppButton
                label="Open latest thread"
                variant="secondary"
                size="sm"
                className="mt-6 self-start"
                onPress={() => router.push(`/player/chat/${playerConversations[0]?.id ?? 'chat-001'}`)}
              />
            </AppCard>

            <AppSection eyebrow="Quick start" title="Prompt ideas" variant="compact" className="mt-0">
              <View className="flex-row flex-wrap gap-2">
                {['Explain my recommendation', 'Ask admin about pickup', 'Need help with payment'].map((item) => (
                  <Pressable key={item} onPress={() => router.push(`/player/chat/${playerConversations[0]?.id ?? 'chat-001'}`)}>
                    <AppCard variant="subtle" padding="sm">
                      <View className="flex-row items-center gap-2">
                        <Sparkles size={14} color="#2F64B6" />
                        <HeroText className="text-sm font-medium text-neutral-700">{item}</HeroText>
                      </View>
                    </AppCard>
                  </Pressable>
                ))}
              </View>
            </AppSection>
          </View>
        }
        renderItem={({ item }) => (
          <View className="mb-4">
            <ConversationCard conversation={item} onPress={() => router.push(`/player/chat/${item.id}`)} />
          </View>
        )}
      />
    </AppScreen>
  );
}
