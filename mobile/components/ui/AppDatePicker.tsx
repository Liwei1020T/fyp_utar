import React, { type CSSProperties } from 'react';
import {
  Modal,
  Platform,
  Pressable,
  View,
} from 'react-native';
import DateTimePicker, {
  type DateTimePickerEvent,
} from '@react-native-community/datetimepicker';
import { CalendarDays } from 'lucide-react-native';
import { AppButton } from './AppButton';
import { AppInput } from './AppInput';
import { HeroText } from './heroui';
import { appChromeColors } from './theme';

interface AppDatePickerProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  minimumDate?: Date;
  maximumDate?: Date;
  isDisabled?: boolean;
}

function pad(value: number) {
  return String(value).padStart(2, '0');
}

function formatDateValue(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function parseDateValue(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return new Date();
  }

  const date = new Date(
    Number(match[1]),
    Number(match[2]) - 1,
    Number(match[3]),
  );
  return date.getFullYear() === Number(match[1]) &&
    date.getMonth() === Number(match[2]) - 1 &&
    date.getDate() === Number(match[3])
    ? date
    : new Date();
}

const webInputStyle: CSSProperties = {
  boxSizing: 'border-box',
  width: '100%',
  height: 52,
  border: `1px solid ${appChromeColors.border}`,
  borderRadius: 10,
  backgroundColor: appChromeColors.surfaceMuted,
  color: appChromeColors.textPrimary,
  fontFamily: 'inherit',
  fontSize: 16,
  padding: '0 16px',
  outline: 'none',
};

export function AppDatePicker({
  label,
  value,
  onChange,
  placeholder = 'YYYY-MM-DD',
  minimumDate,
  maximumDate,
  isDisabled = false,
}: AppDatePickerProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [draftDate, setDraftDate] = React.useState(() => parseDateValue(value));

  const openPicker = () => {
    if (isDisabled) {
      return;
    }
    setDraftDate(parseDateValue(value));
    setIsOpen(true);
  };

  const handleNativeChange = (event: DateTimePickerEvent, date?: Date) => {
    if (event.type === 'dismissed') {
      setIsOpen(false);
      return;
    }
    if (!date) {
      return;
    }

    setDraftDate(date);
    if (Platform.OS === 'android') {
      onChange(formatDateValue(date));
      setIsOpen(false);
    }
  };

  const commitIOSDate = () => {
    onChange(formatDateValue(draftDate));
    setIsOpen(false);
  };

  if (Platform.OS === 'web') {
    return (
      <View className="mb-4">
        <HeroText className="mb-2 ml-1 text-sm font-semibold text-foreground">
          {label}
        </HeroText>
        {React.createElement('input', {
          type: 'date',
          value,
          min: minimumDate ? formatDateValue(minimumDate) : undefined,
          max: maximumDate ? formatDateValue(maximumDate) : undefined,
          onChange: (event: { target: { value: string } }) =>
            onChange(event.target.value),
          'aria-label': label,
          'aria-valuetext': value || placeholder,
          disabled: isDisabled,
          style: webInputStyle,
        })}
      </View>
    );
  }

  return (
    <>
      <Pressable
        onPress={openPicker}
        disabled={isDisabled}
        accessibilityRole="button"
        accessibilityLabel={label}
        accessibilityHint="Open date picker"
        accessibilityValue={{ text: value || placeholder }}
        accessibilityState={{ disabled: isDisabled }}
      >
        <View pointerEvents="none">
          <AppInput
            label={label}
            value={value}
            placeholder={placeholder}
            editable={false}
            isDisabled={isDisabled}
            rightAdornment={
              <CalendarDays size={18} color={appChromeColors.textSecondary} />
            }
          />
        </View>
      </Pressable>

      {isOpen && Platform.OS === 'ios' ? (
        <Modal
          visible
          transparent
          animationType="slide"
          onRequestClose={() => setIsOpen(false)}
        >
          <View className="flex-1 justify-end bg-black/30">
            <View className="rounded-t-[24px] bg-white px-4 pb-8 pt-4">
              <View className="flex-row items-center justify-between">
                <AppButton
                  label="Cancel"
                  variant="ghost"
                  size="sm"
                  onPress={() => setIsOpen(false)}
                />
                <HeroText className="text-base font-semibold text-foreground">
                  Choose date
                </HeroText>
                <AppButton
                  label="Done"
                  variant="ghost"
                  size="sm"
                  onPress={commitIOSDate}
                />
              </View>
              <DateTimePicker
                value={draftDate}
                mode="date"
                display="inline"
                minimumDate={minimumDate}
                maximumDate={maximumDate}
                onChange={handleNativeChange}
                accentColor={appChromeColors.primary}
                style={{ alignSelf: 'center' }}
              />
            </View>
          </View>
        </Modal>
      ) : null}

      {isOpen && Platform.OS === 'android' ? (
        <DateTimePicker
          value={draftDate}
          mode="date"
          display="calendar"
          minimumDate={minimumDate}
          maximumDate={maximumDate}
          onChange={handleNativeChange}
        />
      ) : null}
    </>
  );
}
