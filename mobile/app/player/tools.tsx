import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronRight } from 'lucide-react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppCard } from '../../components/ui/AppCard';
import { HeroText } from '../../components/ui/heroui';
import { appChromeColors } from '../../components/ui/theme';
import { playerToolGroups } from '../../components/player/PlayerToolsSheet';

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
      {playerToolGroups.map((group, groupIndex) => (
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
