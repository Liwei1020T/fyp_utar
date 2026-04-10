import React from 'react';
import { Pressable, View } from 'react-native';
import { CheckCircle2, Clock3 } from 'lucide-react-native';
import { HeroText } from '../ui/heroui';
import type { BookingSlot } from '../../types/domain';

interface SlotPickerProps {
  slots: BookingSlot[];
  selectedSlotId?: string;
  onSelect: (slot: BookingSlot) => void;
}

export function SlotPicker({ slots, selectedSlotId, onSelect }: SlotPickerProps) {
  return (
    <View className="flex-row flex-wrap gap-3">
      {slots.map((item) => {
        const isSelected = item.id === selectedSlotId;
        const isAvailable = item.availableSpots > 0;

        return (
          <Pressable
            key={item.id}
            onPress={() => onSelect(item)}
            disabled={!isAvailable}
            accessibilityRole="button"
            accessibilityLabel={`${item.label} slot`}
            accessibilityState={{ disabled: !isAvailable, selected: isSelected }}
            className={`min-w-[47%] flex-1 rounded-[24px] border ${
              isSelected && isAvailable
                ? 'border-primary-500 bg-primary-50'
                : isAvailable
                  ? 'border-white bg-white/95'
                  : 'border-neutral-200 bg-neutral-100/80 opacity-70'
            }`}
          >
            <View className="rounded-[24px] p-4">
              <View className="flex-row items-start justify-between gap-3">
                <View className="flex-1">
                  <View className="flex-row items-center gap-2">
                    <Clock3 size={16} color={isAvailable ? '#2F64B6' : '#94A3B8'} />
                    <HeroText className="text-[15px] font-bold tracking-tight text-neutral-950">
                      {item.label}
                    </HeroText>
                  </View>
                  <HeroText className="mt-2 text-[12px] leading-5 text-neutral-500">
                    {isAvailable
                      ? `${item.availableSpots} ${item.availableSpots === 1 ? 'slot' : 'slots'} left`
                      : 'Fully booked'}
                  </HeroText>
                </View>
                {isSelected && isAvailable ? (
                  <CheckCircle2 size={18} color="#2F64B6" />
                ) : null}
              </View>
            </View>
          </Pressable>
        );
      })}
    </View>
  );
}
