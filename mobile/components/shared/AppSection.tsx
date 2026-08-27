import React from 'react';
import { View, ViewProps } from 'react-native';
import { HeroText , cn } from '../ui/heroui';

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
    default: 'mt-5',
    compact: 'mt-3',
    hero: 'mt-5',
  };

  const titleStyles = {
    default: 'text-[16px] font-semibold tracking-tight text-slate-900 leading-tight',
    compact: 'text-[15px] font-semibold tracking-tight text-slate-900 leading-tight',
    hero: 'text-[18px] font-semibold tracking-tight text-slate-900 leading-tight',
  };

  return (
    <View className={cn(spacingStyles[variant], className)} {...props}>
      {(title || rightAction) && (
        <View className="mb-2 flex-row items-start justify-between gap-2.5">
          <View className="flex-1">
            {eyebrow ? (
              <HeroText className="mb-0.5 text-[11px] font-medium tracking-normal text-primary-700">
                {eyebrow}
              </HeroText>
            ) : null}
            {title && (
              <HeroText className={titleStyles[variant]}>
                {title}
              </HeroText>
            )}
            {subtitle && (
              <HeroText className="mt-0.5 text-[13px] leading-[18px] text-slate-600">
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
