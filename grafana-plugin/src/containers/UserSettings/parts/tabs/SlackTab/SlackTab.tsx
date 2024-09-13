import React, { useCallback } from 'react';

import { css } from '@emotion/css';
import { Button, Stack, Icon, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize, DOCS_SLACK_SETUP, getPluginId } from 'helpers/consts';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { SlackNewIcon } from 'icons/Icons';
import { useStore } from 'state/useStore';

export const SlackTab = () => {
  const { slackStore } = useStore();

  const handleClickConnectSlackAccount = useCallback(() => {
    slackStore.slackLogin();
  }, [slackStore]);

  const styles = useStyles2(getStyles);

  return (
    <WithPermissionControlDisplay userAction={UserActions.UserSettingsWrite}>
      <Stack direction="column" gap={StackSize.lg}>
        <Block bordered withBackground className={styles.slackInfoblock}>
          <Stack direction="column" alignItems="center" gap={StackSize.lg}>
            <SlackNewIcon />
            <Text>
              Personal Slack connection will allow you to manage alert groups in your connected team's Internal Slack
              workspace.
            </Text>
            <Text>To setup personal Slack click the button below, choose workspace and click Allow.</Text>

            <Text type="secondary">
              More details in{' '}
              <a href={DOCS_SLACK_SETUP} target="_blank" rel="noreferrer">
                <Text type="link">our documentation</Text>
              </a>
            </Text>

            <img
              style={{ height: '350px', display: 'block', margin: '0 auto' }}
              src={`public/plugins/${getPluginId()}/assets/img/slack_instructions.png`}
            />
          </Stack>
        </Block>
        <Button onClick={handleClickConnectSlackAccount}>
          <Stack gap={StackSize.xs} alignItems="center">
            <Icon name="external-link-alt" className={styles.externalLinkStyle} /> Open Slack connection page
          </Stack>
        </Button>
      </Stack>
    </WithPermissionControlDisplay>
  );
};

const getStyles = () => {
  return {
    footer: css`
      display: flex;
      justify-content: flex-end;
    `,

    slackInfoblock: css`
      text-align: center;
      width: 725px;
    `,

    externalLinkStyle: css`
      margin-right: 4px;
      align-self: baseline;
    `,
  };
};
