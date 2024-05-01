import React, { useEffect } from 'react';

import { VerticalGroup, useTheme2 } from '@grafana/ui';

import { Timeline } from 'components/Timeline/Timeline';
import { MSTeamsConnector } from 'containers/AlertRules/parts/connectors/MSTeamsConnector';
import { SlackConnector } from 'containers/AlertRules/parts/connectors/SlackConnector';
import { TelegramConnector } from 'containers/AlertRules/parts/connectors/TelegramConnector';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

interface ChatOpsConnectorsProps {
  channelFilterId: ChannelFilter['id'];
  showLineNumber?: boolean;
}

export const ChatOpsConnectors = (props: ChatOpsConnectorsProps) => {
  const { channelFilterId, showLineNumber = true } = props;

  const store = useStore();
  const theme = useTheme2();
  const { organizationStore, telegramChannelStore, msteamsChannelStore } = store;

  const isSlackInstalled = Boolean(organizationStore.currentOrganization?.slack_team_identity);
  const isTelegramInstalled =
    store.hasFeature(AppFeature.Telegram) && telegramChannelStore.currentTeamToTelegramChannel?.length > 0;

  useEffect(() => {
    msteamsChannelStore.updateMSTeamsChannels();
  }, []);

  const isMSTeamsInstalled = msteamsChannelStore.currentTeamToMSTeamsChannel?.length > 0;

  if (!isSlackInstalled && !isTelegramInstalled && !isMSTeamsInstalled) {
    return null;
  }

  return (
    <Timeline.Item number={0} backgroundHexNumber={theme.colors.secondary.main} isDisabled={!showLineNumber}>
      <VerticalGroup>
        {isSlackInstalled && <SlackConnector channelFilterId={channelFilterId} />}
        {isTelegramInstalled && <TelegramConnector channelFilterId={channelFilterId} />}
        {isMSTeamsInstalled && <MSTeamsConnector channelFilterId={channelFilterId} />}
      </VerticalGroup>
    </Timeline.Item>
  );
};
