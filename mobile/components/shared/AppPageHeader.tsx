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
  primaryMinHeight: 88,
  secondaryMinHeight: 72,
  flowMinHeight: 76,
} as const;

const baseContainerStyles =
  'w-full self-center overflow-hidden border';

const variantStyles: Record<AppHeaderVariant, string> = {
  primary: 'rounded-[18px] border-[#E6EDF5] bg-[#F7F8FB]',
  secondary: 'rounded-[16px] border-[#E6EDF5] bg-[#F7F8FB]',
  flow: 'rounded-[16px] border-[#E1EAF5] bg-[#F7F8FB]',
};

const contentStyles: Record<AppHeaderVariant, string> = {
  primary: 'px-5 py-4',
  secondary: 'px-4 py-3',
  flow: 'px-4 py-3',
};

const titleStyles: Record<AppHeaderVariant, string> = {
  primary: 'text-[20px] font-semibold tracking-[-0.03em] text-[#1D1D1F]',
  secondary: 'text-[17px] font-semibold tracking-[-0.02em] text-[#1D1D1F]',
  flow: 'text-[17px] font-semibold tracking-[-0.02em] text-[#1D1D1F]',
};

const subtitleStyles: Record<AppHeaderVariant, string> = {
  primary: 'text-[14px] leading-[20px] tracking-[-0.01em] text-[rgba(29,29,31,0.72)]',
  secondary: 'text-[12px] leading-[18px] tracking-[-0.01em] text-[rgba(29,29,31,0.68)]',
  flow: 'text-[12px] leading-[18px] tracking-[-0.01em] text-[rgba(29,29,31,0.68)]',
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
    <View className="px-5" style={{ paddingTop: appLayoutMetrics.headerTopSpacing }}>
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
            compact && variant === 'primary' ? 'px-4 py-3' : undefined,
            compact && variant !== 'primary' ? 'px-3.5 py-2.5' : undefined
          )}
        >
          {showBackButton ? (
            <AppIconButton
              icon={<ChevronLeft size={18} color="#0071E3" />}
              accessibilityLabel={backAccessibilityLabel}
              onPress={onBackPress}
              variant="header"
              size="md"
              className={cn(variant === 'flow' ? 'bg-[#F0F5FD]' : undefined)}
            />
          ) : null}

          <View className="min-w-0 flex-1">
            {title ? (
              <HeroText className={titleStyles[variant]} numberOfLines={1}>
                {title}
              </HeroText>
            ) : null}
            {subtitle ? (
              <HeroText
                className={cn(subtitleStyles[variant], title ? 'mt-1' : undefined)}
                numberOfLines={2}
              >
                {subtitle}
              </HeroText>
            ) : null}
          </View>

          {headerRight ? <View className="shrink-0">{headerRight}</View> : null}
        </View>
        {variant === 'flow' ? (
          <View
            className="mx-4 mb-3 h-px"
            style={{ backgroundColor: 'rgba(47, 100, 182, 0.12)' }}
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
