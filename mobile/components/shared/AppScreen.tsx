import React from 'react';
import { BottomTabBarHeightContext } from '@react-navigation/bottom-tabs';
import { ScrollView, useWindowDimensions, View, ViewProps } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { cn } from '../ui/heroui';
import { appChromeColors, appLayoutMetrics } from '../ui/theme';
import { AppMotion } from '../ui/AppMotion';
import { AppHeaderVariant, AppPageHeader } from './AppPageHeader';

type AppScreenTone = 'default' | 'auth' | 'player' | 'admin';

interface AppScreenProps extends ViewProps {
  children: React.ReactNode;
  scrollable?: boolean;
  title?: string;
  subtitle?: string;
  headerRight?: React.ReactNode;
  headerVariant?: AppHeaderVariant;
  compactHeader?: boolean;
  showBackButton?: boolean;
  onBackPress?: () => void;
  backAccessibilityLabel?: string;
  className?: string;
  contentContainerClassName?: string;
  tone?: AppScreenTone;
  footer?: React.ReactNode;
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
  headerRight,
  headerVariant = 'primary',
  compactHeader = false,
  showBackButton = false,
  onBackPress,
  backAccessibilityLabel,
  footer,
  className,
  contentContainerClassName,
  tone = 'default',
  style,
  ...props
}: AppScreenProps) {
  const toneBackgrounds = {
    default: appChromeColors.page,
    auth: appChromeColors.pageAuth,
    player: appChromeColors.page,
    admin: appChromeColors.pageAdmin,
  };

  const insets = useSafeAreaInsets();
  const bottomContentInset = useBottomContentInset(scrollable ? 8 : 0);
  const tabBarHeight = React.useContext(BottomTabBarHeightContext) ?? 0;
  const { width } = useWindowDimensions();
  let pagePadding: number = appLayoutMetrics.pagePadding;
  if (width >= 1024) {
    pagePadding = appLayoutMetrics.desktopPagePadding;
  } else if (width >= 768) {
    pagePadding = appLayoutMetrics.tabletPagePadding;
  }

  return (
    <SafeAreaView
      className="flex-1"
      style={{ flex: 1, backgroundColor: toneBackgrounds[tone] }}
      edges={['top', 'left', 'right', 'bottom']}
    >
      <View className="flex-1" style={{ flex: 1 }}>
        <AppMotion delay={0}>
          <AppPageHeader
            title={title}
            subtitle={subtitle}
            headerRight={headerRight}
            variant={headerVariant}
            compact={compactHeader}
            showBackButton={showBackButton}
            onBackPress={onBackPress}
            backAccessibilityLabel={backAccessibilityLabel}
          />
        </AppMotion>
        {scrollable ? (
          <ScrollView
            className={cn('flex-1', className)}
            style={[
              {
                flex: 1,
              },
              style,
            ]}
            keyboardShouldPersistTaps="handled"
            scrollIndicatorInsets={{ bottom: bottomContentInset }}
            contentContainerStyle={{ flexGrow: 1, paddingBottom: bottomContentInset }}
            {...props}
          >
            <AppMotion
              delay={40}
              className={cn('flex-1 w-full self-center px-4 pt-4', contentContainerClassName)}
              style={{
                flex: 1,
                width: '100%',
                alignSelf: 'center',
                maxWidth: appLayoutMetrics.contentMaxWidth,
                paddingHorizontal: pagePadding,
                paddingTop: 12,
              }}
            >
              {children}
            </AppMotion>
          </ScrollView>
        ) : (
          <View
            className={cn('flex-1', className)}
            style={[
              {
                flex: 1,
              },
              style,
            ]}
            {...props}
          >
            <AppMotion
              delay={40}
              className={cn('flex-1 w-full self-center px-4 pt-4', contentContainerClassName)}
              style={{
                flex: 1,
                width: '100%',
                alignSelf: 'center',
                maxWidth: appLayoutMetrics.contentMaxWidth,
                paddingHorizontal: pagePadding,
                paddingTop: 12,
              }}
            >
              {children}
            </AppMotion>
          </View>
        )}
        {footer && (
          <View 
            className="w-full self-center px-4"
            style={{ 
              maxWidth: appLayoutMetrics.contentMaxWidth,
              marginBottom: Math.max(insets.bottom, tabBarHeight) + 16,
            }}
          >
            {footer}
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}
