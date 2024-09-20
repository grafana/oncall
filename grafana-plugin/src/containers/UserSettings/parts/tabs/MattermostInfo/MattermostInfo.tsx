import React, { useCallback } from 'react';

import { Button, Stack } from '@grafana/ui';
import cn from 'classnames/bind';
import { UserActions } from 'helpers/authorization/authorization';
import { DOCS_MATTERMOST_SETUP, StackSize } from 'helpers/consts';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { useStore } from 'state/useStore';

import styles from './MattermostInfo.module.css';

const cx = cn.bind(styles);

export const MattermostInfo = () => {
  const { mattermostStore } = useStore();

  const handleClickConnectMattermostAccount = useCallback(() => {
    mattermostStore.mattermostLogin();
  }, [mattermostStore]);

  return (
    <WithPermissionControlDisplay userAction={UserActions.UserSettingsWrite}>
      <Stack direction="column" gap={StackSize.lg}>
        <Block bordered withBackground className={cx('mattermost-infoblock', 'u-width-100')}>
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
