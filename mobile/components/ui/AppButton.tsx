import React from 'react';
import { View, type AccessibilityState } from 'react-native';
import { HeroButton, type HeroButtonProps, cn } from './heroui';
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
  accessibilityLabel,
  accessibilityState,
  isDisabled,
  ...props
}: AppButtonProps) {
  const resolvedAccessibilityState = accessibilityState as
    | AccessibilityState
    | undefined;
  const disabled =
    isLoading || Boolean(isDisabled) || Boolean(resolvedAccessibilityState?.disabled);
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
    primary: 'bg-primary-600 border-primary-600 shadow-soft active:bg-primary-700',
    secondary: 'bg-white border-primary-200',
    accent: 'bg-accent-100 border-accent-200',
    outline: 'bg-white border-primary-200',
    ghost: 'bg-transparent border-transparent',
    danger: 'bg-danger border-danger',
    success: 'bg-success-600 border-success-600',
    dark: 'bg-secondary-600 border-secondary-600 shadow-soft',
  };

  const textStyles = {
    primary: 'text-white font-semibold tracking-normal',
    secondary: 'text-primary-700 font-semibold tracking-normal',
    accent: 'text-accent-700 font-semibold tracking-normal',
    outline: 'text-slate-900 font-semibold tracking-normal',
    ghost: 'text-slate-600 font-medium tracking-normal',
    danger: 'text-white font-semibold tracking-normal',
    success: 'text-white font-semibold tracking-normal',
    dark: 'text-white font-semibold tracking-normal',
  };

  const sizeStyles = {
    sm: 'h-11 px-4 py-2 rounded-lg',
    md: 'h-[50px] px-5 py-2.5 rounded-lg',
    lg: 'h-[56px] px-6 py-3 rounded-lg',
  };

  const trailingIslandStyles = {
    primary: 'bg-white/14',
    secondary: 'bg-primary-50',
    accent: 'bg-accent-200/80',
    outline: 'bg-slate-100',
    ghost: 'bg-slate-100',
    danger: 'bg-white/14',
    success: 'bg-white/14',
    dark: 'bg-white/10',
  };

  const content = children ?? (
    <View className="flex-row items-center justify-center gap-3">
      {leadingIcon ? <View className="shrink-0">{leadingIcon}</View> : null}
      {label ? (
        <HeroButton.Label className={cn(textStyles[variant], textClassName)}>
          {isLoading ? `${label}…` : label}
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
      {...props}
      feedbackVariant="none"
      variant={nativeVariantMap[variant]}
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{
        ...resolvedAccessibilityState,
        busy: isLoading,
        disabled,
      }}
      className={cn(
        'items-center justify-center border disabled:opacity-60',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      isDisabled={disabled}
    >
      {content}
    </HeroButton>
  );
}
