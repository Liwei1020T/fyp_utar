import React, { useEffect, useRef } from 'react';
import { View, type ViewProps } from 'react-native';
import { gsap } from 'gsap';

interface AppMotionProps extends ViewProps {
  children: React.ReactNode;
  delay?: number;
}

export function AppMotion({ children, delay = 0, ...props }: AppMotionProps) {
  const containerRef = useRef<View>(null);

  useEffect(() => {
    const target = containerRef.current;
    if (!target || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }

    const context = gsap.context(() => {
      gsap.fromTo(
        target,
        { autoAlpha: 0, y: 8 },
        {
          autoAlpha: 1,
          y: 0,
          duration: 0.24,
          delay: delay / 1000,
          ease: 'power2.out',
          clearProps: 'opacity,transform,visibility',
        },
      );
    });

    return () => context.revert();
  }, [delay]);

  return (
    <View ref={containerRef} {...props}>
      {children}
    </View>
  );
}
