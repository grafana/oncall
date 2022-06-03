export interface ScheduleDTO {
  id: string;
  name: string;
  ical_url_primary: string;
  ical_url_overrides: string;
  type: ScheduleType;
  channel_name: string;
  channel: string;
}

export enum ScheduleType {
  CalendarSchedule,
  IcalSchedule,
}
