import React from 'react';
import { HeroButton, type HeroButtonProps } from './heroui';
import { cn } from './heroui';
import type { ButtonVariant } from 'heroui-native';

type AppIconButtonVariant = 'surface' | 'auth' | 'primary' | 'ghost' | 'header';
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
    header: 'outline',
  };

  const variantStyles = {
    surface: 'border-[#DDE6F0] bg-white shadow-soft',
    auth: 'border-[#DDE6F0] bg-white',
    primary: 'border-primary-600 bg-primary-600 shadow-soft',
    ghost: 'border-transparent bg-transparent',
    header: 'border-[#DDE6F0] bg-white shadow-none',
  };

  const sizeStyles = {
    md: 'h-10 w-10 rounded-lg',
    lg: 'h-11 w-11 rounded-lg',
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
