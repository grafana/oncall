import { FormItem, FormItemType } from 'components/GForm/GForm.types';

export const form: { name: string; fields: FormItem[] } = {
  name: 'Integration',
  fields: [
    {
      label: 'Name',
      name: 'verbal_name',
      type: FormItemType.Input,
      placeholder: 'Integration Name',
      validation: { required: true },
    },
    {
      label: 'Description',
      name: 'description_short',
      type: FormItemType.TextArea,
      placeholder: 'Integration Description',
    },
    {
      name: 'team',
      label: 'Assign to team',
      description:
        'Assigning to the teams allows you to filter Integrations and configure their visibility. Go to OnCall -> Settings -> Team and Access Settings for more details',
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
      name: 'alert_manager',
      type: FormItemType.Other,
    },
    {
      name: 'contact_point',
      type: FormItemType.Other,
    },
    {
      name: 'is_existing',
      type: FormItemType.Other,
    },
    {
      name: 'alerting',
      type: FormItemType.Other,
      render: true,
    },
  ],
};
