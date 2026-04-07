import React from 'react';
import { Image, View } from 'react-native';
import { AppCard } from '../ui/AppCard';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import type { BookingUpdate } from '../../types/domain';

interface BookingUpdatesProps {
  updates: BookingUpdate[];
}

function formatUpdateDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export function BookingUpdates({ updates }: BookingUpdatesProps) {
  if (updates.length === 0) {
    return (
      <AppCard variant="subtle" padding="md">
        <HeroText className="text-sm leading-6 text-neutral-600">
          No booking photos or comments have been added yet.
        </HeroText>
      </AppCard>
    );
  }

  return (
    <View className="gap-3">
      {updates.map((item) => (
        <AppCard key={item.id} variant="elevated" padding="md">
          <View className="gap-3">
            <View className="flex-row items-center justify-between gap-3">
              <AppChip
                label={item.authorRole === 'admin' ? 'Admin update' : 'Player update'}
                variant={item.authorRole === 'admin' ? 'primary' : 'secondary'}
              />
              <HeroText className="text-xs font-medium text-neutral-500">
                {formatUpdateDate(item.createdAt)}
              </HeroText>
            </View>
            {item.comment ? (
              <HeroText className="text-sm leading-6 text-neutral-700">
                {item.comment}
              </HeroText>
            ) : null}
            {item.photoUrl ? (
              <Image
                source={{ uri: item.photoUrl }}
                className="h-48 w-full rounded-[24px] bg-neutral-100"
                resizeMode="cover"
                accessibilityLabel={item.photoOriginalName ?? 'Booking update photo'}
              />
            ) : null}
          </View>
        </AppCard>
      ))}
    </View>
  );
}
