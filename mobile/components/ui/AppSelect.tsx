import React, { useState } from 'react';
import { Check, ChevronDown, ChevronUp } from 'lucide-react-native';
import { Pressable, ScrollView, View } from 'react-native';
import { HeroText, cn } from './heroui';

export interface AppSelectOption {
  id: string;
  label: string;
  description?: string;
  disabled?: boolean;
}

interface AppSelectProps {
  label: string;
  value: string | null | undefined;
  options: AppSelectOption[];
  placeholder?: string;
  helperText?: string;
  onChange: (id: string) => void;
  disabled?: boolean;
  className?: string;
}

export function AppSelect({
  label,
  value,
  options,
  placeholder = 'Select an option',
  helperText,
  onChange,
  disabled = false,
  className,
}: AppSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selectedOption = options.find((option) => option.id === value);
  const displayValue = selectedOption?.label ?? placeholder;

  return (
    <View className={cn('gap-2', className)}>
      <HeroText className="ml-1 text-sm font-semibold text-foreground">
        {label}
      </HeroText>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${label}: ${displayValue}`}
        accessibilityState={{ disabled, expanded: isOpen }}
        disabled={disabled}
        onPress={() => setIsOpen((current) => !current)}
        className={cn(
          'min-h-[52px] flex-row items-center justify-between gap-3 rounded-[10px] border px-3.5 py-2.5',
          isOpen ? 'border-primary-500 bg-primary-50/50' : 'border-field-border bg-white',
          disabled ? 'opacity-60' : undefined,
        )}
      >
        <HeroText
          className={cn(
            'min-w-0 flex-1 text-[15px] leading-5',
            selectedOption ? 'font-semibold text-neutral-900' : 'text-neutral-400',
          )}
        >
          {displayValue}
        </HeroText>
        {isOpen ? (
          <ChevronUp size={18} color="#2F64B6" strokeWidth={2.2} />
        ) : (
          <ChevronDown size={18} color="#64748B" strokeWidth={2.2} />
        )}
      </Pressable>

      {isOpen ? (
        <View className="overflow-hidden rounded-[10px] border border-[#DCE6F7] bg-white">
          <ScrollView
            className="max-h-64"
            nestedScrollEnabled
            showsVerticalScrollIndicator={false}
          >
            {options.map((option) => {
              const isSelected = option.id === value;

              return (
                <Pressable
                  key={option.id}
                  accessibilityRole="radio"
                  accessibilityLabel={option.description ? `${option.label}, ${option.description}` : option.label}
                  accessibilityState={{ checked: isSelected, disabled: option.disabled }}
                  disabled={option.disabled}
                  onPress={() => {
                    if (option.disabled) {
                      return;
                    }
                    onChange(option.id);
                    setIsOpen(false);
                  }}
                  className={cn(
                    'min-h-[52px] flex-row items-center justify-between gap-3 border-b border-[#EEF2F7] px-3.5 py-2.5 last:border-b-0',
                    isSelected ? 'bg-primary-50' : 'bg-white',
                    option.disabled ? 'opacity-50' : undefined,
                  )}
                >
                  <View className="min-w-0 flex-1">
                    <HeroText
                      className={cn(
                        'text-[14px] font-semibold leading-5',
                        isSelected ? 'text-primary-700' : 'text-neutral-900',
                      )}
                    >
                      {option.label}
                    </HeroText>
                    {option.description ? (
                      <HeroText className="mt-0.5 text-xs leading-4 text-neutral-500">
                        {option.description}
                      </HeroText>
                    ) : null}
                  </View>
                  {isSelected ? <Check size={17} color="#2F64B6" strokeWidth={2.2} /> : null}
                </Pressable>
              );
            })}
          </ScrollView>
        </View>
      ) : null}

      {helperText ? (
        <HeroText className="ml-1 text-xs leading-5 text-neutral-500">
          {helperText}
        </HeroText>
      ) : null}
    </View>
  );
}
