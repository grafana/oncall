import { SelectableValue } from '@grafana/data';

const POLICY_DURATION_LIST: SelectableValue[] = [
  {
    value: 1,
    label: '1',
  },
  {
    value: 5,
    label: '5',
  },
  {
    value: 15,
    label: '15',
  },
  {
    value: 30,
    label: '30',
  },
  {
    value: 60,
    label: '60',
  },
];

// SECONDS
export const POLICY_DURATION_LIST_SECONDS: SelectableValue[] = POLICY_DURATION_LIST.map((item: SelectableValue) => ({
  value: item.value * 60,
  label: item.label,
}));

// MINUTES
export const POLICY_DURATION_LIST_MINUTES: SelectableValue[] = [...POLICY_DURATION_LIST];

export const CUSTOM_SILENCE_VALUE = -100;

export const SILENCE_DURATION_LIST: SelectableValue[] = [
  { value: CUSTOM_SILENCE_VALUE, label: 'Custom' },
  { value: 30 * 60, label: '30 minutes' },
  { value: 1 * 60 * 60, label: '1 hour' },
  { value: 2 * 60 * 60, label: '2 hours' },
  { value: 6 * 60 * 60, label: '6 hours' },
  { value: 12 * 60 * 60, label: '12 hours' },
  { value: 24 * 60 * 60, label: '24 hours' },
  { value: -1, label: 'Forever' },
];
