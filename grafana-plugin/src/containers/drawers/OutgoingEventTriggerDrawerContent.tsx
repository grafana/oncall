import React from 'react';

import { observer } from 'mobx-react';

import { useDrawerData } from 'models/drawer/drawer.hooks';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';

const OutgoingEventTriggerDrawerContent = observer(() => {
  const webhook = useDrawerData<OutgoingWebhook>();

  console.log(webhook);

  return <>content</>;
});

export default OutgoingEventTriggerDrawerContent;
