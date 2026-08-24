import React from 'react';
import { Platform, TextInput, type TextInputProps, View } from 'react-native';
import { HeroText , cn } from './heroui';
import { appChromeColors } from './theme';

interface AppInputProps extends TextInputProps {
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
  isDisabled?: boolean;
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
  isDisabled = false,
  ...props
}: AppInputProps) {
  const isMinimal = variant === 'minimal';
  const [isFocused, setIsFocused] = React.useState(false);
  const focusBorder = isFocused ? 'border-primary-600' : 'border-field-border';
  const inputAccessibilityLabel = props.accessibilityLabel ?? label ?? props.placeholder;
  const inputAccessibilityHint = props.accessibilityHint ?? error ?? helperText;
  const inputAccessibilityState = {
    ...props.accessibilityState,
    disabled: isDisabled || props.editable === false || props.accessibilityState?.disabled,
  };
  const webInputReset =
    Platform.OS === 'web'
      ? ({ outlineStyle: 'none', boxShadow: 'none', borderWidth: 0 } as any)
      : undefined;

  if (isMinimal) {
    return (
      <View className={cn('mb-4', className)}>
        <View
          className={cn(
          'h-12 flex-row items-center gap-3 rounded-[10px] border bg-white px-4',
            error ? 'border-danger/30' : focusBorder,
            containerClassName,
            innerContainerClassName,
            'rounded-[10px]',
          )}
        >
          {leftAdornment ? <View className="shrink-0">{leftAdornment}</View> : null}
          <TextInput
            {...props}
            accessibilityHint={inputAccessibilityHint}
            accessibilityLabel={inputAccessibilityLabel}
            accessibilityState={inputAccessibilityState}
            className={cn(
              'h-full flex-1 border-0 bg-transparent px-0 text-base text-foreground',
              props.multiline ? 'min-h-24 py-3' : '',
              inputClassName
            )}
            style={webInputReset}
            onBlur={(event) => {
              setIsFocused(false);
              props.onBlur?.(event);
            }}
            onFocus={(event) => {
              setIsFocused(true);
              props.onFocus?.(event);
            }}
            editable={!isDisabled && props.editable !== false}
            placeholderTextColor={appChromeColors.textMuted}
            selectionColor={appChromeColors.primary}
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
          'rounded-[10px] border bg-white',
          error ? 'border-danger/30' : focusBorder,
          containerClassName,
          'rounded-[10px]',
        )}
      >
        <View
          className={cn(
            'min-h-[52px] flex-row items-center gap-3 rounded-[10px] px-4 py-1',
            error ? 'bg-danger/5' : 'bg-field-background',
            innerContainerClassName,
            'rounded-[10px]',
          )}
        >
          {leftAdornment ? <View className="shrink-0">{leftAdornment}</View> : null}
          <TextInput
            {...props}
            accessibilityHint={inputAccessibilityHint}
            accessibilityLabel={inputAccessibilityLabel}
            accessibilityState={inputAccessibilityState}
            className={cn(
              'h-full flex-1 border-0 bg-transparent px-0 text-base text-foreground',
              props.multiline ? 'min-h-24 py-3' : '',
              inputClassName
            )}
            style={webInputReset}
            onBlur={(event) => {
              setIsFocused(false);
              props.onBlur?.(event);
            }}
            onFocus={(event) => {
              setIsFocused(true);
              props.onFocus?.(event);
            }}
            editable={!isDisabled && props.editable !== false}
            placeholderTextColor={appChromeColors.textMuted}
            selectionColor={appChromeColors.primary}
          />
          {rightAdornment ? <View className="shrink-0">{rightAdornment}</View> : null}
        </View>
      </View>
      {(error || helperText) && (
        <HeroText
          accessibilityLiveRegion={error ? 'polite' : 'none'}
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
