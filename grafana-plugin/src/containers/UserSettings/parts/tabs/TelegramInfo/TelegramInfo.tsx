import React, { HTMLAttributes, useEffect, useState } from 'react';

import { Alert, Button, HorizontalGroup, Icon, VerticalGroup, Field, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import Block from 'components/GBlock/Block';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';
import { TelegramColorIcon } from 'icons';

import styles from './TelegramInfo.module.css';

const cx = cn.bind(styles);

interface TelegramInfoProps extends HTMLAttributes<HTMLElement> {}

const TelegramInfo = observer((props: TelegramInfoProps) => {
  const store = useStore();
  const { userStore, teamStore } = store;

  const [verificationCode, setVerificationCode] = useState<string>();
  const [botLink, setBotLink] = useState<string>();

  const telegramConfigured = teamStore.currentTeam?.env_status.telegram_configured;

  useEffect(() => {
    userStore.sendTelegramConfirmationCode(userStore.currentUserPk).then((res) => {
      setVerificationCode(res.telegram_code);
      setBotLink(res.bot_link);
    });
  }, []);

  return (
    <>
      {telegramConfigured || !store.hasFeature(AppFeature.LiveSettings) ? (
        <VerticalGroup>
          <Text.Title level={5}>Connect personal Telegram</Text.Title>
          <Block bordered withBackground className={cx('automatic-connect-telegram-block')}>
            <Text type="secondary">Connect Telegram automatically</Text>
            <a href={`${botLink}/?start=${verificationCode}`} target="_blank" rel="noreferrer">
              <Button size="sm">Connect account</Button>
            </a>
          </Block>
          <Text.Title level={5}>Manual connection</Text.Title>

          <Text type="secondary">
            1. Go to{' '}
            <a className={cx('verification-code')} href={botLink} target="_blank" rel="noreferrer">
              {botLink}
            </a>
          </Text>

          <Text type="secondary">
            2. Send this verification code to the bot and wait for <Text>the confirmation message: </Text>
          </Text>
          <Field className={cx('field-command')}>
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
        </VerticalGroup>
      ) : (
        <VerticalGroup spacing="lg">
          <Text.Title level={2}>Connect Telegram workspace</Text.Title>
          <Block bordered withBackground className={cx('telegram-infoblock')}>
            <VerticalGroup align="center" spacing="lg">
              <TelegramColorIcon />
              <Text>You can manage incidents in your team Telegram channel or from personal direct messages. </Text>

              <Text>
                To connect channel setup Telegram environment first, which includes connection to your bot and host URL.
              </Text>
              <Text type="secondary">
                More details in{' '}
                <a href="https://grafana.com/docs/grafana-cloud/oncall/chat-options/configure-telegram/">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            </VerticalGroup>
          </Block>
          <PluginLink query={{ page: 'live-settings' }}>
            <Button variant="primary">Setup ENV Variables</Button>
          </PluginLink>
        </VerticalGroup>
      )}
    </>
  );
});

export default TelegramInfo;
