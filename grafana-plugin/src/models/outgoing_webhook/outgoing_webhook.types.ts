import { KeyValuePair } from 'utils/utils';

export interface OutgoingWebhookResponse {
  timestamp: string;
  url: string;
  request_trigger: string;
  request_headers: string;
  request_data: string;
  status_code: string;
  content: string;
  event_data: string;
}

export interface OutgoingWebhookPreset {
  id: string;
  name: string;
  description: string;
  logo: string;
  controlled_fields: string[];
}

export const WebhookTriggerType = {
  EscalationStep: new KeyValuePair('0', 'Escalation Step'),
  AlertGroupCreated: new KeyValuePair('1', 'Alert Group Created'),
  Acknowledged: new KeyValuePair('2', 'Acknowledged'),
  Resolved: new KeyValuePair('3', 'Resolved'),
  Silenced: new KeyValuePair('4', 'Silenced'),
  Unsilenced: new KeyValuePair('5', 'Unsilenced'),
  Unresolved: new KeyValuePair('6', 'Unresolved'),
  Unacknowledged: new KeyValuePair('7', 'Unacknowledged'),
  AlertGroupStatusChange: new KeyValuePair('8', 'Alert Group Status Change'),
};

export const WEBHOOK_TRIGGGER_TYPE_OPTIONS = [
  {
    value: WebhookTriggerType.EscalationStep.key,
    label: WebhookTriggerType.EscalationStep.value,
  },
  {
    value: WebhookTriggerType.AlertGroupCreated.key,
    label: WebhookTriggerType.AlertGroupCreated.value,
  },
  {
    value: WebhookTriggerType.AlertGroupStatusChange.key,
    label: WebhookTriggerType.AlertGroupStatusChange.value,
  },
  {
    value: WebhookTriggerType.Acknowledged.key,
    label: WebhookTriggerType.Acknowledged.value,
  },
  {
    value: WebhookTriggerType.Resolved.key,
    label: WebhookTriggerType.Resolved.value,
  },
  {
    value: WebhookTriggerType.Silenced.key,
    label: WebhookTriggerType.Silenced.value,
  },
  {
    value: WebhookTriggerType.Unsilenced.key,
    label: WebhookTriggerType.Unsilenced.value,
  },
  {
    value: WebhookTriggerType.Unresolved.key,
    label: WebhookTriggerType.Unresolved.value,
  },
  {
    value: WebhookTriggerType.Unacknowledged.key,
    label: WebhookTriggerType.Unacknowledged.value,
  },
];

export const HTTP_METHOD_OPTIONS = [
  {
    value: 'GET',
    label: 'GET',
  },
  {
    value: 'POST',
    label: 'POST',
  },
  {
    value: 'PUT',
    label: 'PUT',
  },
  {
    value: 'PATCH',
    label: 'PATCH',
  },
  {
    value: 'DELETE',
    label: 'DELETE',
  },
  {
    value: 'OPTIONS',
    label: 'OPTIONS',
  },
];
