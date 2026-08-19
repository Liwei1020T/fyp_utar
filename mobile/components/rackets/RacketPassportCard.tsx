import React from 'react';
import { Pressable, View } from 'react-native';
import { ChevronRight, Dumbbell } from 'lucide-react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import type { RacketPassport } from '../../types/domain';

interface RacketPassportCardProps {
  racket: RacketPassport;
  currentStringLabel: string;
  onPress: () => void;
}

export function RacketPassportCard({ racket, currentStringLabel, onPress }: RacketPassportCardProps) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${racket.nickname}. ${racket.brand} ${racket.model}. ${racket.currentTension} pounds, ${currentStringLabel}, ${racket.serviceCount} services`}
      accessibilityHint="Open this racket passport"
    >
      <AppCard variant="elevated" padding="md">
        <View className="flex-row items-start gap-4">
          <View className="h-12 w-12 items-center justify-center rounded-[18px] bg-primary-50">
            <Dumbbell size={20} color="#2F64B6" />
          </View>
          <View className="flex-1">
            <View className="flex-row items-start justify-between gap-3">
              <View className="flex-1">
                <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                  {racket.nickname}
                </HeroText>
                <HeroText className="mt-1 text-sm leading-6 text-neutral-500">
                  {racket.brand} {racket.model}
                </HeroText>
              </View>
              <ChevronRight size={18} color="#94A3B8" />
            </View>
            <View className="mt-4 flex-row flex-wrap gap-2">
              <AppChip label={`${racket.currentTension} lbs`} variant="primary" />
              <AppChip label={currentStringLabel} variant="secondary" />
              <AppChip label={`${racket.serviceCount} services`} variant="neutral" />
            </View>
          </View>
        </View>
      </AppCard>
    </Pressable>
  );
}
