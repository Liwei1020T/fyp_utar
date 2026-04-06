import React from 'react';
import { View, useWindowDimensions } from 'react-native';
import { AppCard } from '../ui/AppCard';
import { HeroText } from '../ui/heroui';

interface MetricStatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  accentClassName?: string;
  icon: React.ReactNode;
}

export function MetricStatCard({
  title,
  value,
  subtitle,
  accentClassName = 'bg-primary-50',
  icon,
}: MetricStatCardProps) {
  const { width } = useWindowDimensions();
  const flexBasis =
    width >= 900 ? '23%' : width >= 640 ? '31%' : '47%';

  return (
    <View style={{ flexBasis, flexGrow: 1, minWidth: 148 }}>
      <AppCard variant="elevated" className="h-full" padding="md">
        <View
          className={`h-11 w-11 items-center justify-center rounded-[18px] ${accentClassName}`}
        >
          {icon}
        </View>
        <HeroText className="mt-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
          {title}
        </HeroText>
        <HeroText
          className="mt-2 text-[26px] font-bold tracking-tight text-neutral-950"
          numberOfLines={1}
          adjustsFontSizeToFit
        >
          {value}
        </HeroText>
        {subtitle ? (
          <HeroText className="mt-1 text-sm leading-5 text-neutral-500">
            {subtitle}
          </HeroText>
        ) : null}
      </AppCard>
    </View>
  );
}
