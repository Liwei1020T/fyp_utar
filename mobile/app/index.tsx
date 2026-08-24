import React, { useEffect } from 'react';
import { useRouter } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';
import { useAppStore, useCurrentUser } from '../store/appStore';
import { getRoleHome } from '../lib/navigation';
import { AppBrandLogo } from '../components/ui/AppBrandLogo';
import { HeroText } from '../components/ui/heroui';
import { appChromeColors } from '../components/ui/theme';

export default function IndexScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const hasHydrated = useAppStore((state) => state.hasHydrated);

  useEffect(() => {
    if (!hasHydrated) {
      return;
    }

    router.replace((user ? getRoleHome(user.role) : '/auth/login') as never);
  }, [hasHydrated, router, user]);

  return (
    <View
      className="flex-1 items-center justify-center px-8"
      style={{
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        paddingHorizontal: 32,
        backgroundColor: appChromeColors.pageAuth,
      }}
    >
      <View className="items-center" style={{ alignItems: 'center' }}>
        <AppBrandLogo size={80} accessibilityLabel="StringSense brand logo" />
        <HeroText className="mt-7 text-[30px] font-bold leading-[36px] tracking-normal text-[#1D1D1F]">
          StringSense
        </HeroText>
        <HeroText className="mt-2 text-center text-[15px] leading-6 text-[rgba(29,29,31,0.62)]">
          Badminton stringing made simple.
        </HeroText>
        <ActivityIndicator
          className="mt-8"
          color={appChromeColors.primary}
          size="small"
        />
      </View>
    </View>
  );
}
