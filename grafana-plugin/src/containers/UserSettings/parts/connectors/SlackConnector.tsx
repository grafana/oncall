import React, { useCallback, useMemo } from 'react';

import { Button, InlineField, Input, Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { getPathFromQueryParams } from 'helpers/url';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface SlackConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const SlackConnector = observer((props: SlackConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore, organizationStore } = store;

  const storeUser = userStore.items[id];

  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.SlackInfo);
  }, [onTabChange]);

  const handleUnlinkSlackAccount = useCallback(() => {
    userStore.unlinkSlack(userStore.currentUserPk);
  }, []);

  const chatOpsQuery = { page: 'chat-ops' };
  const chatOpsPath = useMemo(() => getPathFromQueryParams(chatOpsQuery), [chatOpsQuery]);

  return (
    <>
      {storeUser.slack_user_identity ? (
        <>
          <InlineField
            label="Slack"
            labelWidth={12}
            tooltip={'Connected Slack user will receive mentions during escalations'}
          >
            <Stack gap={StackSize.xs}>
              <Input
                disabled={true}
                value={
                  storeUser.slack_user_identity?.display_name ? '@' + storeUser.slack_user_identity?.display_name : ''
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
            </Stack>
          </InlineField>
        </>
      ) : organizationStore.currentOrganization?.slack_team_identity ? (
        <>
          <InlineField
            label="Slack"
            labelWidth={12}
            disabled={!isCurrentUser}
            tooltip={'To receive mentions for alert groups posted on Slack, connect your Slack profile.'}
          >
            <Button onClick={handleConnectButtonClick}>Connect account</Button>
          </InlineField>
        </>
      ) : (
        <>
          <InlineField
            label="Slack"
            labelWidth={12}
            tooltip={'To receive mentions for alert groups posted on Slack, connect your Slack profile.'}
          >
            <WithConfirm
              title="Leave personal profile settings?"
              confirmText="Continue"
              description="OnCall Slack Application is not installed globally for this Grafana Organization Stack. Please install it in Organization Settings before connecting personal Slack Profile."
            >
              <Button onClick={() => window.open(chatOpsPath, '_blank')} icon="external-link-alt">
                Install Slack App
              </Button>
            </WithConfirm>
          </InlineField>
        </>
      )}
    </>
  );
});
