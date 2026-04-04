import React from 'react';
import { View, ViewProps } from 'react-native';
import { HeroText } from '../ui/heroui';
import { cn } from '../ui/heroui';

type AppSectionVariant = 'default' | 'compact' | 'hero';

interface AppSectionProps extends ViewProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  rightAction?: React.ReactNode;
  className?: string;
  eyebrow?: string;
  variant?: AppSectionVariant;
}

export function AppSection({
  title,
  subtitle,
  children,
  rightAction,
  className,
  eyebrow,
  variant = 'default',
  ...props
}: AppSectionProps) {
  const spacingStyles = {
    default: 'mt-9',
    compact: 'mt-6',
    hero: 'mt-12',
  };

  const titleStyles = {
    default: 'text-[22px] font-bold tracking-tight text-neutral-950 leading-tight',
    compact: 'text-lg font-bold tracking-tight text-neutral-950 leading-tight',
    hero: 'text-[28px] font-bold tracking-tight text-neutral-950 leading-tight',
  };

  return (
    <View className={cn(spacingStyles[variant], className)} {...props}>
      {(title || rightAction) && (
        <View className="mb-4 flex-row items-start justify-between gap-4">
          <View className="flex-1">
            {eyebrow ? (
              <HeroText className="mb-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-700">
                {eyebrow}
              </HeroText>
            ) : null}
            {title && (
              <HeroText className={titleStyles[variant]}>
                {title}
              </HeroText>
            )}
            {subtitle && (
              <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                {subtitle}
              </HeroText>
            )}
          </View>
          {rightAction}
        </View>
      )}
      <View>{children}</View>
    </View>
  );
}
