import React from 'react';
import { HeroButton, HeroChip, HeroSlider, HeroText, HeroTextField } from '../components/ui/heroui';

export function HeroCompatSmoke() {
  return (
    <>
      <HeroText className="text-lg font-bold">StringSense</HeroText>
      <HeroButton
        label="Continue"
        textClassName="text-white"
        onPress={() => undefined}
      />
      <HeroChip onPress={() => undefined}>
        <HeroText className="text-xs">Badge</HeroText>
      </HeroChip>
      <HeroTextField
        placeholder="Email"
        value=""
        onChangeText={() => undefined}
      />
      <HeroSlider
        value={5}
        minimumValue={1}
        maximumValue={10}
        step={1}
        onValueChange={() => undefined}
      />
    </>
  );
}
