import React from 'react';
import { View } from 'react-native';
import { Activity, ChevronLeft } from 'lucide-react-native';
import { AppScreen } from '../shared/AppScreen';
import { AppIconButton } from '../ui/AppIconButton';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import { appChromeColors } from '../ui/theme';

interface AuthShellProps {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  onBack?: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function AuthShell({
  title,
  subtitle,
  eyebrow,
  onBack,
  children,
  footer,
}: AuthShellProps) {
  return (
    <AppScreen
      tone="auth"
      contentContainerClassName="justify-center py-8"
    >
      <View className="w-full self-center" style={{ maxWidth: 430 }}>
        <View className="mb-8 flex-row items-center justify-between gap-4">
          <View className="min-w-0 flex-row items-center gap-3">
            <View className="h-11 w-11 items-center justify-center rounded-lg bg-white shadow-soft">
              <Activity size={21} color={appChromeColors.primary} />
            </View>
            <View className="min-w-0 flex-1">
              <HeroText className="text-[15px] font-semibold tracking-normal text-[#1D1D1F]">
                StringSense
              </HeroText>
              <HeroText className="mt-0.5 text-[12px] leading-4 text-[rgba(29,29,31,0.58)]">
                Badminton stringing
              </HeroText>
            </View>
          </View>
          {onBack ? (
            <AppIconButton
              icon={<ChevronLeft size={20} color="#1D1D1F" />}
              accessibilityLabel="Go back"
              variant="auth"
              onPress={onBack}
            />
          ) : null}
        </View>

        <View className="mb-6">
          {eyebrow ? (
            <AppChip
              label={eyebrow}
              variant="secondary"
              className="self-start"
            />
          ) : null}
          <HeroText className="mt-4 text-[32px] font-bold leading-[38px] tracking-normal text-[#1D1D1F]">
            {title}
          </HeroText>
          {subtitle ? (
            <HeroText className="mt-2 text-[15px] leading-6 text-[rgba(29,29,31,0.68)]">
              {subtitle}
            </HeroText>
          ) : null}
        </View>

        <View>{children}</View>

        {footer ? <View className="mt-5">{footer}</View> : null}
      </View>
    </AppScreen>
  );
}
