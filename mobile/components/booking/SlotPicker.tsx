import React from 'react';
import { AppSelect } from '../ui/AppSelect';
import type { BookingSlot } from '../../types/domain';

interface SlotPickerProps {
  slots: BookingSlot[];
  selectedSlotId?: string;
  onSelect: (slot: BookingSlot) => void;
}

export function SlotPicker({ slots, selectedSlotId, onSelect }: SlotPickerProps) {
  return (
    <AppSelect
      label="Drop-off time"
      value={selectedSlotId}
      placeholder="Choose an available time"
      options={slots.map((item) => ({
        id: item.id,
        label: item.label,
        description:
          item.availableSpots > 0
            ? `${item.availableSpots} ${item.availableSpots === 1 ? 'slot' : 'slots'} left`
            : 'Full',
        disabled: item.availableSpots < 1,
      }))}
      onChange={(id) => {
        const selectedSlot = slots.find((item) => item.id === id);
        if (selectedSlot && selectedSlot.availableSpots > 0) {
          onSelect(selectedSlot);
        }
      }}
    />
  );
}
