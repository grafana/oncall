export const IntegrationFormFieldName = {
  VerbalName: 'verbal_name',
  DescriptionShort: 'description_short',
  Team: 'team',
  Alerting: 'alerting',
  AlertManager: 'alert_manager',
  ContactPoint: 'contact_point',
  IsExisting: 'is_existing',
  Labels: 'labels',
} as const;
export type IntegrationFormFieldName = (typeof IntegrationFormFieldName)[keyof typeof IntegrationFormFieldName];
