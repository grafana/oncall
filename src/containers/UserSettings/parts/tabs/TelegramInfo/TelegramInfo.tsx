import React, { HTMLAttributes, useEffect, useState } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, Icon, Stack, Field, Input, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { DOCS_TELEGRAM_SETUP, StackSize } from 'helpers/consts';
import { openNotification } from 'helpers/helpers';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { TelegramColorIcon } from 'icons/Icons';
import { UserHelper } from 'models/user/user.helpers';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

interface TelegramInfoProps extends HTMLAttributes<HTMLElement> {}

export const TelegramInfo = observer((_props: TelegramInfoProps) => {
  const store = useStore();
  const { userStore, organizationStore } = store;

  const [verificationCode, setVerificationCode] = useState<string>();
  const [botLink, setBotLink] = useState<string>();

  const styles = useStyles2(getStyles);

  const telegramConfigured = organizationStore.currentOrganization?.env_status.telegram_configured;

  useEffect(() => {
    (async () => {
      const res = await UserHelper.fetchTelegramConfirmationCode(userStore.currentUserPk);
      setVerificationCode(res.telegram_code);
      setBotLink(res.bot_link);
    })();
  }, []);

  return (
    <WithPermissionControlDisplay userAction={UserActions.UserSettingsWrite}>
      {telegramConfigured || !store.hasFeature(AppFeature.LiveSettings) ? (
        <Stack direction="column">
          <Text.Title level={5}>Manual connection</Text.Title>

          <Text type="secondary">
            1. Go to{' '}
            <a className={styles.verificationCode} href={botLink} target="_blank" rel="noreferrer">
              {botLink}
            </a>
          </Text>

          <Text type="secondary">
            2. Send this verification code to the bot and wait for <Text>the confirmation message: </Text>
          </Text>
          <Field className={styles.fieldCommand}>
            <Input
              id="telegramVerificationCode"
              value={verificationCode}
              suffix={
                <CopyToClipboard
                  text={verificationCode}
                  onCopy={() => {
                    openNotification('Code is copied');
                  }}
                >
                  <Icon name="copy" />
                </CopyToClipboard>
              }
            />
          </Field>
          <Text type="secondary">3. Refresh the page and start to manage alerts in your personal Telegram.</Text>
        </Stack>
      ) : (
        <Stack direction="column" gap={StackSize.lg}>
          <Text.Title level={2}>Connect Telegram workspace</Text.Title>
          <Block
            bordered
            withBackground
            className={cx(
              styles.telegramInfoBlock,
              css`
                width: 100%;
              `
            )}
          >
            <Stack direction="column" alignItems="center" gap={StackSize.lg}>
              <TelegramColorIcon />
              <Text>You can manage alert groups in your team Telegram channel or from personal direct messages. </Text>

              <Text>
                To connect channel setup Telegram environment first, which includes connection to your bot and host URL.
              </Text>
              <Text type="secondary">
                More details in{' '}
                <a href={DOCS_TELEGRAM_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </Stack>
          </Block>
          {store.hasFeature(AppFeature.LiveSettings) && (
            <PluginLink query={{ page: 'live-settings' }}>
              <Button variant="primary">Setup ENV Variables</Button>
            </PluginLink>
          )}
        </Stack>
      )}
    </WithPermissionControlDisplay>
  );
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    verificationCode: css`
      color: ${theme.colors.primary.text};
    `,

    verificationCodeText: css`
      display: flex;
      justify-content: space-between;
    `,

    automaticConnect: css`
      width: 100%;
      display: flex;
      justify-content: space-between;
      margin-bottom: 24px;
    `,

    fieldCommand: css`
      width: 100%;
      display: inline-block;
    `,

    telegramInfoBlock: css`
      text-align: center;
      width: 725px;
    `,
  };
};
