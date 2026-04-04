import React from 'react';
import { HeroButton, type HeroButtonProps } from './heroui';
import { cn } from './heroui';
import type { ButtonVariant } from 'heroui-native';

type AppIconButtonVariant = 'surface' | 'auth' | 'primary' | 'ghost';
type AppIconButtonSize = 'md' | 'lg';

interface AppIconButtonProps
  extends Omit<HeroButtonProps, 'children' | 'variant' | 'feedbackVariant' | 'animation'> {
  icon: React.ReactNode;
  accessibilityLabel: string;
  variant?: AppIconButtonVariant;
  size?: AppIconButtonSize;
  className?: string;
}

export function AppIconButton({
  icon,
  accessibilityLabel,
  variant = 'surface',
  size = 'md',
  className,
  ...props
}: AppIconButtonProps) {
  const nativeVariantMap: Record<AppIconButtonVariant, ButtonVariant> = {
    surface: 'outline',
    auth: 'outline',
    primary: 'primary',
    ghost: 'ghost',
  };

  const variantStyles = {
    surface: 'border-white/90 bg-white shadow-soft',
    auth: 'border-[#E4EBE5] bg-white',
    primary: 'border-primary-600 bg-primary-600 shadow-glow',
    ghost: 'border-transparent bg-transparent',
  };

  const sizeStyles = {
    md: 'h-11 w-11 rounded-full',
    lg: 'h-12 w-12 rounded-full',
  };

  return (
    <HeroButton
      {...props}
      variant={nativeVariantMap[variant]}
      isIconOnly
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      className={cn(
        'items-center justify-center border',
        sizeStyles[size],
        variantStyles[variant],
        className
      )}
      hitSlop={6}
    >
      {icon}
    </HeroButton>
  );
}
