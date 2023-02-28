import React, { FC } from 'react';

import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';
import { RootStore } from 'state';
import { AppFeature } from 'state/features';

import ICalConnector from './ICalConnector';
import MobileAppConnector from './MobileAppConnector';
import PhoneConnector from './PhoneConnector';
import SlackConnector from './SlackConnector';
import TelegramConnector from './TelegramConnector';

interface ConnectorsProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
  store: RootStore;
}

export const Connectors: FC<ConnectorsProps> = (props) => {
  const { store } = props;
  return (
    <div>
      <PhoneConnector {...props} />
      <SlackConnector {...props} />
      {store.hasFeature(AppFeature.Telegram) && <TelegramConnector {...props} />}
      <ICalConnector {...props} />
      <MobileAppConnector {...props} />
    </div>
  );
};
