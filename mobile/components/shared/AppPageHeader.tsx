import React from 'react';
import { View } from 'react-native';
import { ChevronLeft } from 'lucide-react-native';
import { HeroText, cn } from '../ui/heroui';
import { AppIconButton } from '../ui/AppIconButton';
import { appChromeColors, appLayoutMetrics } from '../ui/theme';

export type AppHeaderVariant = 'primary' | 'secondary' | 'flow';
type AppScreenTone = 'default' | 'auth' | 'player' | 'admin';

interface AppPageHeaderProps {
  title?: string;
  subtitle?: string;
  headerRight?: React.ReactNode;
  variant?: AppHeaderVariant;
  compact?: boolean;
  showBackButton?: boolean;
  onBackPress?: () => void;
  backAccessibilityLabel?: string;
  tone?: AppScreenTone;
}

const appHeaderMetrics = {
  primaryMinHeight: 76,
  secondaryMinHeight: 64,
  flowMinHeight: 68,
} as const;

const baseContainerStyles = 'w-full self-center overflow-hidden border-b';

const variantStyles: Record<AppHeaderVariant, string> = {
  primary: 'border-[#D8E0EA] bg-transparent',
  secondary: 'border-[#D8E0EA] bg-transparent',
  flow: 'border-[#D8E0EA] bg-transparent',
};

const contentStyles: Record<AppHeaderVariant, string> = {
  primary: 'px-1 py-4',
  secondary: 'px-1 py-3',
  flow: 'px-1 py-3',
};

const titleStyles: Record<AppHeaderVariant, string> = {
  primary: 'text-[24px] font-bold tracking-tight text-slate-900',
  secondary: 'text-[17px] font-semibold tracking-normal text-slate-900',
  flow: 'text-[17px] font-semibold tracking-normal text-slate-900',
};

const subtitleStyles: Record<AppHeaderVariant, string> = {
  primary: 'text-[14px] leading-[20px] tracking-normal text-slate-600',
  secondary: 'text-[12px] leading-[18px] tracking-normal text-slate-600',
  flow: 'text-[12px] leading-[18px] tracking-normal text-slate-600',
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
  tone = 'default',
}: AppPageHeaderProps) {
  if (!title && !headerRight && !showBackButton) {
    return null;
  }

  return (
    <View
      className="px-4"
      style={{
        paddingTop: appLayoutMetrics.headerTopSpacing,
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
        <View
          className={cn(
            'flex-row items-center gap-3',
            contentStyles[variant],
            compact && variant === 'primary' ? 'px-1 py-3' : undefined,
            compact && variant !== 'primary' ? 'px-1 py-2.5' : undefined
          )}
        >
          {showBackButton ? (
            <AppIconButton
              icon={<ChevronLeft size={18} color={appChromeColors.primary} />}
              accessibilityLabel={backAccessibilityLabel}
              onPress={onBackPress}
              variant="header"
              size="md"
              className={cn(variant === 'flow' ? 'bg-primary-50' : undefined)}
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
                className={cn(subtitleStyles[variant], title ? 'mt-1' : undefined)}
                numberOfLines={3}
              >
                {subtitle}
              </HeroText>
            ) : null}
          </View>

          {headerRight ? <View className="shrink-0">{headerRight}</View> : null}
        </View>
        {variant === 'flow' ? (
          <View
            className="mb-2 h-px"
            style={{ backgroundColor: 'rgba(37, 99, 235, 0.12)' }}
          >
            <View
              className="h-full w-12"
              style={{ backgroundColor: appChromeColors.primary }}
            />
          </View>
        ) : null}
      </View>
    </View>
  );
}
