import { LocationHelper } from 'helpers/LocationHelper';
import { useParams } from 'react-router-dom-v5-compat';

import { useStore } from 'state/useStore';

import { TriggerDetailsQueryStringKey } from './OutgoingTab.types';

export const useDrawerWebhook = () => {
  const webhookId = LocationHelper.getQueryParam(TriggerDetailsQueryStringKey.WebhookId);
  const {
    alertReceiveChannelWebhooksStore: { items },
  } = useStore();
  return items[webhookId];
};

export const useIntegrationIdFromUrl = () => useParams<{ id: string }>().id;

export const useCurrentIntegration = () => {
  const {
    alertReceiveChannelStore: { items },
  } = useStore();
  const id = useIntegrationIdFromUrl();
  return items[id];
};
