import React from 'react';
import { View } from 'react-native';
import { Activity, ChevronLeft } from 'lucide-react-native';
import { AppScreen } from '../shared/AppScreen';
import { AppIconButton } from '../ui/AppIconButton';
import { AppCard } from '../ui/AppCard';
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
      contentContainerClassName="justify-center py-4"
    >
      <View className="w-full self-center" style={{ maxWidth: 460 }}>
        <View className="mb-6 flex-row items-center justify-between gap-4">
          <View className="flex-row items-center gap-3">
            <View className="h-12 w-12 items-center justify-center rounded-lg bg-primary-50">
              <Activity size={22} color={appChromeColors.primary} />
            </View>
            <View>
              <HeroText className="text-[11px] font-semibold uppercase tracking-normal text-primary-700">
                StringSense
              </HeroText>
              <HeroText className="mt-1 text-lg font-bold tracking-normal text-neutral-950">
                Badminton stringing
              </HeroText>
            </View>
          </View>
          {onBack ? (
            <AppIconButton
              icon={<ChevronLeft size={20} color="#0F172A" />}
              accessibilityLabel="Go back"
              variant="auth"
              onPress={onBack}
            />
          ) : null}
        </View>

        <AppCard variant="elevated" padding="lg">
          {eyebrow ? (
            <AppChip
              label={eyebrow}
              variant="secondary"
              className="self-start"
            />
          ) : null}
          <HeroText className="mt-4 text-[30px] font-bold tracking-normal text-neutral-950">
            {title}
          </HeroText>
          {subtitle ? (
            <HeroText className="mt-2 text-[15px] leading-6 text-neutral-500">
              {subtitle}
            </HeroText>
          ) : null}
          <View className="mt-6">{children}</View>
        </AppCard>

        {footer ? <View className="mt-5">{footer}</View> : null}
      </View>
    </AppScreen>
  );
}
