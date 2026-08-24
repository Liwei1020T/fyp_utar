import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { backendApi, BackendApiError } from '../../services/backendApi';
import type { BackendRacketModelOption } from '../../types/backend';
import { AppButton } from '../ui/AppButton';
import { AppSelect } from '../ui/AppSelect';
import { HeroText } from '../ui/heroui';

const OTHER_MODEL_OPTION_ID = '__other_racket_model__';

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
      {!isLoading ? (
        <AppSelect
          label="Standard model"
          value={selectedKey ?? OTHER_MODEL_OPTION_ID}
          placeholder="Choose a standard model"
          options={[
            ...options.map((option) => ({
              id: option.key,
              label: `${option.brand} ${option.model}`,
            })),
            {
              id: OTHER_MODEL_OPTION_ID,
              label: 'Other model',
              description: 'Enter the brand and model manually.',
            },
          ]}
          onChange={(id) => {
            const selectedOption = options.find((option) => option.key === id);
            onSelect(selectedOption ?? null);
          }}
          helperText="Standard models use exact shared racket evidence. Other models use global community evidence."
        />
      ) : null}
    </View>
  );
}
