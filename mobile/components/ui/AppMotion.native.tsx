import React from 'react';
import { type ViewProps } from 'react-native';
import Animated, { FadeInDown, ReduceMotion } from 'react-native-reanimated';

interface AppMotionProps extends ViewProps {
  children: React.ReactNode;
  delay?: number;
}

export function AppMotion({ children, delay = 0, ...props }: AppMotionProps) {
  const entering = FadeInDown.duration(220)
    .delay(delay)
    .withInitialValues({ opacity: 0, transform: [{ translateY: 8 }] })
    .reduceMotion(ReduceMotion.System);

  return (
    <Animated.View entering={entering} {...props}>
      {children}
    </Animated.View>
  );
}
