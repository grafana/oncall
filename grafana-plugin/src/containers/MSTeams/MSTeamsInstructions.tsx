import React, { FC } from 'react';

import { Button, Icon, VerticalGroup, Field, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import MSTeamsLogo from 'icons/MSTeamsLogo';
import { useStore } from 'state/useStore';
import { openNotification, openWarningNotification } from 'utils/utils';

import styles from './MSTeamsInstructions.module.css';

interface MSTeamsInstructionsProps {
  onCallisAdded?: boolean;
  showInfoBox?: boolean;
  personalSettings?: boolean;
  verificationCode: string;
  onHide?: () => void;
}

const cx = cn.bind(styles);

export const MSTeamsInstructions: FC<MSTeamsInstructionsProps> = observer((props) => {
  const { onCallisAdded, showInfoBox, personalSettings, onHide = () => {}, verificationCode } = props;
  const { msteamsChannelStore } = useStore();

  const handleMSTeamsGetChannels = async () => {
    await msteamsChannelStore.updateItems();
    const connectedChannels = msteamsChannelStore.getSearchResult();

    if (!connectedChannels?.length) {
      openWarningNotification('No MS Teams channels found');
    }

    onHide();
  };

  return (
    <VerticalGroup align="flex-start" spacing="lg">
      {!personalSettings && <Text.Title level={2}>Connect MS Teams workspace</Text.Title>}
      {showInfoBox && (
        <Block bordered withBackground className={cx('info-block')}>
          <VerticalGroup align="center">
            <div style={{ width: '60px', marginTop: '24px' }}>
              <MSTeamsLogo />
            </div>
            <Text>You can manage alert groups in your Microsoft Teams workspace.</Text>
            <br />
            {personalSettings ? (
              <VerticalGroup align="center">
                <Text>This setup is for direct profile connection with bot. </Text>
                <br />
                <Text className={cx('infoblock-text')}>
                  To manage alert groups in Team channel, setup{' '}
                  <PluginLink query={{ page: 'chat-ops', tab: 'MSTeams' }}>Team ChatOps</PluginLink>
                </Text>
              </VerticalGroup>
            ) : (
              <VerticalGroup align="center">
                <Text>This setup is for Team channel connection with bot. </Text>
                <br />
                <Text className={cx('infoblock-text')}>
                  To manage alert groups in Direct Messages and verify users who are allowed to operate with MS Teams,
                  setup <PluginLink query={{ page: 'users', id: 'me' }}>personal MS Teams connection</PluginLink>
                </Text>
              </VerticalGroup>
            )}
          </VerticalGroup>
        </Block>
      )}

      {!onCallisAdded && (
        <Text type="secondary">
          1. Go to{' '}
          <a href="https://appsource.microsoft.com/en-us/product/office/WA200004307" target="_blank" rel="noreferrer">
            <Text type="link">MS Teams marketplace</Text>
          </a>{' '}
          and add <Text type="primary">Grafana OnCall app</Text> to your MS Teams org workspace.{' '}
        </Text>
      )}
      <Text type="secondary">
        {!onCallisAdded ? 2 : 1}.{' '}
        {personalSettings ? (
          <Text type="secondary">
            Send a direct message to the Grafana OnCall bot using <Text type="primary">⁠linkUser</Text> command with
            following code:
          </Text>
        ) : (
          <Text type="secondary">
            Add OnCall bot to your team channel and send this code by{' '}
            <Text type="primary">@Grafana OnCall linkTeam</Text> command
          </Text>
        )}
        <Field className={cx('field-command')}>
          <Input
            id="msTeamsCommand"
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
      </Text>
      <Block bordered withBackground className={cx('info-block')}>
        <Text type="secondary">
          For more information please read{' '}
          <a href="https://grafana.com/docs/oncall/latest/notify/ms-teams/" target="_blank" rel="noreferrer">
            <Text type="link">OnCall documentation</Text>
          </a>
          .
        </Text>
      </Block>
      {!personalSettings && (
        <div className={cx('done-button')}>
          <Button onClick={handleMSTeamsGetChannels}>Done</Button>
        </div>
      )}
    </VerticalGroup>
  );
});
