import React from 'react';
import { Image, View } from 'react-native';
import { cn } from './heroui';

interface AppBrandLogoProps {
  size?: number;
  accessibilityLabel?: string;
  className?: string;
}

export function AppBrandLogo({
  size = 48,
  accessibilityLabel = 'StringSense logo',
  className,
}: AppBrandLogoProps) {
  const borderRadius = Math.max(10, Math.round(size * 0.24));

  return (
    <View
      className={cn('overflow-hidden bg-[#020B24]', className)}
      style={{ width: size, height: size, borderRadius }}
    >
      <Image
        source={require('../../assets/icon.png')}
        resizeMode="cover"
        accessible
        accessibilityLabel={accessibilityLabel}
        className="h-full w-full"
      />
    </View>
  );
}
