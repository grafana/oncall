export const Datasource = {
  GrafanaCloudPrometheus: {
    type: 'prometheus',
    uid: 'grafanacloud-usage',
  },
} as const;
export type WebhookFormFieldName = (typeof Datasource)[keyof typeof Datasource];
