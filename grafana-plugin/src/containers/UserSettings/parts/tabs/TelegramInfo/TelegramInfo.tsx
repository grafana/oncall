import React, { HTMLAttributes, useEffect, useState } from 'react';

import { Alert, Button, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';

import styles from './TelegramInfo.module.css';

const cx = cn.bind(styles);

interface TelegramInfoProps extends HTMLAttributes<HTMLElement> {}

const TelegramInfo = observer((_props: TelegramInfoProps) => {
  const { userStore, teamStore, hasFeature } = useStore();

  const [verificationCode, setVerificationCode] = useState<string>();
  const [botLink, setBotLink] = useState<string>();

  const telegramConfigured = teamStore.currentTeam?.env_status.telegram_configured;

  useEffect(() => {
    userStore.sendTelegramConfirmationCode(userStore.currentUserPk).then((res) => {
      setVerificationCode(res.telegram_code);
      setBotLink(res.bot_link);
    });
  }, [userStore]);

  return (
    <>
      {telegramConfigured || !hasFeature(AppFeature.LiveSettings) ? (
        <VerticalGroup>
          <a href={`${botLink}/?start=${verificationCode}`} target="_blank" rel="noreferrer">
            <Button size="sm" fill="outline">
              Connect automatically
            </Button>
          </a>
          <Text>Or add bot manually:</Text>
          <HorizontalGroup>
            <Text>
              1) Go to{' '}
              <a className={cx('verification-code')} href={botLink} target="_blank" rel="noreferrer">
                {botLink}
              </a>
            </Text>
          </HorizontalGroup>
          <HorizontalGroup className={cx('verification-code-text')}>
            <Text>2) Send </Text>
            <Text className={cx('verification-code')}>{verificationCode}</Text>
            <CopyToClipboard
              text={verificationCode}
              onCopy={() => {
                openNotification('Verification code copied');
              }}
            >
              <Icon name="copy" />
            </CopyToClipboard>
            <Text>to telegram bot </Text>
          </HorizontalGroup>
        </VerticalGroup>
      ) : (
        <Alert
          severity="warning"
          // @ts-ignore
          title={
            <>
              Can't connect Telegram. <PluginLink query={{ page: 'live-settings' }}> Check ENV variables</PluginLink>{' '}
              related to Telegram.
            </>
          }
        />
      )}
    </>
  );
});

export default TelegramInfo;
