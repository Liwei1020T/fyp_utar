import React from 'react';
import { View } from 'react-native';
import { HeroTextField, HeroText } from './heroui';
import { cn, type HeroTextFieldProps } from './heroui';

interface AppInputProps extends HeroTextFieldProps {
  label?: string;
  error?: string;
  helperText?: string;
  className?: string;
  containerClassName?: string;
  inputClassName?: string;
  leftAdornment?: React.ReactNode;
  rightAdornment?: React.ReactNode;
}

export function AppInput({
  label,
  error,
  helperText,
  className,
  containerClassName,
  inputClassName,
  leftAdornment,
  rightAdornment,
  ...props
}: AppInputProps) {
  return (
    <View className={cn('mb-4', className)}>
      {label && (
        <HeroText className="mb-2 ml-1 text-sm font-semibold text-foreground">
          {label}
        </HeroText>
      )}
      <View
        className={cn(
          'rounded-[28px] border p-1.5 shadow-soft',
          error ? 'border-danger/20 bg-danger/10' : 'border-separator bg-surface-secondary',
          containerClassName
        )}
      >
        <View
          className={cn(
            'min-h-14 flex-row items-center gap-3 rounded-[24px] border px-4 py-1',
            error ? 'border-danger/15 bg-danger/5' : 'border-field-border bg-field-background'
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
