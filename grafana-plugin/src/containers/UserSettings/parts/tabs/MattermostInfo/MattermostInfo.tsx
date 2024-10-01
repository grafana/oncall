import React, { useCallback } from 'react';

import { css } from '@emotion/css';
import { Button, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { DOCS_MATTERMOST_SETUP, StackSize } from 'helpers/consts';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { useStore } from 'state/useStore';

export const MattermostInfo = () => {
  const styles = useStyles2(getStyles);

  const { mattermostStore } = useStore();

  const handleClickConnectMattermostAccount = useCallback(() => {
    mattermostStore.mattermostLogin();
  }, [mattermostStore]);

  return (
    <WithPermissionControlDisplay userAction={UserActions.UserSettingsWrite}>
      <Stack direction="column" gap={StackSize.lg}>
        <Block bordered withBackground className={styles.mattermostInfoblock}>
          <Stack direction="column" alignItems="center" gap={StackSize.lg}>
            <Text>
              Personal Mattermost connection will allow you to manage alert group in your connected mattermost channel
            </Text>
            <Text>To setup personal mattermost click the button below and login to your mattermost server</Text>

            <Text type="secondary">
              More details in{' '}
              <a href={DOCS_MATTERMOST_SETUP} target="_blank" rel="noreferrer">
                <Text type="link">our documentation</Text>
              </a>
            </Text>
          </Stack>
        </Block>
        <Stack gap={StackSize.xs} alignItems="center">
          <Button onClick={handleClickConnectMattermostAccount} icon="external-link-alt">
            Open Mattermost connection page
          </Button>
        </Stack>
      </Stack>
    </WithPermissionControlDisplay>
  );
};

const getStyles = () => {
  return {
    mattermostInfoblock: css`
      text-align: center;
    `,
  };
};
