import { Channel } from 'models/channel';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { Schedule } from 'models/schedule/schedule.types';
import { User } from 'models/user/user.types';
import { UserGroup } from 'models/user_group/user_group.types';

export interface EscalationPolicy {
  id: string;
  notify_to_user: User['pk'] | null;
  //  it's option value from api/internal/v1/escalation_policies/escalation_options/
  step: EscalationPolicyOption['value'];
  wait_delay: string | null;
  is_final: boolean;
  escalation_chain: EscalationChain['id'];
  notify_to_users_queue: Array<User['pk']>;
  from_time: string | null;
  to_time: string | null;
  notify_to_channel: Channel['id'] | null;
  custom_webhook: OutgoingWebhook['id'] | null;
  notify_to_group: UserGroup['id'] | null;
  notify_schedule: Schedule['id'] | null;
  important: boolean | null;
  num_alerts_in_window: number;
  num_minutes_in_window: number;
}

export interface EscalationPolicyOption {
  can_change_importance: boolean;
  display_name: string;
  create_display_name: string;
  slack_integration_required: boolean;
  value: number;
}
