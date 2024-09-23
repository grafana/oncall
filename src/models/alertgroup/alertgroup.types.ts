import { ApiSchemas } from 'network/oncall-api/api.types';

export enum IncidentStatus {
  'Firing',
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
  author: ApiSchemas['User'] | null;
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

export interface AlertGroupColumn {
  id: string;
  name: string;
  isVisible: boolean;
  type?: AlertGroupColumnType;
}

export enum AlertGroupColumnType {
  DEFAULT = 'default',
  LABEL = 'label',
}

interface RenderForWeb {
  message: any;
  title: any;
  image_url: string;
  source_link: string;
}
