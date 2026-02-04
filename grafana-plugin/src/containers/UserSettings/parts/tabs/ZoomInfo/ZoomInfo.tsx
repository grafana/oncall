import React, { useCallback } from 'react';

import { css } from '@emotion/css';
import { Button, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { DOCS_ZOOM_SETUP, StackSize } from 'helpers/consts';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { useStore } from 'state/useStore';

export const ZoomInfo = () => {
  const styles = useStyles2(getStyles);

  const { zoomStore } = useStore();

  const handleClickConnectZoomAccount = useCallback(() => {
    zoomStore.zoomLogin();
  }, [zoomStore]);

  return (
    <WithPermissionControlDisplay userAction={UserActions.UserSettingsWrite}>
      <Stack direction="column" gap={StackSize.lg}>
        <Block bordered withBackground className={styles.zoomInfoblock}>
          <Stack direction="column" alignItems="center" gap={StackSize.lg}>
            <Text>
              Personal Zoom connection will allow you to manage alert groups in your connected Zoom Team Chat channel
            </Text>
            <Text>To link your Zoom account, click the button below and login to your Zoom workspace</Text>

            <Text type="secondary">
              More details in{' '}
              <a href={DOCS_ZOOM_SETUP} target="_blank" rel="noreferrer">
                <Text type="link">our documentation</Text>
              </a>
            </Text>
          </Stack>
        </Block>
        <Stack gap={StackSize.xs} alignItems="center">
          <Button onClick={handleClickConnectZoomAccount} icon="external-link-alt">
            Open Zoom connection page
          </Button>
        </Stack>
      </Stack>
    </WithPermissionControlDisplay>
  );
};

const getStyles = () => {
  return {
    zoomInfoblock: css`
      text-align: center;
    `,
  };
};
