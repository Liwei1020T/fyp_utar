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
    default: 'mt-7',
    compact: 'mt-5',
    hero: 'mt-8',
  };

  const titleStyles = {
    default: 'text-[19px] font-semibold tracking-tight text-slate-900 leading-tight',
    compact: 'text-[17px] font-semibold tracking-tight text-slate-900 leading-tight',
    hero: 'text-[24px] font-semibold tracking-tight text-slate-900 leading-tight',
  };

  return (
    <View className={cn(spacingStyles[variant], className)} {...props}>
      {(title || rightAction) && (
        <View className="mb-3.5 flex-row items-start justify-between gap-4">
          <View className="flex-1">
            {eyebrow ? (
              <HeroText className="mb-1 text-[12px] font-medium tracking-normal text-primary-700">
                {eyebrow}
              </HeroText>
            ) : null}
            {title && (
              <HeroText className={titleStyles[variant]}>
                {title}
              </HeroText>
            )}
            {subtitle && (
              <HeroText className="mt-1 text-[14px] leading-5 text-slate-600">
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
