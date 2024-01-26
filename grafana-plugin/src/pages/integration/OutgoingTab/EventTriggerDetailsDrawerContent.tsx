import React, { FC } from 'react';

import Tabs from 'components/Tabs/Tabs';

import { TriggerDetailsQueryStringKey, TriggerDetailsTab } from './OutgoingTab.types';

interface EventTriggerDetailsDrawerContentProps {
  closeDrawer: () => void;
}

export const EventTriggerDetailsDrawerContent: FC<EventTriggerDetailsDrawerContentProps> = ({ closeDrawer }) => {
  return (
    <Tabs
      queryStringKey={TriggerDetailsQueryStringKey.ActiveTab}
      tabs={[
        { label: TriggerDetailsTab.Settings, content: <div>settings</div> },
        { label: TriggerDetailsTab.LastEvent, content: <div>Last event</div> },
      ]}
    />
  );
};
