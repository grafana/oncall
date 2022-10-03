import React from 'react';

import { VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Timeline from 'components/Timeline/Timeline';
import MattermostConnector from 'containers/AlertRules/parts/connectors/MattermostConnector';
import SlackConnector from 'containers/AlertRules/parts/connectors/SlackConnector';
import TelegramConnector from 'containers/AlertRules/parts/connectors/TelegramConnector';
import { ChannelFilter } from 'models/channel_filter';
import { useStore } from 'state/useStore';

import styles from 'containers/AlertRules/parts/index.module.css';

const cx = cn.bind(styles);

interface ChatOpsConnectorsProps {
  channelFilterId: ChannelFilter['id'];
}

export const ChatOpsConnectors = (props: ChatOpsConnectorsProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const { telegramChannelStore } = store;

  // TODO: implement right check for Mattermost
  const isMattermostInstalled = true;
  const isSlackInstalled = Boolean(store.teamStore.currentTeam?.slack_team_identity);
  const isTelegramInstalled = Boolean(telegramChannelStore.currentTeamToTelegramChannel?.length > 0);

  if (!isMattermostInstalled && !isSlackInstalled && !isTelegramInstalled) {
    return null;
  }

  return (
    <Timeline.Item number={0} color="#464C54">
      <VerticalGroup>
        {isSlackInstalled && <SlackConnector channelFilterId={channelFilterId} />}
        {isTelegramInstalled && <TelegramConnector channelFilterId={channelFilterId} />}
        {isMattermostInstalled && <MattermostConnector channelFilterId={channelFilterId} />}
      </VerticalGroup>
    </Timeline.Item>
  );
};
