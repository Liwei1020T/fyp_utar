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
      <View className="w-full self-center" style={{ width: '100%', alignSelf: 'center', maxWidth: 430 }}>
        <View
          className="mb-9 flex-row items-center justify-between gap-4"
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            marginBottom: 36,
          }}
        >
          <View
            className="min-w-0 flex-row items-center gap-3"
            style={{ minWidth: 0, flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12 }}
          >
            <View
              className="h-12 w-12 items-center justify-center rounded-[16px] bg-app-hero shadow-float"
              style={{
                width: 48,
                height: 48,
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 16,
                backgroundColor: appChromeColors.hero,
              }}
            >
              <Activity size={22} color="#FFFFFF" />
            </View>
            <View className="min-w-0 flex-1" style={{ minWidth: 0, flex: 1 }}>
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

        <View className="mb-6" style={{ marginBottom: 24 }}>
          {eyebrow ? (
            <AppChip
              label={eyebrow}
              variant="secondary"
              className="self-start"
            />
          ) : null}
          <HeroText
            accessibilityRole="header"
            className="mt-4 text-[34px] font-bold leading-[39px] tracking-tight text-[#1D1D1F]"
          >
            {title}
          </HeroText>
          {subtitle ? (
            <HeroText className="mt-2 text-[15px] leading-6 text-[rgba(29,29,31,0.68)]">
              {subtitle}
            </HeroText>
          ) : null}
        </View>

        <View>{children}</View>

        {footer ? <View className="mt-5" style={{ marginTop: 20 }}>{footer}</View> : null}
      </View>
    </AppScreen>
  );
}
