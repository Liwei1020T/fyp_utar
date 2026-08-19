import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import {
  BadgeCheck,
  Bell,
  CalendarPlus,
  ChevronRight,
  List,
  MessageSquareText,
  NotebookText,
  Settings2,
  Sparkles,
  Wallet,
  Zap,
} from 'lucide-react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppCard } from '../../components/ui/AppCard';
import { HeroText } from '../../components/ui/heroui';
import { appChromeColors } from '../../components/ui/theme';

const toolGroups = [
  {
    title: 'Play',
    items: [
      {
        title: 'Advisor',
        subtitle: 'Get a string and tension recommendation.',
        icon: Zap,
        route: '/player/recommend',
      },
      {
        title: 'String catalog',
        subtitle: 'Browse, filter, and compare available strings.',
        icon: List,
        route: '/player/strings',
      },
      {
        title: 'Book service',
        subtitle: 'Start a new racket restring booking.',
        icon: CalendarPlus,
        route: '/player/bookings/new',
      },
      {
        title: 'My bookings',
        subtitle: 'Check current orders and service history.',
        icon: NotebookText,
        route: '/player/bookings',
      },
    ],
  },
  {
    title: 'Service',
    items: [
      {
        title: 'AI assistant',
        subtitle: 'Ask grounded questions about strings and recommendations.',
        icon: Sparkles,
        route: '/player/chatbot',
      },
      {
        title: 'Message shop',
        subtitle: 'Contact the shop with or without a booking.',
        icon: MessageSquareText,
        route: '/player/chat',
      },
      {
        title: 'Notifications',
        subtitle: 'Review booking, payment, and service updates.',
        icon: Bell,
        route: '/player/notifications',
      },
      {
        title: 'Racket passport',
        subtitle: 'Review your rackets and stringing history.',
        icon: BadgeCheck,
        route: '/player/rackets',
      },
    ],
  },
  {
    title: 'Account',
    items: [
      {
        title: 'Wallet',
        subtitle: 'View your verified balance and transactions.',
        icon: Wallet,
        route: '/player/wallet',
      },
      {
        title: 'App settings',
        subtitle: 'Manage security, privacy, and notifications.',
        icon: Settings2,
        route: '/player/settings',
      },
    ],
  },
] as const;

export default function PlayerToolsScreen() {
  const router = useRouter();

  return (
    <AppScreen
      headerVariant="flow"
      title="All tools"
      showBackButton
      onBackPress={() => router.back()}
      backAccessibilityLabel="Back to player home"
    >
      {toolGroups.map((group, groupIndex) => (
        <AppSection
          key={group.title}
          title={group.title}
          variant="compact"
          className={groupIndex === 0 ? 'mt-1' : undefined}
        >
          <AppCard variant="default" padding="none" className="rounded-[18px]">
            {group.items.map((item, itemIndex) => {
              const Icon = item.icon;

              return (
                <Pressable
                  key={item.title}
                  accessibilityRole="button"
                  accessibilityLabel={`${item.title}. ${item.subtitle}`}
                  accessibilityHint={`Open ${item.title.toLowerCase()}`}
                  className={[
                    'min-h-[68px] flex-row items-center gap-3 px-3.5 py-3',
                    itemIndex > 0 ? 'border-t border-[#E7ECF2]' : '',
                  ].join(' ')}
                  style={({ pressed }) => ({
                    opacity: pressed ? 0.72 : 1,
                    transform: [{ scale: pressed ? 0.99 : 1 }],
                  })}
                  onPress={() => router.push(item.route as never)}
                >
                  <View className="h-10 w-10 shrink-0 items-center justify-center rounded-[14px] bg-primary-50">
                    <Icon size={18} color={appChromeColors.primary} strokeWidth={2} />
                  </View>
                  <View className="min-w-0 flex-1">
                    <HeroText className="text-[14px] font-semibold leading-[18px] text-slate-900">
                      {item.title}
                    </HeroText>
                    <HeroText
                      className="mt-0.5 text-[13px] leading-[17px] text-slate-500"
                      numberOfLines={2}
                    >
                      {item.subtitle}
                    </HeroText>
                  </View>
                  <ChevronRight size={16} color="#94A3B8" strokeWidth={2} />
                </Pressable>
              );
            })}
          </AppCard>
        </AppSection>
      ))}
    </AppScreen>
  );
}
