import { Moment } from 'moment';

export enum FormItemType {
  'Input' = 'input',
  'TextArea' = 'textarea',
  'Select' = 'select',
  'GSelect' = 'gselect',
  'Switch' = 'switch',
  'RemoteSelect' = 'remoteselect',

  /* 'InputNumber' = 'input-number',
  'Select' = 'select',
  'Switch' = 'switch',
  'ASelect' = 'aselect',
  'JustSelect' = 'just-select',
  'DatePicker' = 'datepicker', */
}

export interface FormItem {
  name: string;
  label?: string;
  type: FormItemType;
  description?: string;
  normalize?: (value: any) => any;
  getDisabled?: (value: any) => any;
  validation?: {
    required?: boolean;
    validation?: (v: any) => boolean;
  };
  extra?: any;
}
