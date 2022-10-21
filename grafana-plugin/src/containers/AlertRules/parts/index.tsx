import React from 'react';

import { VerticalGroup } from '@grafana/ui';

import Timeline from 'components/Timeline/Timeline';
import SlackConnector from 'containers/AlertRules/parts/connectors/SlackConnector';
import TelegramConnector from 'containers/AlertRules/parts/connectors/TelegramConnector';
import { ChannelFilter } from 'models/channel_filter';
import { useStore } from 'state/useStore';

interface ChatOpsConnectorsProps {
  channelFilterId: ChannelFilter['id'];
}

export const ChatOpsConnectors = ({ channelFilterId }: ChatOpsConnectorsProps) => {
  const { telegramChannelStore, teamStore } = useStore();

  const isSlackInstalled = Boolean(teamStore.currentTeam?.slack_team_identity);
  const isTelegramInstalled = Boolean(telegramChannelStore.currentTeamToTelegramChannel?.length > 0);

  if (!isSlackInstalled && !isTelegramInstalled) {
    return null;
  }

  return (
    <Timeline.Item number={0} color="#464C54">
      <VerticalGroup>
        {isSlackInstalled && <SlackConnector channelFilterId={channelFilterId} />}
        {isTelegramInstalled && <TelegramConnector channelFilterId={channelFilterId} />}
      </VerticalGroup>
    </Timeline.Item>
  );
};
