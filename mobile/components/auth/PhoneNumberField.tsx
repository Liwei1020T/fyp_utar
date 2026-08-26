import React, { useState } from 'react';
import { Pressable, TextInput, View } from 'react-native';
import { Check, ChevronDown, Phone } from 'lucide-react-native';
import { HeroText } from '../ui/heroui';
import { appChromeColors } from '../ui/theme';

export const countryDialCodes = [
  { value: '+60', label: '+60', caption: 'Malaysia' },
  { value: '+65', label: '+65', caption: 'Singapore' },
  { value: '+62', label: '+62', caption: 'Indonesia' },
] as const;

export const LOCAL_PHONE_DIGIT_LIMIT = 10;

export function normalizePhoneNumber(value: string) {
  return value.replace(/\D/g, '');
}

export function splitPhoneIdentifier(identifier: string) {
  const cleanedIdentifier = identifier.trim();
  const matchedCode = countryDialCodes.find((item) =>
    cleanedIdentifier.startsWith(item.value),
  );

  if (!matchedCode) {
    return {
      countryCode: countryDialCodes[0].value,
      phoneNumber: normalizePhoneNumber(cleanedIdentifier),
    };
  }

  return {
    countryCode: matchedCode.value,
    phoneNumber: normalizePhoneNumber(
      cleanedIdentifier.slice(matchedCode.value.length),
    ),
  };
}

export function composePhoneIdentifier(
  countryCode: string,
  phoneNumber: string,
) {
  const normalizedNumber = normalizePhoneNumber(phoneNumber).replace(/^0+/, '');
  return `${countryCode}${normalizedNumber}`;
}

interface PhoneNumberFieldProps {
  countryCode: string;
  error?: string | null;
  helperText?: string;
  label?: string;
  onChangeCountryCode: (value: string) => void;
  onChangePhoneNumber: (value: string) => void;
  placeholder?: string;
  value: string;
}

export function PhoneNumberField({
  countryCode,
  error,
  helperText,
  label = 'Phone number',
  onChangeCountryCode,
  onChangePhoneNumber,
  placeholder = '1234567890',
  value,
}: PhoneNumberFieldProps) {
  const [isCountryPickerOpen, setIsCountryPickerOpen] = useState(false);
  const selectedCountry =
    countryDialCodes.find((item) => item.value === countryCode) ??
    countryDialCodes[0];

  return (
    <View className="relative z-20 gap-2">
      <HeroText className="ml-1 text-sm font-semibold text-foreground">
        {label}
      </HeroText>
      <View
        className={`flex-row items-center rounded-lg border bg-white shadow-soft ${
          isCountryPickerOpen ? 'border-primary-600' : 'border-[#D2D2D7]'
        }`}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Choose country code"
          accessibilityState={{ expanded: isCountryPickerOpen }}
          onPress={() => setIsCountryPickerOpen((current) => !current)}
          className="h-14 min-w-[94px] flex-row items-center justify-center gap-1.5 border-r border-[#D2D2D7] px-3"
        >
          <HeroText className="text-[15px] font-semibold text-[#1D1D1F]">
            {selectedCountry.value}
          </HeroText>
          <ChevronDown
            size={15}
            color="#1D1D1F"
            strokeWidth={2}
            style={{
              transform: [{ rotate: isCountryPickerOpen ? '180deg' : '0deg' }],
            }}
          />
        </Pressable>
        <Phone
          size={17}
          color="rgba(29,29,31,0.48)"
          strokeWidth={2}
          className="ml-3"
        />
        <TextInput
          accessibilityLabel={label}
          accessibilityHint={error ?? helperText}
          placeholder={placeholder}
          keyboardType="phone-pad"
          maxLength={LOCAL_PHONE_DIGIT_LIMIT}
          value={value}
          onChangeText={(nextValue) =>
            onChangePhoneNumber(
              normalizePhoneNumber(nextValue).slice(0, LOCAL_PHONE_DIGIT_LIMIT),
            )
          }
          placeholderTextColor="rgba(29,29,31,0.48)"
          selectionColor={appChromeColors.primary}
          className="h-14 flex-1 border-0 bg-transparent px-3 text-[15px] text-[#1D1D1F] outline-none"
        />
      </View>
      {isCountryPickerOpen ? (
        <View className="absolute left-0 right-0 top-[78px] z-30 overflow-hidden rounded-lg border border-[#D2D2D7] bg-white shadow-float">
          {countryDialCodes.map((item) => {
            const isSelected = countryCode === item.value;

            return (
              <Pressable
                key={item.value}
                accessibilityRole="radio"
                accessibilityLabel={`${item.caption}, ${item.value}`}
                accessibilityState={{ checked: isSelected }}
                onPress={() => {
                  onChangeCountryCode(item.value);
                  setIsCountryPickerOpen(false);
                }}
                className={`min-h-14 flex-row items-center justify-between px-4 py-3 ${
                  isSelected ? 'bg-primary-50' : 'bg-white'
                }`}
              >
                <View>
                  <HeroText
                    className={`text-[15px] font-semibold ${
                      isSelected ? 'text-primary-700' : 'text-[#1D1D1F]'
                    }`}
                  >
                    {item.caption}
                  </HeroText>
                  <HeroText className="mt-0.5 text-[12px] text-[rgba(29,29,31,0.52)]">
                    {item.value}
                  </HeroText>
                </View>
                {isSelected ? (
                  <Check size={17} color="#0071E3" strokeWidth={2.2} />
                ) : null}
              </Pressable>
            );
          })}
        </View>
      ) : null}
      {error ? (
        <HeroText
          accessibilityLiveRegion="polite"
          className="ml-1 text-xs leading-5 text-danger"
        >
          {error}
        </HeroText>
      ) : helperText ? (
        <HeroText className="ml-1 text-xs leading-5 text-muted">
          {helperText}
        </HeroText>
      ) : null}
    </View>
  );
}
