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
];

// SECONDS
export const POLICY_DURATION_LIST_SECONDS: SelectableValue[] = POLICY_DURATION_LIST.map((item: SelectableValue) => ({
  value: item.value * 60,
  label: item.label,
}));

// MINUTES
export const POLICY_DURATION_LIST_MINUTES: SelectableValue[] = [...POLICY_DURATION_LIST];
