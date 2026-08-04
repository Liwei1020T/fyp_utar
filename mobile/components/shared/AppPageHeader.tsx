import React from 'react';
import { Image, View } from 'react-native';
import { ChevronLeft } from 'lucide-react-native';
import { HeroText, cn } from '../ui/heroui';
import { AppIconButton } from '../ui/AppIconButton';
import { appChromeColors, appLayoutMetrics } from '../ui/theme';

export type AppHeaderVariant = 'primary' | 'secondary' | 'flow';

interface AppPageHeaderProps {
  title?: string;
  headerRight?: React.ReactNode;
  variant?: AppHeaderVariant;
  compact?: boolean;
  showBackButton?: boolean;
  onBackPress?: () => void;
  backAccessibilityLabel?: string;
}

const appHeaderMetrics = {
  primaryMinHeight: 84,
  secondaryMinHeight: 68,
  flowMinHeight: 76,
} as const;

const baseContainerStyles = 'w-full self-center overflow-hidden border';

const variantStyles: Record<AppHeaderVariant, string> = {
  primary: 'rounded-[28px] border-[#D6E4FF] bg-[#EAF2FF] shadow-subtle',
  secondary: 'rounded-[22px] border-[#DCE3EC] bg-white shadow-subtle',
  flow: 'rounded-[24px] border-[#163B7A] bg-[#102F63] shadow-float',
};

const contentStyles: Record<AppHeaderVariant, string> = {
  primary: 'px-5 py-4',
  secondary: 'px-4 py-3',
  flow: 'px-4 py-4',
};

const titleStyles: Record<AppHeaderVariant, string> = {
  primary: 'text-[27px] font-bold leading-[32px] tracking-tight text-slate-900',
  secondary: 'text-[17px] font-semibold tracking-normal text-slate-900',
  flow: 'text-[20px] font-bold leading-6 tracking-tight text-white',
};

const minHeights: Record<AppHeaderVariant, number> = {
  primary: appHeaderMetrics.primaryMinHeight,
  secondary: appHeaderMetrics.secondaryMinHeight,
  flow: appHeaderMetrics.flowMinHeight,
};

export function AppPageHeader({
  title,
  headerRight,
  variant = 'primary',
  compact = false,
  showBackButton = false,
  onBackPress,
  backAccessibilityLabel = 'Go back',
}: AppPageHeaderProps) {
  if (!title && !headerRight && !showBackButton) {
    return null;
  }

  return (
    <View
      className="px-4"
      style={{
        paddingTop: Math.max(appLayoutMetrics.headerTopSpacing - 2, 0),
        maxWidth: appLayoutMetrics.contentMaxWidth,
        width: '100%',
        alignSelf: 'center',
      }}
    >
      <View
        className={cn(baseContainerStyles, variantStyles[variant])}
        style={{
          maxWidth: appLayoutMetrics.contentMaxWidth,
          minHeight: compact ? Math.max(minHeights[variant] - 12, 56) : minHeights[variant],
        }}
      >
        {variant === 'flow' ? (
          <Image
            source={require('../../assets/ui/header-string-weave.png')}
            resizeMode="cover"
            className="absolute inset-0 h-full w-full opacity-70"
          />
        ) : null}

        <View
          className={cn(
            'flex-row items-center gap-3',
            contentStyles[variant],
            compact && variant === 'primary' ? 'py-3.5' : undefined,
            compact && variant === 'secondary' ? 'py-2.5' : undefined
          )}
        >
          {showBackButton ? (
            <AppIconButton
              icon={
                <ChevronLeft
                  size={18}
                  color={variant === 'flow' ? '#FFFFFF' : appChromeColors.primary}
                />
              }
              accessibilityLabel={backAccessibilityLabel}
              onPress={onBackPress}
              variant="header"
              size="md"
              className={cn(
                variant === 'flow'
                  ? 'border-white/20 bg-white/10'
                  : 'border-primary-100 bg-primary-50'
              )}
            />
          ) : null}

          <View className="min-w-0 flex-1">
            {title ? (
              <HeroText
                accessibilityRole="header"
                className={titleStyles[variant]}
                numberOfLines={2}
              >
                {title}
              </HeroText>
            ) : null}
          </View>

          {headerRight ? <View className="shrink-0">{headerRight}</View> : null}
        </View>
      </View>
    </View>
  );
}
