import React from 'react';
import { Pressable, View } from 'react-native';
import type { LucideIcon } from 'lucide-react-native';
import { HeroText, cn } from './heroui';

type SegmentedOption<T extends string> = {
  id: T;
  label: string;
  icon?: LucideIcon;
};

interface AppSegmentedControlProps<T extends string> {
  options: readonly SegmentedOption<T>[];
  selectedId: T;
  onSelect: (id: T) => void;
  className?: string;
  contentClassName?: string;
  segmentClassName?: string;
}

export function AppSegmentedControl<T extends string>({
  options,
  selectedId,
  onSelect,
  className,
  contentClassName,
  segmentClassName,
}: AppSegmentedControlProps<T>) {
  if (options.length === 0) {
    return null;
  }

  const activeId = options.some((option) => option.id === selectedId)
    ? selectedId
    : options[0].id;

  return (
    <View
      accessibilityRole="tablist"
      className={cn('border border-neutral-200 bg-white p-1', className, 'rounded-[14px]')}
    >
      <View className={cn('flex-row gap-1', contentClassName)}>
        {options.map((option) => {
          const isSelected = option.id === activeId;
          const Icon = option.icon;

          return (
            <Pressable
              key={option.id}
              accessibilityRole="tab"
              accessibilityLabel={option.label}
              accessibilityState={{ selected: isSelected }}
              onPress={() => onSelect(option.id)}
              className={cn(
                'min-h-11 flex-1 flex-row items-center justify-center gap-2 rounded-[10px] px-3 py-2',
                isSelected ? 'bg-primary-600 shadow-soft' : 'bg-transparent',
                segmentClassName,
                'rounded-[10px]',
              )}
            >
              {Icon ? (
                <Icon
                  size={15}
                  strokeWidth={2.5}
                  color={isSelected ? '#FFFFFF' : '#64748B'}
                />
              ) : null}
              <HeroText
                className={cn(
                  'text-[12px] font-semibold leading-5',
                  isSelected ? 'text-white' : 'text-neutral-500',
                )}
              >
                {option.label}
              </HeroText>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}
