import React from 'react';

import { Icon } from '@grafana/ui';

import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Channel } from 'models/channel';
import { User } from 'models/user/user.types';

export enum IncidentStatus {
  'New',
  'Acknowledged',
  'Resolved',
  'Silenced',
}

export enum AlertAction {
  Acknowledge = 'acknowledge',
  unAcknowledge = 'unacknowledge',
  Resolve = 'resolve',
  unResolve = 'unresolve',
  Silence = 'silence',
  unSilence = 'unsilence',
}

export enum TimeLineRealm {
  UserNotification = 'user_notification',
  AlertGroup = 'alert_group',
  ResolutionNote = 'resolution_note',
}

export interface TimeLineItem {
  action: string;
  author: User | null;
  created_at: string;
  realm: TimeLineRealm;
  time: string;
  type: number;
}

export interface GroupedAlert {
  created_at: string;
  id: string;
  render_for_web: RenderForWeb;
}

export interface Alert {
  pk: string;
  title: string;
  message: string;
  image_url: string;
  alerts?: GroupedAlert[];
  acknowledged: boolean;
  created_at: string;
  acknowledged_at: string;
  acknowledged_by_user: User;
  acknowledged_on_source: boolean;
  channel: Channel;
  permalink?: string;
  related_users: User[];
  render_after_resolve_report_json?: TimeLineItem[];
  render_for_slack: { attachments: any[] };
  render_for_web: RenderForWeb;
  alerts_count: number;
  inside_organization_number: number;
  resolved: boolean;
  resolved_at: string;
  resolved_by: number;
  resolved_by_user: User;
  silenced: boolean;
  silenced_at: string;
  silenced_by_user: Partial<User>;
  silenced_until: string;
  started_at: string;
  last_alert_at: string;
  verbose_name: string;
  dependent_alert_groups: Alert[];
  status: IncidentStatus;
  short?: boolean;
  root_alert_group?: Alert;
  alert_receive_channel: Partial<AlertReceiveChannel>;

  // set by client
  loading?: boolean;
  undoAction?: AlertAction;

  has_pormortem?: boolean; // not implemented yet
}

interface RenderForWeb {
  message: any;
  title: any;
  image_url: string;
}
