import React, { FC } from 'react';

import { Legend } from '@grafana/ui';

import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

import { ICalConnector } from './ICalConnector';
import { MSTeamsConnector } from './MSTeamsConnector';
import { MobileAppConnector } from './MobileAppConnector';
import { PhoneConnector } from './PhoneConnector';
import { SlackConnector } from './SlackConnector';
import { TelegramConnector } from './TelegramConnector';

interface ConnectorsProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const Connectors: FC<ConnectorsProps> = (props) => {
  const store = useStore();
  return (
    <>
      <PhoneConnector {...props} />
      <MobileAppConnector {...props} />
      <SlackConnector {...props} />
      {store.hasFeature(AppFeature.Telegram) && <TelegramConnector {...props} />}
      {store.hasFeature(AppFeature.MsTeams) && <MSTeamsConnector {...props} />}
      <Legend>Calendar export</Legend>
      <ICalConnector {...props} />
    </>
  );
};
