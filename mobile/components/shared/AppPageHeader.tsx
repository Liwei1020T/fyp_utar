import React from 'react';
import { Image, View } from 'react-native';
import { ChevronLeft } from 'lucide-react-native';
import { HeroText, cn } from '../ui/heroui';
import { AppIconButton } from '../ui/AppIconButton';
import { appChromeColors, appLayoutMetrics } from '../ui/theme';

export type AppHeaderVariant = 'primary' | 'secondary' | 'flow';

interface AppPageHeaderProps {
  title?: string;
  subtitle?: string;
  headerRight?: React.ReactNode;
  variant?: AppHeaderVariant;
  compact?: boolean;
  showBackButton?: boolean;
  onBackPress?: () => void;
  backAccessibilityLabel?: string;
}

const appHeaderMetrics = {
  primaryMinHeight: 64,
  secondaryMinHeight: 54,
  flowMinHeight: 64,
} as const;

const baseContainerStyles = 'w-full self-center overflow-hidden border';

const variantStyles: Record<AppHeaderVariant, string> = {
  primary: 'rounded-[14px] border-[#D6E4FF] bg-[#EAF2FF] shadow-subtle',
  secondary: 'rounded-[14px] border-[#DCE3EC] bg-white shadow-subtle',
  flow: 'rounded-[14px] border-[#163B7A] bg-[#102F63] shadow-float',
};

const contentStyles: Record<AppHeaderVariant, string> = {
  primary: 'px-3 py-2.5',
  secondary: 'px-3 py-2',
  flow: 'px-3 py-2.5',
};

const titleStyles: Record<AppHeaderVariant, string> = {
  primary: 'text-[18px] font-bold leading-[22px] tracking-tight text-slate-900',
  secondary: 'text-[15px] font-semibold leading-[19px] tracking-normal text-slate-900',
  flow: 'text-[17px] font-bold leading-[21px] tracking-tight text-white',
};

const minHeights: Record<AppHeaderVariant, number> = {
  primary: appHeaderMetrics.primaryMinHeight,
  secondary: appHeaderMetrics.secondaryMinHeight,
  flow: appHeaderMetrics.flowMinHeight,
};

export function AppPageHeader({
  title,
  subtitle,
  headerRight,
  variant = 'primary',
  compact = false,
  showBackButton = false,
  onBackPress,
  backAccessibilityLabel = 'Go back',
}: AppPageHeaderProps) {
  if (!title && !subtitle && !headerRight && !showBackButton) {
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
            accessible={false}
          />
        ) : null}

        <View
          className={cn(
            'flex-row items-center gap-2.5',
            contentStyles[variant],
            compact && variant === 'primary' ? 'py-2.5' : undefined,
            compact && variant === 'secondary' ? 'py-2' : undefined
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
            {subtitle ? (
              <HeroText
                className={cn(
                  'mt-0.5 text-[12px] leading-4',
                  variant === 'flow' ? 'text-secondary-100' : 'text-slate-600',
                )}
                numberOfLines={compact && variant === 'flow' ? 1 : 2}
              >
                {subtitle}
              </HeroText>
            ) : null}
          </View>

          {headerRight ? <View className="shrink-0">{headerRight}</View> : null}
        </View>
      </View>
    </View>
  );
}
