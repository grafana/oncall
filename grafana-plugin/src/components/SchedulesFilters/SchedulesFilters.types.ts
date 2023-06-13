import { ScheduleType } from 'models/schedule/schedule.types';

export interface SchedulesFiltersType {
  searchTerm: string;
  type: ScheduleType;
  used: boolean | undefined;
  mine: boolean | undefined;
}
