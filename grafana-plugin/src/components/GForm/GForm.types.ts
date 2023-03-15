export enum FormItemType {
  'Input' = 'input',
  'TextArea' = 'textarea',
  'MultiSelect' = 'multiselect',
  'Select' = 'select',
  'GSelect' = 'gselect',
  'Switch' = 'switch',
  'RemoteSelect' = 'remoteselect',
}

export interface FormItem {
  name: string;
  label?: string;
  type: FormItemType;
  description?: string;
  normalize?: (value: any) => any;
  shouldShow?: (data: any) => any;
  getDisabled?: (value: any) => any;
  validation?: {
    required?: boolean;
    validation?: (v: any) => boolean;
  };
  extra?: any;
}
