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
      label: 'Message (optional)',
      validation: { required: false },
    },
  ],
};
