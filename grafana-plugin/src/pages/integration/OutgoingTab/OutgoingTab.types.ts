export type OutgoingTabDrawerKey = 'webhookDetails' | 'newOutgoingWebhook';

export const TriggerDetailsQueryStringKey = {
  ActiveTab: 'activeEventTriggerDrawerTab',
  WebhookId: 'webhookId',
};

export const TriggerDetailsTab = {
  Settings: 'Settings',
  LastEvent: 'Last event',
} as const;
export type TriggerDetailsTab = (typeof TriggerDetailsTab)[keyof typeof TriggerDetailsTab];

export interface OutgoingTabFormValues {
  triggerType: string;
  isEnabled?: boolean;
  url: string;
  httpMethod: string;
  triggerTemplateToogle?: boolean;
  triggerTemplate?: string;
  forwardedDataTemplateToogle?: boolean;
  forwardedDataTemplate?: string;
}
