import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { KeyValuePair } from 'utils';

export const WebhookTriggerType = {
  EscalationStep: new KeyValuePair('0', 'Escalation Step'),
  Firing: new KeyValuePair('1', 'Firing'),
  Acknowledged: new KeyValuePair('2', 'Acknowledged'),
  Resolved: new KeyValuePair('3', 'Resolved'),
  Silenced: new KeyValuePair('4', 'Silenced'),
  Unsilenced: new KeyValuePair('5', 'Unsilenced'),
  Unresolved: new KeyValuePair('6', 'Unresolved'),
};

export const form: { name: string; fields: FormItem[] } = {
  name: 'OutgoingWebhook2',
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
      description: 'Controls if this webhook will execute when the event is triggered',
    },
    {
      name: 'team',
      label: 'Assign to Team',
      description:
        'Assigning to the teams allows you to filter Outgoing Webhooks and configure their visibility. Go to OnCall -> Settings -> Team and Access Settings for more details',
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
      type: FormItemType.Select,
      extra: {
        options: [
          {
            value: WebhookTriggerType.EscalationStep.key,
            label: WebhookTriggerType.EscalationStep.value,
          },
          {
            value: WebhookTriggerType.Firing.key,
            label: WebhookTriggerType.Firing.value,
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
    /*
     * TODO: Uncomment once backend implements it too
    {
      name: 'alert_receive_channel_id',
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
    },
    */
    {
      name: 'url',
      label: 'Webhook URL',
      type: FormItemType.Input,
      validation: { required: true },
    },
    {
      name: 'headers',
      label: 'Webhook Headers',
      type: FormItemType.TextArea,
      extra: {
        rows: 5,
      },
    },
    {
      name: 'username',
      type: FormItemType.Input,
    },
    {
      name: 'password',
      type: FormItemType.Input,
    },
    {
      name: 'authorization_header',
      type: FormItemType.Input,
    },
    {
      name: 'trigger_template',
      type: FormItemType.TextArea,
      description: 'Trigger template must be empty or evaluate to true or 1 for webhook to be sent',
      extra: {
        rows: 2,
      },
    },
    {
      name: 'data',
      getDisabled: (form_data) => Boolean(form_data?.forward_whole_payload),
      type: FormItemType.TextArea,
      description: 'Available variables: {{ alert_payload }}, {{ alert_group_id }}',
      extra: {
        rows: 9,
      },
    },
    {
      name: 'forward_all',
      normalize: (value) => Boolean(value),
      type: FormItemType.Switch,
      description: "Forwards whole payload of the alert to the webhook's url as POST data",
    },
  ],
};
