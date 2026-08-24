import React from 'react';
import { Image, View } from 'react-native';
import { ChevronLeft } from 'lucide-react-native';
import { AppScreen } from '../shared/AppScreen';
import { AppBrandLogo } from '../ui/AppBrandLogo';
import { AppIconButton } from '../ui/AppIconButton';
import { HeroText } from '../ui/heroui';

interface AuthShellProps {
  title: string;
  onBack?: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function AuthShell({
  title,
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
          className="mb-8 flex-row items-center justify-between gap-4 overflow-hidden rounded-[28px] border border-[#163B7A] bg-app-hero px-5 py-5 shadow-float"
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            marginBottom: 32,
          }}
        >
          <Image
            source={require('../../assets/ui/header-string-weave.png')}
            resizeMode="cover"
            className="absolute inset-0 h-full w-full opacity-70"
            accessible={false}
          />
          <View
            className="min-w-0 flex-row items-center gap-3"
            style={{ minWidth: 0, flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12 }}
          >
            <AppBrandLogo size={48} accessibilityLabel="StringSense brand logo" />
            <View className="min-w-0 flex-1" style={{ minWidth: 0, flex: 1 }}>
              <HeroText className="text-[17px] font-semibold tracking-tight text-white">
                StringSense
              </HeroText>
            </View>
          </View>
          {onBack ? (
            <AppIconButton
              icon={<ChevronLeft size={20} color="#FFFFFF" />}
              accessibilityLabel="Go back"
              variant="auth"
              className="border-white/20 bg-white/10"
              onPress={onBack}
            />
          ) : null}
        </View>

        <View className="mb-6" style={{ marginBottom: 24 }}>
          <HeroText
            accessibilityRole="header"
            className="text-[34px] font-bold leading-[39px] tracking-tight text-[#1D1D1F]"
          >
            {title}
          </HeroText>
        </View>

        <View>{children}</View>

        {footer ? <View className="mt-5" style={{ marginTop: 20 }}>{footer}</View> : null}
      </View>
    </AppScreen>
  );
}
