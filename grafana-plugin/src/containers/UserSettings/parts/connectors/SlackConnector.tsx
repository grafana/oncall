import React, { useCallback } from 'react';

import { Button, HorizontalGroup, InlineField, Input } from '@grafana/ui';

import PluginLink from 'components/PluginLink/PluginLink';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

interface SlackConnectorProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

const SlackConnector = (props: SlackConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore, teamStore } = store;

  const storeUser = userStore.items[id];

  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.SlackInfo);
  }, [onTabChange]);

  const handleUnlinkSlackAccount = useCallback(() => {
    userStore.unlinkSlack(userStore.currentUserPk);
  }, []);

  return (
    <>
      {storeUser.slack_user_identity ? (
        <>
          <InlineField label="Slack" labelWidth={12}>
            <HorizontalGroup spacing="xs">
              <Input
                disabled={true}
                value={
                  storeUser.slack_user_identity?.slack_login ? '@' + storeUser.slack_user_identity?.slack_login : ''
                }
              />
              <WithConfirm title="Are you sure to disconnect your Slack account?" confirmText="Disconnect">
                <Button
                  variant="destructive"
                  icon="times"
                  onClick={handleUnlinkSlackAccount}
                  disabled={!isCurrentUser}
                />
              </WithConfirm>
            </HorizontalGroup>
          </InlineField>
        </>
      ) : teamStore.currentTeam?.slack_team_identity ? (
        <>
          <InlineField label="Slack" labelWidth={12} disabled={!isCurrentUser}>
            <Button onClick={handleConnectButtonClick}>Connect account</Button>
          </InlineField>
        </>
      ) : (
        <>
          <InlineField label="Slack" labelWidth={12}>
            <PluginLink query={{ page: 'chat-ops' }}>
              <WithConfirm
                title="The Slack application is not installed globally for this Grafana Stack. You will be redirected to the Grafana OnCall organization settings to connect the Slack app. Please note that you may need Slack admin permissions to install the Slack app."
                confirmText="Proceed"
              >
                <Button>Install Slack App</Button>
              </WithConfirm>
            </PluginLink>
          </InlineField>
        </>
      )}
    </>
  );
};

export default SlackConnector;
