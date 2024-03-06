import { Channel } from 'models/channel/channel';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Schedule } from 'models/schedule/schedule.types';
import { UserGroup } from 'models/user_group/user_group.types';
import { ApiSchemas } from 'network/oncall-api/api.types';

export interface EscalationPolicy {
  id: string;
  notify_to_user: ApiSchemas['User']['pk'] | null;
  //  it's option value from api/internal/v1/escalation_policies/escalation_options/
  step: EscalationPolicyOption['value'];
  wait_delay: string | null;
  is_final: boolean;
  escalation_chain: EscalationChain['id'];
  notify_to_users_queue: Array<ApiSchemas['User']['pk']>;
  from_time: string | null;
  to_time: string | null;
  notify_to_channel: Channel['id'] | null;
  custom_webhook: ApiSchemas['Webhook']['id'] | null;
  notify_to_group: UserGroup['id'] | null;
  notify_to_team_members: GrafanaTeam['id'] | null;
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
