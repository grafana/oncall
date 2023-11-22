import React from 'react';

import { SelectableValue } from '@grafana/data';
import Emoji from 'react-emoji-render';

import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { OutgoingWebhookPreset } from 'models/outgoing_webhook/outgoing_webhook.types';
import { KeyValuePair } from 'utils';
import { generateAssignToTeamInputDescription } from 'utils/consts';

import { WebhookFormFieldName } from './OutgoingWebhookForm.types';

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

export function createForm(
  presets: OutgoingWebhookPreset[],
  hasLabelsFeature?: boolean
): {
  name: string;
  fields: FormItem[];
} {
  return {
    name: 'OutgoingWebhook',
    fields: [
      {
        name: WebhookFormFieldName.Name,
        type: FormItemType.Input,
        validation: { required: true },
      },
      {
        name: WebhookFormFieldName.IsWebhookEnabled,
        label: 'Enabled',
        normalize: (value) => Boolean(value),
        type: FormItemType.Switch,
      },
      {
        name: WebhookFormFieldName.Team,
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
          placeholder: 'Choose (Optional)',
        },
      },
      {
        name: WebhookFormFieldName.TriggerType,
        label: 'Trigger Type',
        description: 'The type of event which will cause this webhook to execute.',
        type: FormItemType.Select,
        extra: {
          placeholder: 'Choose (Required)',
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
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.TriggerType),
        normalize: (value) => value,
      },
      {
        name: WebhookFormFieldName.HttpMethod,
        label: 'HTTP Method',
        type: FormItemType.Select,
        extra: {
          placeholder: 'Choose (Required)',
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
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.HttpMethod),
        normalize: (value) => value,
      },
      {
        name: WebhookFormFieldName.IntegrationFilter,
        label: 'Integrations',
        type: FormItemType.MultiSelect,
        isVisible: (data) =>
          isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.IntegrationFilter) &&
          data.trigger_type !== WebhookTriggerType.EscalationStep.key,
        extra: {
          placeholder: 'Choose (Optional)',
          modelName: 'alertReceiveChannelStore',
          displayField: 'verbal_name',
          valueField: 'id',
          showSearch: true,
          getOptionLabel: (item: SelectableValue) => <Emoji text={item?.label || ''} />,
        },
        description:
          'Integrations that this webhook applies to. If this is empty the webhook will execute for all integrations',
      },
      {
        name: WebhookFormFieldName.Labels,
        label: 'Labels',
        type: FormItemType.Other,
        render: true,
      },
      {
        name: WebhookFormFieldName.Url,
        label: 'Webhook URL',
        type: FormItemType.Monaco,
        extra: {
          height: 30,
        },
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.Url),
      },
      {
        name: WebhookFormFieldName.Headers,
        label: 'Webhook Headers',
        description: 'Request headers should be in JSON format.',
        type: FormItemType.Monaco,
        extra: {
          rows: 3,
        },
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.Headers),
      },
      {
        name: WebhookFormFieldName.Username,
        type: FormItemType.Input,
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.Username),
      },
      {
        name: WebhookFormFieldName.Password,
        type: FormItemType.Password,
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.Password),
      },
      {
        name: WebhookFormFieldName.AuthorizationHeader,
        description:
          'Value of the Authorization header, do not need to prefix with "Authorization:". For example: Bearer AbCdEf123456',
        type: FormItemType.Password,
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.AuthorizationHeader),
      },
      {
        name: WebhookFormFieldName.TriggerTemplate,
        type: FormItemType.Monaco,
        description:
          'Trigger template is used to conditionally execute the webhook based on incoming data. The trigger template must be empty or evaluate to true or 1 for the webhook to be sent',
        extra: {
          rows: 2,
        },
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.TriggerTemplate),
      },
      {
        name: WebhookFormFieldName.ForwardAll,
        normalize: (value) => (value ? Boolean(value) : value),
        type: FormItemType.Switch,
        description: "Forwards whole payload of the alert group and context data to the webhook's url as POST/PUT data",
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.ForwardAll),
      },
      {
        name: WebhookFormFieldName.Data,
        getDisabled: (data) => Boolean(data?.forward_all),
        type: FormItemType.Monaco,
        description: `Available variables: {{ event }}, {{ user }}, {{ alert_group }}, {{ alert_group_id }}, {{ alert_payload }}, {{ integration }}, {{ notified_users }}, {{ users_to_be_notified }}, {{ responses }}${
          hasLabelsFeature ? ' {{ webhook }}' : ''
        }`,
        extra: {},
        isVisible: (data) => isPresetFieldVisible(data.preset, presets, WebhookFormFieldName.Data),
      },
    ],
  };
}

function isPresetFieldVisible(presetId: string, presets: OutgoingWebhookPreset[], fieldName: WebhookFormFieldName) {
  if (presetId == null) {
    return true;
  }
  const selectedPreset = presets.find((item) => item.id === presetId);
  if (selectedPreset && selectedPreset.controlled_fields.includes(fieldName)) {
    return false;
  }
  return true;
}
