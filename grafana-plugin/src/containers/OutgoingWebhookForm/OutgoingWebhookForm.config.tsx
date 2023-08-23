import React from 'react';

import { SelectableValue } from '@grafana/data';
import Emoji from 'react-emoji-render';

import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { KeyValuePair } from 'utils';
import { generateAssignToTeamInputDescription } from 'utils/consts';

export const WebhookTriggerType = {
  EscalationStep: new KeyValuePair('0', 'Escalation Step'),
  AlertGroupCreated: new KeyValuePair('1', 'Alert Group Created'),
  Acknowledged: new KeyValuePair('2', 'Acknowledged'),
  Resolved: new KeyValuePair('3', 'Resolved'),
  Silenced: new KeyValuePair('4', 'Silenced'),
  Unsilenced: new KeyValuePair('5', 'Unsilenced'),
  Unresolved: new KeyValuePair('6', 'Unresolved'),
  Unacknowledged: new KeyValuePair('7', 'Unacknowledged'),
};

export const form: { name: string; fields: FormItem[] } = {
  name: 'OutgoingWebhook',
  fields: [
    {
      name: 'name',
      type: FormItemType.Input,
      validation: { required: true },
    },
    {
      name: 'is_webhook_enabled',
      label: 'Enabled',
      normalize: (value) => Boolean(value),
      type: FormItemType.Switch,
    },
    {
      name: 'team',
      label: 'Assign to Team',
      description: `${generateAssignToTeamInputDescription(
        'Outgoing Webhooks'
      )} This setting does not effect execution of the webhook.`,
      type: FormItemType.GSelect,
      extra: {
        modelName: 'grafanaTeamStore',
        displayField: 'name',
        valueField: 'id',
        showSearch: true,
        allowClear: true,
      },
    },
    {
      name: 'trigger_type',
      label: 'Trigger Type',
      description: 'The type of event which will cause this webhook to execute.',
      type: FormItemType.Select,
      extra: {
        options: [
          {
            value: WebhookTriggerType.EscalationStep.key,
            label: WebhookTriggerType.EscalationStep.value,
          },
          {
            value: WebhookTriggerType.AlertGroupCreated.key,
            label: WebhookTriggerType.AlertGroupCreated.value,
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
        ],
      },
      validation: { required: true },
      normalize: (value) => value,
    },
    {
      name: 'http_method',
      label: 'HTTP Method',
      type: FormItemType.Select,
      extra: {
        options: [
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
            value: 'DELETE',
            label: 'DELETE',
          },
          {
            value: 'OPTIONS',
            label: 'OPTIONS',
          },
        ],
      },
      validation: { required: true },
      normalize: (value) => value,
    },
    {
      name: 'integration_filter',
      label: 'Integrations',
      type: FormItemType.MultiSelect,
      isVisible: (data) => {
        return data.trigger_type !== WebhookTriggerType.EscalationStep.key;
      },
      extra: {
        modelName: 'alertReceiveChannelStore',
        displayField: 'verbal_name',
        valueField: 'id',
        showSearch: true,
        getOptionLabel: (item: SelectableValue) => <Emoji text={item?.label || ''} />,
      },
      validation: { required: true },
      description:
        'Integrations that this webhook applies to. If this is empty the webhook will execute for all integrations',
    },
    {
      name: 'url',
      label: 'Webhook URL',
      type: FormItemType.Monaco,
      validation: { required: true },
      extra: {
        height: 30,
      },
    },
    {
      name: 'headers',
      label: 'Webhook Headers',
      description: 'Request headers should be in JSON format.',
      type: FormItemType.Monaco,
      extra: {
        rows: 3,
      },
    },
    {
      name: 'username',
      type: FormItemType.Input,
    },
    {
      name: 'password',
      type: FormItemType.Password,
    },
    {
      name: 'authorization_header',
      description:
        'Value of the Authorization header, do not need to prefix with "Authorization:". For example: Bearer AbCdEf123456',
      type: FormItemType.Password,
    },
    {
      name: 'trigger_template',
      type: FormItemType.Monaco,
      description:
        'Trigger template is used to conditionally execute the webhook based on incoming data. The trigger template must be empty or evaluate to true or 1 for the webhook to be sent',
      extra: {
        rows: 2,
      },
    },
    {
      name: 'forward_all',
      normalize: (value) => Boolean(value),
      type: FormItemType.Switch,
      description: "Forwards whole payload of the alert group and context data to the webhook's url as POST/PUT data",
    },
    {
      name: 'data',
      getDisabled: (data) => Boolean(data?.forward_all),
      type: FormItemType.Monaco,
      description:
        'Available variables: {{ event }}, {{ user }}, {{ alert_group }}, {{ alert_group_id }}, {{ alert_payload }}, {{ integration }}, {{ notified_users }}, {{ users_to_be_notified }}, {{ responses }}',
      extra: {},
    },
  ],
};
