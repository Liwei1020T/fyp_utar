import React from 'react';
import { BottomTabBarHeightContext } from '@react-navigation/bottom-tabs';
import { ScrollView, View, ViewProps } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { HeroText } from '../ui/heroui';
import { cn } from '../ui/heroui';
import { appChromeColors, appLayoutMetrics } from '../ui/theme';

type AppScreenTone = 'default' | 'auth' | 'player' | 'admin';

interface AppScreenProps extends ViewProps {
  children: React.ReactNode;
  scrollable?: boolean;
  title?: string;
  subtitle?: string;
  eyebrow?: string;
  headerRight?: React.ReactNode;
  headerLeft?: React.ReactNode;
  className?: string;
  contentContainerClassName?: string;
  tone?: AppScreenTone;
}

export function useBottomContentInset(extra = 0) {
  const insets = useSafeAreaInsets();
  const tabBarHeight = React.useContext(BottomTabBarHeightContext) ?? 0;

  return Math.max(insets.bottom + 28, tabBarHeight + 22) + extra;
}

export function AppScreen({
  children,
  scrollable = true,
  title,
  subtitle,
  eyebrow,
  headerRight,
  headerLeft,
  footer,
  className,
  contentContainerClassName,
  tone = 'default',
  ...props
}: AppScreenProps) {
  const toneBackgrounds = {
    default: appChromeColors.page,
    auth: appChromeColors.pageAuth,
    player: appChromeColors.page,
    admin: appChromeColors.pageAdmin,
  };

  const headerStyles = {
    default: 'border-white/90 bg-white/72',
    auth: 'border-[#E0E8F1] bg-[#EDF3F9]',
    player: 'border-white/90 bg-white/72',
    admin: 'border-white/90 bg-[#EAF4F3]',
  };

  const headerCoreStyles = {
    default: 'bg-app-surface border-[#E8EEF6]',
    auth: 'bg-app-surface border-[#E1EAF3]',
    player: 'bg-app-surface border-[#E8EEF6]',
    admin: 'bg-app-surface border-[#D9ECE8]',
  };

  const bottomContentInset = useBottomContentInset(scrollable ? 8 : 0);

  return (
    <SafeAreaView
      className="flex-1"
      style={{ backgroundColor: toneBackgrounds[tone] }}
      edges={['top', 'left', 'right', 'bottom']}
    >
      <View className="flex-1">
        {(title || headerRight || headerLeft) && (
          <View className="px-5 pt-4">
            <View
              className={cn(
                'w-full self-center rounded-[28px] border p-1 shadow-soft',
                headerStyles[tone]
              )}
              style={{ maxWidth: appLayoutMetrics.contentMaxWidth }}
            >
              <View
                className={cn(
                  'rounded-[24px] border px-4 py-3',
                  headerCoreStyles[tone]
                )}
              >
                <View className="flex-row items-center justify-between gap-4">
                  <View className="min-w-0 flex-1 flex-row items-center gap-3">
                    {headerLeft}
                    <View className="min-w-0 flex-1">
                      {eyebrow ? (
                        <HeroText className="mb-0.5 text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
                          {eyebrow}
                        </HeroText>
                      ) : null}
                      {title ? (
                        <HeroText className="text-[20px] font-bold tracking-tight text-neutral-950">
                          {title}
                        </HeroText>
                      ) : null}
                      {subtitle ? (
                        <HeroText className="mt-0.5 text-[13px] leading-5 text-neutral-500">
                          {subtitle}
                        </HeroText>
                      ) : null}
                    </View>
                  </View>
                  <View>{headerRight}</View>
                </View>
              </View>
            </View>
          </View>
        )}
        {scrollable ? (
          <ScrollView
            className={cn('flex-1', className)}
            keyboardShouldPersistTaps="handled"
            scrollIndicatorInsets={{ bottom: bottomContentInset }}
            contentContainerStyle={{ flexGrow: 1, paddingBottom: bottomContentInset }}
            {...props}
          >
            <View
              className={cn('flex-1 w-full self-center px-5 pt-4', contentContainerClassName)}
              style={{ maxWidth: appLayoutMetrics.contentMaxWidth }}
            >
              {children}
            </View>
          </ScrollView>
        ) : (
          <View className={cn('flex-1', className)} {...props}>
            <View
              className={cn('flex-1 w-full self-center px-5 pt-4', contentContainerClassName)}
              style={{ maxWidth: appLayoutMetrics.contentMaxWidth }}
            >
              {children}
            </View>
          </View>
        )}
        {footer && (
          <View 
            className="w-full self-center px-5"
            style={{ 
              maxWidth: appLayoutMetrics.contentMaxWidth,
              marginBottom: (React.useContext(BottomTabBarHeightContext) ?? 0) + 16,
            }}
          >
            {footer}
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}
