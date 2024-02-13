export interface ItemGroup {
  key: any;
  values: any[];
}

export interface ItemSelected {
  key: any;
  value: any;
}

export enum LabelInputType {
  key = 'key',
  value = 'value',
}

export interface ServiceLabelValidator {
  isValid: boolean;
  errorMessage?: string;
}
