import { NULL_VALUE } from './LiveSettings.config';

export const normalizeValue = (value: string): string => (value === null ? NULL_VALUE : String(value));

export const prepareForUpdate = (value: string | boolean): string | boolean => (value === '' ? null : value);
