import { FormItem, FormItemType } from 'components/GForm/GForm.types';

export type FormData = {
  message: string;
};

export const manualAlertFormConfig: { name: string; fields: FormItem[] } = {
  name: 'Manual Alert Group',
  fields: [
    {
      name: 'message',
      type: FormItemType.TextArea,
      label: 'What is going on?',
      validation: { required: true },
    },
  ],
};
