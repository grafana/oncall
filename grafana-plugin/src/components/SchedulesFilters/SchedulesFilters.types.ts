import { ScheduleType } from 'models/schedule/schedule.types';

export interface SchedulesFiltersType {
  searchTerm: string;
  type: ScheduleType;
  status: string;
}
