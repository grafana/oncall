export interface RotationCreateData {}

export interface RotationData {}

export enum RepeatEveryPeriod {
  'DAYS' = 0,
  'WEEKS' = 1,
  'MONTHS' = 2,
  'HOURS' = 3,
  'MINUTES' = 4,
}

export type PeriodUnitName = 'minutes' | 'hours' | 'days' | 'weeks' | 'months';
