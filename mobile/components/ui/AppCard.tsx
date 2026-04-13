import React from 'react';
import { Pressable, StyleSheet, View, ViewProps } from 'react-native';
import { Surface } from 'heroui-native';
import { cn } from './heroui';
import type { SurfaceVariant } from 'heroui-native';

export type AppCardVariant =
  | 'default'
  | 'elevated'
  | 'highlighted'
  | 'subtle'
  | 'dark';

interface AppCardProps extends ViewProps {
  onPress?: () => void;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  variant?: AppCardVariant;
  contentClassName?: string;
}

export function AppCard({
  children,
  onPress,
  className,
  padding = 'md',
  variant = 'default',
  contentClassName,
  ...props
}: AppCardProps) {
  const nativeVariantMap: Record<AppCardVariant, SurfaceVariant> = {
    default: 'default',
    elevated: 'secondary',
    highlighted: 'secondary',
    subtle: 'tertiary',
    dark: 'default',
  };

  const paddingStyles = {
    none: 'p-0',
    sm: 'p-3.5',
    md: 'p-5',
    lg: 'p-6',
  };

  const shellStyles = {
    default: 'bg-white border border-[#D2D2D7] shadow-soft',
    elevated: 'bg-white border border-transparent shadow-float',
    highlighted: 'bg-primary-50 border border-primary-100 shadow-soft',
    subtle: 'bg-[#F1F5F9] border border-[#E1E8F0] shadow-none',
    dark: 'bg-[#1D1D1F] border border-[#2A2A2D] shadow-float',
  };

  const coreStyles = {
    default: 'bg-app-surface',
    elevated: 'bg-app-surface-elevated',
    highlighted: 'bg-primary-50',
    subtle: 'bg-app-muted',
    dark: 'bg-app-hero',
  };

  return (
    <Surface
      variant={nativeVariantMap[variant]}
      className={cn(
        'overflow-hidden rounded-lg',
        shellStyles[variant],
        className
      )}
      {...props}
    >
      <View
        className={cn(
          'overflow-hidden rounded-lg',
          coreStyles[variant]
        )}
      >
        {onPress ? (
          <Pressable
            onPress={onPress}
            accessibilityRole="button"
            className={cn(paddingStyles[padding], contentClassName)}
            style={({ pressed }) => (pressed ? styles.pressed : undefined)}
          >
            {children}
          </Pressable>
        ) : (
          <View className={cn(paddingStyles[padding], contentClassName)}>{children}</View>
        )}
      </View>
    </Surface>
  );
}

const styles = StyleSheet.create({
  pressed: {
    opacity: 0.96,
    transform: [{ scale: 0.992 }],
  },
});
