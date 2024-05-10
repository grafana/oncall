export const WebhookFormFieldName = {
  Name: 'name',
  IsWebhookEnabled: 'is_webhook_enabled',
  Team: 'team',
  TriggerType: 'trigger_type',
  HttpMethod: 'http_method',
  IntegrationFilter: 'integration_filter',
  Labels: 'labels',
  Url: 'url',
  Headers: 'headers',
  Username: 'username',
  Password: 'password',
  AuthorizationHeader: 'authorization_header',
  TriggerTemplate: 'trigger_template',
  ForwardAll: 'forward_all',
  Data: 'data',
} as const;

export type WebhookFormFieldName = (typeof WebhookFormFieldName)[keyof typeof WebhookFormFieldName];

export interface TemplateParams {
  name: WebhookFormFieldName;
  value: string;
  displayName: string;
}
