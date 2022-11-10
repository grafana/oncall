import { NULL_VALUE } from './LiveSettings.config';

export function normalizeValue(value: string) {
  if (value === null) {
    return NULL_VALUE;
  }

  return String(value);
}

export function prepareForUpdate(value: string | boolean) {
  if (value === '') {
    return null;
  }

  return value;
}
