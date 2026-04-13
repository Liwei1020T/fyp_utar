import React from 'react';
import { View } from 'react-native';
import { HeroTextField, HeroText } from './heroui';
import { cn, type HeroTextFieldProps } from './heroui';

interface AppInputProps extends Omit<HeroTextFieldProps, 'variant'> {
  label?: string;
  error?: string;
  helperText?: string;
  className?: string;
  containerClassName?: string;
  inputClassName?: string;
  innerContainerClassName?: string;
  leftAdornment?: React.ReactNode;
  rightAdornment?: React.ReactNode;
  variant?: 'default' | 'minimal';
}

export function AppInput({
  label,
  error,
  helperText,
  className,
  containerClassName,
  inputClassName,
  innerContainerClassName,
  leftAdornment,
  rightAdornment,
  variant = 'default',
  ...props
}: AppInputProps) {
  const isMinimal = variant === 'minimal';

  if (isMinimal) {
    return (
      <View className={cn('mb-4', className)}>
        <View
          className={cn(
            'h-11 flex-row items-center gap-3 rounded-lg border border-[#DDE6F0] bg-white px-4 shadow-sm',
            containerClassName,
            innerContainerClassName
          )}
        >
          {leftAdornment ? <View className="shrink-0">{leftAdornment}</View> : null}
          <HeroTextField
            variant="secondary"
            isInvalid={Boolean(error)}
            className={cn(
              'h-full flex-1 border-0 bg-transparent px-0 text-base text-foreground',
              props.multiline ? 'min-h-24 py-3' : '',
              inputClassName
            )}
            selectionColorClassName="accent-primary-600"
            placeholderColorClassName="field-placeholder"
            {...props}
          />
          {rightAdornment ? <View className="shrink-0">{rightAdornment}</View> : null}
        </View>
      </View>
    );
  }

  return (
    <View className={cn('mb-4', className)}>
      {label && (
        <HeroText className="mb-2 ml-1 text-sm font-semibold text-foreground">
          {label}
        </HeroText>
      )}
      <View
        className={cn(
          'rounded-lg border shadow-soft',
          error ? 'border-danger/20 bg-danger/10' : 'border-[#DDE6F0] bg-white',
          containerClassName
        )}
      >
        <View
          className={cn(
            'min-h-[52px] flex-row items-center gap-3 rounded-lg px-4 py-1',
            error ? 'bg-danger/5' : 'bg-field-background',
            innerContainerClassName
          )}
        >
          {leftAdornment ? <View className="shrink-0">{leftAdornment}</View> : null}
          <HeroTextField
            variant="secondary"
            isInvalid={Boolean(error)}
            className={cn(
              'h-full flex-1 border-0 bg-transparent px-0 text-base text-foreground',
              props.multiline ? 'min-h-24 py-3' : '',
              inputClassName
            )}
            selectionColorClassName="accent-primary-600"
            placeholderColorClassName="field-placeholder"
            {...props}
          />
          {rightAdornment ? <View className="shrink-0">{rightAdornment}</View> : null}
        </View>
      </View>
      {(error || helperText) && (
        <HeroText
          className={cn(
            'mt-2 ml-1 text-xs leading-5',
            error ? 'text-danger' : 'text-muted'
          )}
        >
          {error ?? helperText}
        </HeroText>
      )}
    </View>
  );
}
