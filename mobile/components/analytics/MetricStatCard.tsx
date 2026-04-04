import React from 'react';
import { View } from 'react-native';
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
  return (
    <AppCard variant="elevated" className="flex-1" padding="md">
      <View className="flex-row items-center justify-between gap-3">
        <View className={`h-11 w-11 items-center justify-center rounded-[18px] ${accentClassName}`}>
          {icon}
        </View>
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
          {title}
        </HeroText>
      </View>
      <HeroText className="mt-5 text-[28px] font-bold tracking-tight text-neutral-950">
        {value}
      </HeroText>
      {subtitle ? (
        <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
          {subtitle}
        </HeroText>
      ) : null}
    </AppCard>
  );
}
