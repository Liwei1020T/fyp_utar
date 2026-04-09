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
  showBackButton?: boolean;
  onBackPress?: () => void;
  backAccessibilityLabel?: string;
  tone?: AppScreenTone;
}

const appHeaderMetrics = {
  primaryMinHeight: 92,
  secondaryMinHeight: 76,
  flowMinHeight: 80,
} as const;

const baseContainerStyles =
  'w-full self-center overflow-hidden border shadow-soft';

const variantStyles: Record<AppHeaderVariant, string> = {
  primary: 'rounded-[30px] border-[#DCE7F2] bg-[#FAFCFF]',
  secondary: 'rounded-[26px] border-[#E1E9F2] bg-white',
  flow: 'rounded-[26px] border-[#D8E6F7] bg-[#F7FBFF]',
};

const toneAccentStyles: Record<AppScreenTone, string> = {
  default: 'border-l-[#7FB6FF]',
  auth: 'border-l-[#9EB7D5]',
  player: 'border-l-[#7FB6FF]',
  admin: 'border-l-[#8FD4CB]',
};

const contentStyles: Record<AppHeaderVariant, string> = {
  primary: 'px-5 py-4',
  secondary: 'px-4 py-3',
  flow: 'px-4 py-3',
};

const titleStyles: Record<AppHeaderVariant, string> = {
  primary: 'text-[23px] font-bold tracking-tight text-neutral-950',
  secondary: 'text-[18px] font-bold tracking-tight text-neutral-950',
  flow: 'text-[18px] font-bold tracking-tight text-[#163A66]',
};

const subtitleStyles: Record<AppHeaderVariant, string> = {
  primary: 'text-[13px] leading-5 text-neutral-500',
  secondary: 'text-[12px] leading-[18px] text-neutral-500',
  flow: 'text-[12px] leading-[18px] text-[#58708E]',
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
          minHeight: minHeights[variant],
        }}
      >
        <View
          className={cn(
            'flex-row items-center gap-3 border-l-4',
            contentStyles[variant],
            toneAccentStyles[tone]
          )}
        >
          {showBackButton ? (
            <AppIconButton
              icon={<ChevronLeft size={20} color={variant === 'flow' ? '#163A66' : '#0F172A'} />}
              accessibilityLabel={backAccessibilityLabel}
              onPress={onBackPress}
              variant="header"
              size="md"
              className={cn(variant === 'flow' ? 'bg-[#EDF5FF]' : undefined)}
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
            className="mx-4 mb-3 h-1.5 rounded-full"
            style={{ backgroundColor: `${appChromeColors.primary}1A` }}
          >
            <View
              className="h-full w-16 rounded-full"
              style={{ backgroundColor: appChromeColors.primary }}
            />
          </View>
        ) : null}
      </View>
    </View>
  );
}
