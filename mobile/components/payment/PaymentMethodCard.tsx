import React from 'react';
import { Pressable, View } from 'react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';

interface PaymentMethodCardProps {
  title: string;
  description: string;
  badge: string;
  icon: React.ReactNode;
  selected?: boolean;
  onPress: () => void;
}

export function PaymentMethodCard({
  title,
  description,
  badge,
  icon,
  selected,
  onPress,
}: PaymentMethodCardProps) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="radio"
      accessibilityLabel={`${title}. ${description}. ${badge}`}
      accessibilityHint="Select this payment method"
      accessibilityState={{ selected: Boolean(selected) }}
    >
      <AppCard variant={selected ? 'highlighted' : 'elevated'} padding="md">
        <View className="flex-row items-start gap-4">
          <View className="h-12 w-12 items-center justify-center rounded-[18px] bg-primary-50">
            {icon}
          </View>
          <View className="flex-1">
            <View className="flex-row items-center justify-between gap-3">
              <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                {title}
              </HeroText>
              <AppChip label={badge} variant={selected ? 'primary' : 'neutral'} />
            </View>
            <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
              {description}
            </HeroText>
          </View>
        </View>
      </AppCard>
    </Pressable>
  );
}
