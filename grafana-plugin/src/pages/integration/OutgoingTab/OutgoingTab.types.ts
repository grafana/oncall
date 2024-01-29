export type OutgoingTabDrawerKey = 'urlSettings' | 'triggerDetails' | 'newEventTrigger';

export const TriggerDetailsQueryStringKey = {
  ActiveTab: 'activeEventTriggerDrawerTab',
  WebhookId: 'webhookId',
};

export const TriggerDetailsTab = {
  Settings: 'Settings',
  LastEvent: 'Last event',
} as const;
export type TriggerDetailsTab = (typeof TriggerDetailsTab)[keyof typeof TriggerDetailsTab];

export interface FormValues {
  triggerType: string;
  isEnabled?: boolean;
  triggerTemplateToogle?: boolean;
  triggerTemplate?: string;
  forwardedDataTemplateToogle?: boolean;
  forwardedDataTemplate?: string;
}
