import React, { useEffect, useRef } from 'react';
import { useRouter } from 'expo-router';
import {
  Animated,
  Easing,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  BadgeCheck,
  Bell,
  CalendarPlus,
  List,
  MessageSquareText,
  NotebookText,
  Sparkles,
  Wallet,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react-native';
import { HeroText } from '../ui/heroui';
import { appChromeColors } from '../ui/theme';

type PlayerTool = {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  route: string;
};

type PlayerToolGroup = {
  title: string;
  items: readonly PlayerTool[];
};

export const playerToolGroups: readonly PlayerToolGroup[] = [
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
    ],
  },
] as const;

interface PlayerToolsSheetProps {
  visible: boolean;
  onClose: () => void;
}

export function PlayerToolsSheet({ visible, onClose }: PlayerToolsSheetProps) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const sheetOffset = useRef(new Animated.Value(420)).current;

  useEffect(() => {
    if (!visible) {
      return;
    }

    sheetOffset.setValue(420);
    const animation = Animated.timing(sheetOffset, {
      toValue: 0,
      duration: 220,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    });
    animation.start();

    return () => animation.stop();
  }, [sheetOffset, visible]);

  const openTool = (route: string) => {
    onClose();
    router.push(route as never);
  };

  return (
    <Modal
      transparent
      visible={visible}
      animationType="none"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <View style={styles.backdrop}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Close more menu"
          onPress={onClose}
          style={StyleSheet.absoluteFillObject}
        />
        <Animated.View
          style={[
            styles.sheet,
            { paddingBottom: Math.max(insets.bottom, 16), transform: [{ translateY: sheetOffset }] },
          ]}
        >
          <View style={styles.handle} accessible={false} />
          <View style={styles.header}>
            <View>
              <HeroText style={styles.title}>More</HeroText>
              <HeroText style={styles.subtitle}>All player features</HeroText>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Close more menu"
              hitSlop={8}
              onPress={onClose}
              style={({ pressed }) => [styles.closeButton, pressed && styles.pressed]}
            >
              <X size={19} color={appChromeColors.textSecondary} strokeWidth={2.2} />
            </Pressable>
          </View>

          <ScrollView
            contentInsetAdjustmentBehavior="automatic"
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.content}
          >
            {playerToolGroups.map((group) => (
              <View key={group.title} style={styles.group}>
                <HeroText style={styles.groupTitle}>{group.title}</HeroText>
                <View style={styles.toolGrid}>
                  {group.items.map((item) => {
                    const Icon = item.icon;

                    return (
                      <Pressable
                        key={item.title}
                        accessibilityRole="button"
                        accessibilityLabel={item.title}
                        accessibilityHint={`Open ${item.title.toLowerCase()}`}
                        onPress={() => openTool(item.route)}
                        style={({ pressed }) => [styles.toolItem, pressed && styles.pressed]}
                      >
                        <View style={styles.toolIcon}>
                          <Icon size={18} color={appChromeColors.primary} strokeWidth={2} />
                        </View>
                        <HeroText style={styles.toolTitle}>{item.title}</HeroText>
                      </Pressable>
                    );
                  })}
                </View>
              </View>
            ))}
          </ScrollView>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(9, 29, 62, 0.38)',
  },
  sheet: {
    width: '100%',
    maxHeight: '78%',
    paddingHorizontal: 16,
    paddingTop: 10,
    backgroundColor: appChromeColors.surface,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    borderTopWidth: 1,
    borderColor: appChromeColors.borderSoft,
  },
  handle: {
    width: 38,
    height: 4,
    alignSelf: 'center',
    borderRadius: 4,
    backgroundColor: appChromeColors.border,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
  },
  title: {
    color: appChromeColors.textPrimary,
    fontSize: 22,
    fontWeight: '700',
    lineHeight: 27,
  },
  subtitle: {
    marginTop: 2,
    color: appChromeColors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
    backgroundColor: appChromeColors.surfaceMuted,
  },
  content: {
    gap: 18,
    paddingBottom: 4,
  },
  group: {
    gap: 8,
  },
  groupTitle: {
    color: appChromeColors.textMuted,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.4,
    textTransform: 'uppercase',
  },
  toolGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  toolItem: {
    flexGrow: 1,
    flexBasis: 145,
    minHeight: 68,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: appChromeColors.borderSoft,
    backgroundColor: appChromeColors.surfaceMuted,
  },
  toolIcon: {
    width: 38,
    height: 38,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    backgroundColor: appChromeColors.primarySoft,
  },
  toolTitle: {
    flex: 1,
    color: appChromeColors.textPrimary,
    fontSize: 13,
    fontWeight: '600',
    lineHeight: 17,
  },
  pressed: {
    opacity: 0.72,
    transform: [{ scale: 0.98 }],
  },
});
