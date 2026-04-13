import React from 'react';
import { View } from 'react-native';
import { HeroButton, HeroButtonProps } from './heroui';
import { cn } from './heroui';
import type { ButtonVariant } from 'heroui-native';

export type AppButtonVariant =
  | 'primary'
  | 'secondary'
  | 'accent'
  | 'outline'
  | 'ghost'
  | 'danger'
  | 'success'
  | 'dark';

export type AppButtonSize = 'sm' | 'md' | 'lg';

type AppButtonProps = Omit<HeroButtonProps, 'size' | 'variant' | 'feedbackVariant' | 'animation'> & {
  variant?: AppButtonVariant;
  size?: AppButtonSize;
  className?: string;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
  isLoading?: boolean;
};

export function AppButton({
  variant = 'primary',
  size = 'md',
  className,
  textClassName,
  label,
  children,
  leadingIcon,
  trailingIcon,
  isLoading = false,
  ...props
}: AppButtonProps) {
  const nativeVariantMap: Record<AppButtonVariant, ButtonVariant> = {
    primary: 'primary',
    secondary: 'secondary',
    accent: 'secondary',
    outline: 'outline',
    ghost: 'ghost',
    danger: 'danger',
    success: 'primary',
    dark: 'primary',
  };

  const variantStyles = {
    primary: 'bg-primary-600 border-primary-600 shadow-soft',
    secondary: 'bg-secondary-50 border-secondary-200',
    accent: 'bg-accent-100 border-accent-200',
    outline: 'bg-white border-[#DDE6F0]',
    ghost: 'bg-transparent border-transparent',
    danger: 'bg-red-600 border-red-600',
    success: 'bg-success-600 border-success-600',
    dark: 'bg-[#1D1D1F] border-[#1D1D1F] shadow-soft',
  };

  const textStyles = {
    primary: 'text-white font-semibold tracking-normal',
    secondary: 'text-secondary-700 font-semibold tracking-normal',
    accent: 'text-accent-900 font-semibold tracking-normal',
    outline: 'text-neutral-700 font-semibold tracking-normal',
    ghost: 'text-neutral-600 font-medium tracking-normal',
    danger: 'text-white font-semibold tracking-normal',
    success: 'text-white font-semibold tracking-normal',
    dark: 'text-white font-semibold tracking-normal',
  };

  const sizeStyles = {
    sm: 'h-10 px-4 py-2 rounded-lg',
    md: 'h-[50px] px-5 py-2.5 rounded-lg',
    lg: 'h-[56px] px-6 py-3 rounded-lg',
  };

  const trailingIslandStyles = {
    primary: 'bg-white/14',
    secondary: 'bg-secondary-200/80',
    accent: 'bg-accent-200/80',
    outline: 'bg-neutral-100',
    ghost: 'bg-neutral-100',
    danger: 'bg-white/14',
    success: 'bg-white/14',
    dark: 'bg-white/10',
  };

  const content = children ?? (
    <View className="flex-row items-center justify-center gap-3">
      {leadingIcon ? <View className="shrink-0">{leadingIcon}</View> : null}
      {label ? (
        <HeroButton.Label className={cn(textStyles[variant], textClassName)}>
          {isLoading ? 'Loading...' : label}
        </HeroButton.Label>
      ) : null}
      {trailingIcon ? (
        <View
          className={cn(
            'ml-1 h-8 w-8 items-center justify-center rounded-full',
            trailingIslandStyles[variant]
          )}
        >
          {trailingIcon}
        </View>
      ) : null}
    </View>
  );

  return (
    <HeroButton
      variant={nativeVariantMap[variant]}
      className={cn(
        'items-center justify-center border disabled:opacity-60',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
      isDisabled={isLoading || props.isDisabled}
    >
      {content}
    </HeroButton>
  );
}
