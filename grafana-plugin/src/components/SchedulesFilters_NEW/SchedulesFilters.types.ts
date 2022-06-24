import { Moment } from 'moment';

enum ScheduleType {
  Web = 'Web',
  iCal = 'iCal',
  API = 'API',
}

export interface SchedulesFiltersType {
  searchTerm: string;
  type: string;
  status: string;
}
