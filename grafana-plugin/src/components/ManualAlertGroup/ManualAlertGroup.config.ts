import { FormItem, FormItemType } from 'components/GForm/GForm.types';

export const manualAlertFormConfig: { name: string; fields: FormItem[] } = {
  name: 'Manual Alert Group',
  fields: [
    {
      name: 'title',
      type: FormItemType.Input,
      label: 'Title',
      validation: { required: true },
    },
    {
      name: 'message',
      type: FormItemType.TextArea,
      label: 'Description',
      validation: { required: true },
    },
    {
      name: 'team',
      label: 'Assign to team',
      description:
        'Assigning to the teams allows you to filter Alert Groups and configure their visibility. Go to OnCall -> Settings -> Team and Access Settings for more details',
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
