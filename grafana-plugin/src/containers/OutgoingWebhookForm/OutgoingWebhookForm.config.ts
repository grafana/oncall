import { FormItem, FormItemType } from 'components/GForm/GForm.types';

export const form: { name: string; fields: FormItem[] } = {
  name: 'OutgoingWebhook',
  fields: [
    {
      name: 'name',
      type: FormItemType.Input,
      validation: { required: true },
    },
    {
      name: 'trigger_type',
      label: 'Trigger type',
      type: FormItemType.Select,
      extra: {
        options: [
          {
            value: 0,
            label: 'Escalation step',
          },
          {
            value: 1,
            label: 'User notification',
          },
          {
            value: 2,
            label: 'Triggered',
          },
          {
            value: 3,
            label: 'Acknowledged',
          },
          {
            value: 4,
            label: 'Resolved',
          },
          {
            value: 5,
            label: 'Silenced',
          },
          {
            value: 6,
            label: 'Unsilenced',
          },
          {
            value: 7,
            label: 'Unresolved',
          },
          {
            value: 8,
            label: 'Schedule shift change',
          },
        ],
      },
    },
    {
      name: 'http_method',
      label: 'HTTP method',
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
    },
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
