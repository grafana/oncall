import React from 'react';

import { VerticalGroup } from '@grafana/ui';

import Timeline from 'components/Timeline/Timeline';
import SlackConnector from 'containers/AlertRules/parts/connectors/SlackConnector';
import TelegramConnector from 'containers/AlertRules/parts/connectors/TelegramConnector';
import { ChannelFilter } from 'models/channel_filter';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { getVar } from 'utils/DOM';

interface ChatOpsConnectorsProps {
  channelFilterId: ChannelFilter['id'];
}

export const ChatOpsConnectors = (props: ChatOpsConnectorsProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const { telegramChannelStore } = store;

  const isSlackInstalled = Boolean(store.teamStore.currentTeam?.slack_team_identity);
  const isTelegramInstalled =
    store.hasFeature(AppFeature.Telegram) && telegramChannelStore.currentTeamToTelegramChannel?.length > 0;

  if (!isSlackInstalled && !isTelegramInstalled) {
    return null;
  }

  return (
    <Timeline.Item number={0} backgroundColor={getVar('--tag-secondary')}>
      <VerticalGroup>
        {isSlackInstalled && <SlackConnector channelFilterId={channelFilterId} />}
        {isTelegramInstalled && <TelegramConnector channelFilterId={channelFilterId} />}
      </VerticalGroup>
    </Timeline.Item>
  );
};
