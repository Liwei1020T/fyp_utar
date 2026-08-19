import React from 'react';
import {
  Button,
  Chip,
  Input,
  Slider,
  type ButtonRootProps,
  type ChipProps,
  type InputProps,
  type SliderProps,
} from 'heroui-native';
import {
  Text,
  Platform,
  type View as RNView,
  type TextInput as RNTextInput,
  type Text as RNText,
  type TextProps,
} from 'react-native';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const NativeText = Text as unknown as React.ComponentType<any>;

export interface HeroTextProps extends TextProps {
  className?: string;
}

export const HeroText = React.forwardRef<RNText, HeroTextProps>(
  ({ className, style, ...props }, ref) => (
    <NativeText
      ref={ref}
      className={cn('font-normal text-foreground', className)}
      style={[
        Platform.OS === 'web'
          ? ({
              textRendering: 'optimizeLegibility',
              WebkitFontSmoothing: 'antialiased',
              MozOsxFontSmoothing: 'grayscale',
            } as any)
          : undefined,
        style,
      ]}
      {...props}
    />
  ),
);

HeroText.displayName = 'HeroText';

export type HeroButtonProps = ButtonRootProps & {
  children?: React.ReactNode;
  label?: string;
  textClassName?: string;
};

type HeroButtonComponent = React.ForwardRefExoticComponent<
  HeroButtonProps & React.RefAttributes<RNView>
> & {
  Label: typeof Button.Label;
};

const HeroButtonRoot = React.forwardRef<RNView, HeroButtonProps>(
  ({ children, label, textClassName, ...props }, ref) => {
    const content = children
      ?? (label ? <Button.Label className={textClassName}>{label}</Button.Label> : null);

    return (
      <Button ref={ref} {...props}>
        {content}
      </Button>
    );
  },
);

HeroButtonRoot.displayName = 'HeroButton';

export const HeroButton = Object.assign(
  HeroButtonRoot,
  { Label: Button.Label },
) as HeroButtonComponent;

HeroButton.displayName = 'HeroButton';

export type HeroChipProps = ChipProps;

export const HeroChip = Chip;

export type HeroTextFieldProps = InputProps;

export const HeroTextField = React.forwardRef<RNTextInput, HeroTextFieldProps>(
  (props, ref) => <Input ref={ref} {...props} />,
);

HeroTextField.displayName = 'HeroTextField';

export interface HeroSliderProps
  extends Omit<
    SliderProps,
    'children' | 'defaultValue' | 'maxValue' | 'minValue' | 'onChange' | 'onChangeEnd' | 'value'
  > {
  children?: React.ReactNode;
  defaultValue?: number;
  maximumValue?: number;
  minimumValue?: number;
  onSlidingComplete?: (value: number) => void;
  onValueChange?: (value: number) => void;
  value?: number;
}

export function HeroSlider({
  children,
  defaultValue,
  maximumValue,
  minimumValue,
  onSlidingComplete,
  onValueChange,
  value,
  ...props
}: HeroSliderProps) {
  return (
    <Slider
      defaultValue={defaultValue}
      maxValue={maximumValue}
      minValue={minimumValue}
      onChange={(nextValue) =>
        onValueChange?.(Array.isArray(nextValue) ? nextValue[0] ?? 0 : nextValue)
      }
      onChangeEnd={(nextValue) =>
        onSlidingComplete?.(Array.isArray(nextValue) ? nextValue[0] ?? 0 : nextValue)
      }
      value={value}
      {...props}
    >
      {children ?? (
        <Slider.Track>
          <Slider.Fill />
          <Slider.Thumb />
        </Slider.Track>
      )}
    </Slider>
  );
}
