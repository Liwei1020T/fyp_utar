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
  const cardWidth =
    width >= 900 ? '18.5%' : width >= 640 ? '31%' : width >= 360 ? '47%' : '100%';

  return (
    <View style={{ width: cardWidth, minWidth: 0 }}>
      <AppCard variant="elevated" padding="sm">
        <View
          className={`h-11 w-11 items-center justify-center rounded-[18px] border border-white/70 ${accentClassName}`}
          style={{
            width: 44,
            height: 44,
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 18,
          }}
        >
          {icon}
        </View>
        <HeroText className="mt-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">
          {title}
        </HeroText>
        <HeroText
          className="mt-1.5 text-[26px] font-bold tracking-tight text-slate-900"
          numberOfLines={1}
          adjustsFontSizeToFit
        >
          {value}
        </HeroText>
        {subtitle ? (
          <HeroText className="mt-1 text-sm leading-5 text-slate-600">
            {subtitle}
          </HeroText>
        ) : null}
      </AppCard>
    </View>
  );
}
