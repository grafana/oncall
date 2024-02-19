import { ReactNode } from 'react';

export enum FormItemType {
  'Input' = 'input',
  'Password' = 'password',
  'TextArea' = 'textarea',
  'MultiSelect' = 'multiselect',
  'Select' = 'select',
  'GSelect' = 'gselect',
  'Switch' = 'switch',
  'RemoteSelect' = 'remoteselect',
  'Monaco' = 'monaco',
  'Other' = 'other',
  'PlainLabel' = 'plainlabel',
}

export interface FormItem {
  name: string;
  label?: ReactNode;
  type: FormItemType;
  disabled?: boolean;
  description?: ReactNode;
  placeholder?: string;
  normalize?: (value: any) => any;
  isHidden?: (data: any) => any;
  getDisabled?: (value: any) => any;
  validation?: {
    required?: boolean;
    validation?: (v: any) => boolean;
  };
  extra?: any;
  collapsed?: boolean;
  render?: boolean;
}
