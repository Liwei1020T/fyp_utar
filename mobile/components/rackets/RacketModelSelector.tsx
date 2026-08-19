import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { backendApi, BackendApiError } from '../../services/backendApi';
import type { BackendRacketModelOption } from '../../types/backend';
import { AppButton } from '../ui/AppButton';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';

interface RacketModelSelectorProps {
  token: string | null;
  selectedKey: string | null;
  onSelect: (option: BackendRacketModelOption | null) => void;
}

export function RacketModelSelector({
  token,
  selectedKey,
  onSelect,
}: RacketModelSelectorProps) {
  const [options, setOptions] = useState<BackendRacketModelOption[]>([]);
  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadCount, setReloadCount] = useState(0);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    let active = true;
    setIsLoading(true);
    setLoadError(null);
    void backendApi
      .listRacketModels(token)
      .then((items) => {
        if (active) {
          setOptions(items);
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setLoadError(
            error instanceof BackendApiError
              ? error.message
              : 'Failed to load standard racket models.',
          );
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [reloadCount, token]);

  return (
    <View className="mb-4 gap-3">
      <HeroText className="text-sm font-semibold text-neutral-800">
        Standard model
      </HeroText>
      {isLoading ? (
        <HeroText className="text-sm text-neutral-500">
          Loading standard models...
        </HeroText>
      ) : null}
      {loadError ? (
        <View className="gap-2 rounded-[16px] border border-red-100 bg-red-50 px-3 py-3">
          <HeroText className="text-sm font-medium text-red-600">
            {loadError}
          </HeroText>
          <AppButton
            label="Retry model list"
            variant="outline"
            size="sm"
            onPress={() => setReloadCount((count) => count + 1)}
          />
        </View>
      ) : null}
      <View className="flex-row flex-wrap gap-2">
        {options.map((option) => {
          const isSelected = selectedKey === option.key;
          return (
            <AppChip
              key={option.key}
              label={`${option.brand} ${option.model}`}
              variant={isSelected ? 'primary' : 'neutral'}
              accessibilityState={{ selected: isSelected }}
              onPress={() => onSelect(option)}
              size="md"
            />
          );
        })}
        <AppChip
          label="Other model"
          variant={selectedKey === null ? 'primary' : 'neutral'}
          accessibilityState={{ selected: selectedKey === null }}
          onPress={() => onSelect(null)}
          size="md"
        />
      </View>
      <HeroText className="text-xs leading-5 text-neutral-500">
        Standard models use an exact shared CF identity. Other models use global
        community evidence without cross-model guessing.
      </HeroText>
    </View>
  );
}
