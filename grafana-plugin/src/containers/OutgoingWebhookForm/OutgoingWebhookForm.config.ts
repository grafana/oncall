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
      name: 'team',
      label: 'Assign to team',
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
      name: 'webhook',
      label: 'Webhook URL',
      type: FormItemType.Input,
      validation: { required: true },
    },
    {
      name: 'user',
      type: FormItemType.Input,
    },
    {
      name: 'password',
      type: FormItemType.Input,
    },
    {
      name: 'authorization_header',
      type: FormItemType.TextArea,
      extra: {
        rows: 5,
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
      name: 'forward_whole_payload',
      normalize: (value) => Boolean(value),
      type: FormItemType.Switch,
      description: "Forwards whole payload of the alert to the webhook's url as POST data",
    },
  ],
};
