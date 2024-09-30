export const default_working_hours: DefaultWorkingHours = {
  friday: [{ end: '17:00:00', start: '09:00:00' }],
  monday: [{ end: '17:00:00', start: '09:00:00' }],
  sunday: [],
  tuesday: [{ end: '17:00:00', start: '09:00:00' }],
  saturday: [],
  thursday: [{ end: '17:00:00', start: '09:00:00' }],
  wednesday: [{ end: '17:00:00', start: '09:00:00' }],
};

export interface DefaultWorkingHours {
  friday: DefaultWorkingHourType[];
  monday: DefaultWorkingHourType[];
  sunday: DefaultWorkingHourType[];
  tuesday: DefaultWorkingHourType[];
  saturday: DefaultWorkingHourType[];
  thursday: DefaultWorkingHourType[];
  wednesday: DefaultWorkingHourType[];
}

interface DefaultWorkingHourType {
  end: string;
  start: string;
}
