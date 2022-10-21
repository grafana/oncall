import React, { FC } from 'react';

import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';

import ICalConnector from './ICalConnector';
import MobileAppConnector from './MobileAppConnector';
import PhoneConnector from './PhoneConnector';
import SlackConnector from './SlackConnector';
import TelegramConnector from './TelegramConnector';

interface ConnectorsProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const Connectors: FC<ConnectorsProps> = (props) => (
  <div>
    <PhoneConnector {...props} />
    <SlackConnector {...props} />
    <TelegramConnector {...props} />
    <ICalConnector {...props} />
    <MobileAppConnector {...props} />
  </div>
);
