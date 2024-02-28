import { useStore } from 'state/useStore';
import { LocationHelper } from 'utils/LocationHelper';

import { TriggerDetailsQueryStringKey } from './OutgoingTab.types';

export const useDrawerWebhook = () => {
  const webhookId = LocationHelper.getQueryParam(TriggerDetailsQueryStringKey.WebhookId);
  const {
    alertReceiveChannelWebhooksStore: { items },
  } = useStore();
  return items[webhookId];
};
