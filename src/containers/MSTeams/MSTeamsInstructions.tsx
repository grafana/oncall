import React, { FC } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, Icon, Stack, Field, Input, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { openWarningNotification, openNotification } from 'helpers/helpers';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import MSTeamsLogo from 'icons/MSTeamsLogo';
import { useStore } from 'state/useStore';

interface MSTeamsInstructionsProps {
  onCallisAdded?: boolean;
  showInfoBox?: boolean;
  personalSettings?: boolean;
  verificationCode: string;
  onHide?: () => void;
}

export const MSTeamsInstructions: FC<MSTeamsInstructionsProps> = observer((props) => {
  const styles = useStyles2(getStyles);

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
    <Stack direction="column" alignItems="flex-start" gap={StackSize.lg}>
      {!personalSettings && <Text.Title level={2}>Connect MS Teams workspace</Text.Title>}
      {showInfoBox && (
        <Block bordered withBackground className={styles.infoBlock}>
          <Stack direction="column" alignItems="center">
            <div style={{ width: '60px', marginTop: '24px' }}>
              <MSTeamsLogo />
            </div>
            <Text>You can manage alert groups in your Microsoft Teams workspace.</Text>
            <br />
            {personalSettings ? (
              <Stack direction="column" alignItems="center">
                <Text>This setup is for direct profile connection with bot. </Text>
                <br />
                <Text className={styles.infoblockText}>
                  To manage alert groups in Team channel, setup{' '}
                  <PluginLink query={{ page: 'chat-ops', tab: 'MSTeams' }}>Team ChatOps</PluginLink>
                </Text>
              </Stack>
            ) : (
              <Stack direction="column" alignItems="center">
                <Text>This setup is for Team channel connection with bot. </Text>
                <br />
                <Text className={styles.infoblockText}>
                  To manage alert groups in Direct Messages and verify users who are allowed to operate with MS Teams,
                  setup <PluginLink query={{ page: 'users', id: 'me' }}>personal MS Teams connection</PluginLink>
                </Text>
              </Stack>
            )}
          </Stack>
        </Block>
      )}

      {!onCallisAdded && (
        <Text type="secondary">
          1. Go to{' '}
          <a href="https://appsource.microsoft.com/en-us/product/office/WA200004307" target="_blank" rel="noreferrer">
            <Text type="link">MS Teams marketplace</Text>
          </a>{' '}
          and add <Text type="primary">Grafana IRM app</Text> to your MS Teams org workspace.{' '}
        </Text>
      )}
      <Text type="secondary">
        {!onCallisAdded ? 2 : 1}.{' '}
        {personalSettings ? (
          <Text type="secondary">
            Send a direct message to the Grafana IRM bot using <Text type="primary">⁠linkUser</Text> command with
            following code:
          </Text>
        ) : (
          <Text type="secondary">
            Add IRM bot to your team channel and send this code by <Text type="primary">@Grafana IRM linkTeam</Text>{' '}
            command
          </Text>
        )}
        <Field className={styles.fieldCommand}>
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
      <Block bordered withBackground className={styles.infoBlock}>
        <Text type="secondary">
          For more information please read{' '}
          <a href="https://grafana.com/docs/oncall/latest/notify/ms-teams/" target="_blank" rel="noreferrer">
            <Text type="link">OnCall documentation</Text>
          </a>
          .
        </Text>
      </Block>
      {!personalSettings && (
        <div className={styles.doneButton}>
          <Button onClick={handleMSTeamsGetChannels}>Done</Button>
        </div>
      )}
    </Stack>
  );
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    infoBlock: css`
      width: 752px;
      text-align: center;
      font-style: normal;
      font-weight: 400;
      font-size: 14px;
      line-height: 20px;
    `,

    fieldCommand: css`
      margin-top: 8px;
      width: 752px;

      input {
        font-weight: 400;
        font-size: 14px;
        line-height: 20px;
        color: ${theme.colors.primary.text};
      }
    `,

    infoblockText: css`
      margin-left: 48px;
      margin-right: 48px;
    `,

    doneButton: css`
      width: 752px;
      direction: rtl;
    `,
  };
};
