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
      <AppCard
        variant="default"
        padding="none"
        contentClassName="min-h-[92px] p-2.5"
      >
        <View
          className={`h-8 w-8 items-center justify-center rounded-[9px] ${accentClassName}`}
          style={{
            width: 32,
            height: 32,
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 9,
          }}
        >
          {icon}
        </View>
        <View className="mt-1.5 min-w-0">
          <HeroText className="text-[12px] font-medium leading-4 tracking-normal text-slate-600" numberOfLines={2}>
            {title}
          </HeroText>
          <HeroText
            className={
              value.length > 7
                ? 'mt-0.5 text-[18px] font-bold tracking-tight text-slate-900'
                : 'mt-0.5 text-[20px] font-bold tracking-tight text-slate-900'
            }
            numberOfLines={1}
          >
            {value}
          </HeroText>
          {subtitle ? (
            <HeroText className="mt-0.5 text-xs leading-4 text-slate-600" numberOfLines={1}>
              {subtitle}
            </HeroText>
          ) : null}
        </View>
      </AppCard>
    </View>
  );
}
