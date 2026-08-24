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
  accessibilityHint,
  accessibilityLabel,
  accessibilityRole,
  accessibilityState,
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
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-5',
  };

  const shellStyles = {
    default: 'bg-white border border-field-border shadow-none',
    elevated: 'bg-white border border-field-border shadow-soft',
    highlighted: 'bg-primary-50 border border-primary-200 shadow-none',
    subtle: 'bg-app-muted border border-separator shadow-none',
    dark: 'bg-app-hero border border-white/10 shadow-float',
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
        'overflow-hidden rounded-[18px]',
        shellStyles[variant],
        className
      )}
      {...props}
      {...(onPress
        ? {}
        : { accessibilityHint, accessibilityLabel, accessibilityRole, accessibilityState })}
    >
      <View
        className={cn(
          'overflow-hidden rounded-[18px]',
          coreStyles[variant]
        )}
      >
        {onPress ? (
          <Pressable
            onPress={onPress}
            accessibilityHint={accessibilityHint}
            accessibilityLabel={accessibilityLabel}
            accessibilityRole={accessibilityRole ?? 'button'}
            accessibilityState={accessibilityState}
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
    opacity: 0.94,
    transform: [{ scale: 0.99 }],
  },
});
