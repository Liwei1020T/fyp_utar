import React from 'react';
import { View } from 'react-native';
import { AppCard, type AppCardVariant } from '../ui/AppCard';
import { HeroText , cn } from '../ui/heroui';

interface AppDetailListItem {
  label: string;
  value: React.ReactNode;
  helper?: React.ReactNode;
}

interface AppDetailListProps {
  items: AppDetailListItem[];
  variant?: AppCardVariant;
  className?: string;
}

export function AppDetailList({
  items,
  variant = 'elevated',
  className,
}: AppDetailListProps) {
  return (
    <AppCard variant={variant} padding="none" className={className}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <View
            key={`${item.label}-${index}`}
            className={cn('px-3.5 py-2.5', !isLast && 'border-b border-neutral-100')}
          >
            <View className="gap-0.5 md:flex-row md:items-start md:justify-between md:gap-3">
              <HeroText className="text-[13px] leading-5 text-neutral-500">
                {item.label}
              </HeroText>
              <View className="md:max-w-[58%] md:items-end">
                {typeof item.value === 'string' ? (
                  <HeroText
                    className="text-[13px] font-semibold leading-5 text-neutral-950 md:text-right"
                  >
                    {item.value}
                  </HeroText>
                ) : (
                  item.value
                )}
              </View>
            </View>
            {item.helper ? (
              <View className="mt-1">
                {typeof item.helper === 'string' ? (
                  <HeroText className="text-[13px] leading-5 text-neutral-500">
                    {item.helper}
                  </HeroText>
                ) : (
                  item.helper
                )}
              </View>
            ) : null}
          </View>
        );
      })}
    </AppCard>
  );
}
