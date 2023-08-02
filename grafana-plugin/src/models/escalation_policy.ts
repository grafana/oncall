import { Channel } from 'models/channel';
import { Schedule } from 'models/schedule/schedule.types';
import { UserGroup } from 'models/user_group/user_group.types';

import { ChannelFilter } from './channel_filter';
import { ScheduleDTO } from './schedule';
import { UserDTO as User } from './user';

export interface EscalationPolicyType {
  id: string;
  notify_to_user: User['pk'] | null;
  //  it's option value from api/internal/v1/escalation_policies/escalation_options/
  step: number;
  wait_delay: string | null;
  is_final: boolean;
  channel_filter: ChannelFilter['id'];
  notify_to_users_queue: Array<User['pk']>;
  from_time: string | null;
  to_time: string | null;
  notify_to_schedule: ScheduleDTO['id'] | null;
  notify_to_channel: Channel['id'] | null;
  notify_to_group: UserGroup['id'];
  notify_schedule: Schedule['id'];
}

export function prepareEscalationPolicy(value: EscalationPolicyType): EscalationPolicyType {
  return {
    ...value,
    notify_to_user: null,
    wait_delay: null,
    notify_to_users_queue: [],
    from_time: null,
    to_time: null,
    notify_to_schedule: null,
  };
}
