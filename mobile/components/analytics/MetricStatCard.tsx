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
        contentClassName="min-h-[104px] p-3"
      >
        <View
          className={`h-9 w-9 items-center justify-center rounded-[10px] ${accentClassName}`}
          style={{
            width: 36,
            height: 36,
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 10,
          }}
        >
          {icon}
        </View>
        <View className="mt-2 min-w-0">
          <HeroText className="text-[12px] font-medium leading-4 tracking-normal text-slate-600" numberOfLines={2}>
            {title}
          </HeroText>
          <HeroText
            className={
              value.length > 7
                ? 'mt-0.5 text-[19px] font-bold tracking-tight text-slate-900'
                : 'mt-0.5 text-[22px] font-bold tracking-tight text-slate-900'
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
