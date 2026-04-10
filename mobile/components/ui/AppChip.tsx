import React from 'react';
import { HeroChip, HeroText, type HeroChipProps } from './heroui';
import { cn } from './heroui';

interface AppChipProps extends Omit<HeroChipProps, 'children' | 'variant'> {
  label: string;
  variant?: AppChipVariant;
  className?: string;
  onPress?: () => void;
  size?: 'sm' | 'md';
}

export type AppChipVariant =
  | 'primary'
  | 'secondary'
  | 'accent'
  | 'neutral'
  | 'complete'
  | 'success'
  | 'warning'
  | 'danger'
  | 'error'
  | 'info';

export function AppChip({
  label,
  variant = 'neutral',
  className,
  onPress,
  size = 'sm',
  ...props
}: AppChipProps) {
  const variantStyles = {
    primary: 'bg-primary-50 border-primary-100',
    secondary: 'bg-secondary-50 border-secondary-100',
    accent: 'bg-accent-50 border-accent-100',
    neutral: 'bg-neutral-100 border-neutral-200',
    complete: 'bg-complete-50 border-complete-100',
    success: 'bg-success-50 border-success-100',
    warning: 'bg-warning-50 border-warning-100',
    danger: 'bg-red-50 border-red-100',
    error: 'bg-red-50 border-red-100',
    info: 'bg-secondary-50 border-secondary-100',
  };

  const textStyles = {
    primary: 'text-primary-700 font-semibold text-xs',
    secondary: 'text-secondary-700 font-semibold text-xs',
    accent: 'text-accent-700 font-semibold text-xs',
    neutral: 'text-neutral-600 font-medium text-xs',
    complete: 'text-complete-700 font-semibold text-xs',
    success: 'text-success-700 font-semibold text-xs',
    warning: 'text-warning-700 font-semibold text-xs',
    danger: 'text-red-700 font-semibold text-xs',
    error: 'text-red-700 font-semibold text-xs',
    info: 'text-secondary-700 font-semibold text-xs',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 min-h-8 rounded-full',
    md: 'px-3.5 py-2 min-h-10 rounded-full',
  };

  return (
    <HeroChip
      accessibilityRole={onPress ? 'button' : undefined}
      className={cn(
        'border',
        sizeStyles[size],
        variantStyles[variant],
        className
      )}
      onPress={onPress}
      {...props}
    >
      <HeroText className={textStyles[variant]}>
        {label}
      </HeroText>
    </HeroChip>
  );
}
