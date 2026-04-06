import React from 'react';
import { View } from 'react-native';
import { AppCard, type AppCardVariant } from '../ui/AppCard';
import { HeroText } from '../ui/heroui';
import { cn } from '../ui/heroui';

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
            className={cn('p-4', !isLast && 'border-b border-neutral-100')}
          >
            <View className="gap-1 md:flex-row md:items-start md:justify-between md:gap-4">
              <HeroText className="text-sm text-neutral-500">
                {item.label}
              </HeroText>
              <View className="md:max-w-[58%] md:items-end">
                {typeof item.value === 'string' ? (
                  <HeroText className="text-sm font-semibold leading-6 text-neutral-950 md:text-right">
                    {item.value}
                  </HeroText>
                ) : (
                  item.value
                )}
              </View>
            </View>
            {item.helper ? (
              <View className="mt-2">
                {typeof item.helper === 'string' ? (
                  <HeroText className="text-sm leading-6 text-neutral-500">
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
