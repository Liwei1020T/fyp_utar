import type { AppSelectOption } from '../ui/AppSelect';

export const RACKET_SPEC_NONE = '__not_specified__';

export const racketWeightClassOptions: AppSelectOption[] = [
  { id: '2U', label: '2U' },
  { id: '3U', label: '3U' },
  { id: '4U', label: '4U' },
  { id: '5U', label: '5U' },
  { id: '6U', label: '6U' },
  { id: 'F', label: 'F' },
  { id: RACKET_SPEC_NONE, label: 'Not specified' },
];

export const racketBalancePointOptions: AppSelectOption[] = [
  { id: 'Head heavy', label: 'Head heavy' },
  { id: 'Even balance', label: 'Even balance' },
  { id: 'Head light', label: 'Head light' },
  { id: RACKET_SPEC_NONE, label: 'Not specified' },
];

export const racketGripSizeOptions: AppSelectOption[] = [
  { id: 'G2', label: 'G2' },
  { id: 'G3', label: 'G3' },
  { id: 'G4', label: 'G4' },
  { id: 'G5', label: 'G5' },
  { id: 'G6', label: 'G6' },
  { id: RACKET_SPEC_NONE, label: 'Not specified' },
];

export function toRacketSpecValue(id: string) {
  return id === RACKET_SPEC_NONE ? '' : id;
}
