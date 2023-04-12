import { FormItem, FormItemType } from 'components/GForm/GForm.types';

export const form: { name: string; fields: FormItem[] } = {
  name: 'Integration',
  fields: [
    {
      name: 'verbal_name',
      type: FormItemType.Input,
      validation: { required: true },
    },
    {
      name: 'description',
      type: FormItemType.TextArea,
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
  ],
};
