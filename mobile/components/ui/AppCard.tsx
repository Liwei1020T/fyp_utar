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
    default: 'bg-white/80 border border-white/90 shadow-soft',
    elevated: 'bg-white/85 border border-white shadow-float',
    highlighted: 'bg-primary-100/70 border border-primary-100 shadow-glow',
    subtle: 'bg-white/75 border border-white/90 shadow-soft',
    dark: 'bg-primary-200/20 border border-white/30 shadow-glow',
  };

  const coreStyles = {
    default: 'bg-app-surface border border-[#E8EEF6]',
    elevated: 'bg-app-surface-elevated border border-white',
    highlighted: 'bg-primary-50 border border-primary-100/90',
    subtle: 'bg-app-muted border border-white/80',
    dark: 'bg-app-hero border border-white/10',
  };

  return (
    <Surface
      variant={nativeVariantMap[variant]}
      className={cn(
        'overflow-hidden rounded-[26px] p-1',
        shellStyles[variant],
        className
      )}
      {...props}
    >
      <View
        className={cn(
          'overflow-hidden rounded-[22px]',
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
