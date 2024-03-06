import { ApiSchemas } from 'network/oncall-api/api.types';

export interface ScheduleFiltersType {
  users: Array<ApiSchemas['User']['pk']>;
}
