import React, { useEffect } from 'react';

import { Stack, useTheme2 } from '@grafana/ui';

import { Timeline } from 'components/Timeline/Timeline';
import { MSTeamsConnector } from 'containers/AlertRules/parts/connectors/MSTeamsConnector';
import { MattermostConnector } from 'containers/AlertRules/parts/connectors/MattermostConnector';
import { SlackConnector } from 'containers/AlertRules/parts/connectors/SlackConnector';
import { TelegramConnector } from 'containers/AlertRules/parts/connectors/TelegramConnector';
import { ZoomConnector } from 'containers/AlertRules/parts/connectors/ZoomConnector';
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
  const { organizationStore, telegramChannelStore, msteamsChannelStore, mattermostChannelStore, zoomChannelStore } = store;

  const isSlackInstalled = Boolean(organizationStore.currentOrganization?.slack_team_identity);
  const isTelegramInstalled =
    store.hasFeature(AppFeature.Telegram) && telegramChannelStore.currentTeamToTelegramChannel?.length > 0;

  useEffect(() => {
    msteamsChannelStore.updateMSTeamsChannels();
    mattermostChannelStore.updateMattermostChannels();
    if (store.hasFeature(AppFeature.Zoom)) {
      zoomChannelStore.updateZoomChannels();
    }
  }, []);

  const isMSTeamsInstalled = msteamsChannelStore.currentTeamToMSTeamsChannel?.length > 0;
  const isMattermostInstalled = store.hasFeature(AppFeature.Mattermost) && Object.keys(mattermostChannelStore.items).length > 0;
  const isZoomInstalled = store.hasFeature(AppFeature.Zoom) && Object.keys(zoomChannelStore.items).length > 0;

  if (!isSlackInstalled && !isTelegramInstalled && !isMSTeamsInstalled && !isMattermostInstalled && !isZoomInstalled) {
    return null;
  }

  return (
    <Timeline.Item number={0} backgroundHexNumber={theme.colors.secondary.main} isDisabled={!showLineNumber}>
      <Stack direction="column">
        {isSlackInstalled && <SlackConnector channelFilterId={channelFilterId} />}
        {isTelegramInstalled && <TelegramConnector channelFilterId={channelFilterId} />}
        {isMSTeamsInstalled && <MSTeamsConnector channelFilterId={channelFilterId} />}
        {isMattermostInstalled && <MattermostConnector channelFilterId={channelFilterId} />}
        {isZoomInstalled && <ZoomConnector channelFilterId={channelFilterId} />}
      </Stack>
    </Timeline.Item>
  );
};
