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
          className={`h-10 w-10 items-center justify-center rounded-[10px] ${accentClassName}`}
          style={{
            width: 40,
            height: 40,
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 10,
          }}
        >
          {icon}
        </View>
        <HeroText className="mt-3 text-[12px] font-medium leading-4 tracking-normal text-slate-600">
          {title}
        </HeroText>
        <HeroText
          className={
            value.length > 7
              ? 'mt-1 text-[20px] font-bold tracking-tight text-slate-900'
              : 'mt-1 text-[24px] font-bold tracking-tight text-slate-900'
          }
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
