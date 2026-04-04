import React from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { Clock3 } from 'lucide-react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import type { BookingSlot } from '../../types/domain';

interface SlotPickerProps {
  slots: BookingSlot[];
  selectedSlotId?: string;
  onSelect: (slot: BookingSlot) => void;
}

export function SlotPicker({ slots, selectedSlotId, onSelect }: SlotPickerProps) {
  return (
    <FlatList
      horizontal
      data={slots}
      keyExtractor={(item) => item.id}
      showsHorizontalScrollIndicator={false}
      ItemSeparatorComponent={() => <View className="w-3" />}
      contentContainerStyle={{ paddingRight: 8 }}
      renderItem={({ item }) => {
        const isSelected = item.id === selectedSlotId;
        const isAvailable = item.availableSpots > 0;

        return (
          <Pressable
            onPress={() => onSelect(item)}
            disabled={!isAvailable}
            accessibilityRole="button"
            accessibilityLabel={`${item.label} slot`}
            accessibilityState={{ disabled: !isAvailable, selected: isSelected }}
          >
            <AppCard
              variant={isSelected && isAvailable ? 'highlighted' : 'elevated'}
              className={isAvailable ? 'w-36' : 'w-36 opacity-60'}
              padding="md"
            >
              <View className="items-start gap-3">
                <View
                  className={`h-10 w-10 items-center justify-center rounded-2xl ${
                    isAvailable ? 'bg-primary-50' : 'bg-neutral-100'
                  }`}
                >
                  <Clock3 size={18} color={isAvailable ? '#2F64B6' : '#94A3B8'} />
                </View>
                <View>
                  <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                    {item.label}
                  </HeroText>
                  <HeroText className="mt-1 text-sm text-neutral-500">
                    {item.availableSpots} of {item.capacity} left
                  </HeroText>
                </View>
                <AppChip
                  label={item.availableSpots > 0 ? 'Available' : 'Full'}
                  variant={item.availableSpots > 0 ? 'success' : 'danger'}
                />
              </View>
            </AppCard>
          </Pressable>
        );
      }}
    />
  );
}
