import React, { useCallback, useState, useEffect } from 'react';

import { Button, Modal, Icon, HorizontalGroup, VerticalGroup, Field, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';
import { UserActions } from 'utils/authorization';

import styles from './TelegramIntegrationButton.module.css';

const cx = cn.bind(styles);

interface TelegramIntegrationProps {
  disabled?: boolean;
  size?: 'md' | 'lg';
  onUpdate: () => void;
}

const TelegramIntegrationButton = observer((props: TelegramIntegrationProps) => {
  const { disabled, size = 'md', onUpdate } = props;

  const [showModal, setShowModal] = useState<boolean>(false);

  const onInstallModalHideCallback = useCallback(() => {
    setShowModal(false);
  }, []);

  const onInstallModalCallback = useCallback(() => {
    setShowModal(true);
  }, []);

  const onModalUpdateCallback = useCallback(() => {
    setShowModal(false);

    onUpdate();
  }, [onUpdate]);

  return (
    <>
      <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
        <Button size={size} variant="primary" icon="plus" disabled={disabled} onClick={onInstallModalCallback}>
          Add Telegram channel
        </Button>
      </WithPermissionControlTooltip>
      {showModal && <TelegramModal onHide={onInstallModalHideCallback} onUpdate={onModalUpdateCallback} />}
    </>
  );
});

interface TelegramModalProps {
  onHide: () => void;
  onUpdate: () => void;
}

const TelegramModal = (props: TelegramModalProps) => {
  const { onHide, onUpdate } = props;
  const store = useStore();
  const { telegramChannelStore } = store;

  const [verificationCode, setVerificationCode] = useState<string>();
  const [botLink, setBotLink] = useState<string>();

  useEffect(() => {
    telegramChannelStore.getTelegramVerificationCode().then((res) => {
      setVerificationCode(res.telegram_code);
      setBotLink(res.bot_link);
    });
  }, []);

  return (
    <Modal title="Adding Telegram Channel" closeOnEscape isOpen onDismiss={onUpdate}>
      <VerticalGroup spacing="md">
        <Block withBackground bordered className={cx('telegram-block')}>
          <Text type="secondary">
            If you already have a private channel to work with OnCall, use the following activation code:
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
        </Block>
        <Text.Title level={5}>Setup new channel</Text.Title>
        <Text type="secondary">
          1. Open Telegram, create a new <Text type="primary">Private Channel</Text> and enable{' '}
          <Text type="primary">Sign Messages</Text> in settings.
        </Text>
        <Text type="secondary">
          2. Create a new <Text type="primary">Discussion group</Text>. This group handles alert actions, comments and
          must be unique for each OnCall telegram channel.{' '}
        </Text>
        <Text type="secondary">
          3. Connect the discussion group with the channel. In <Text type="primary">Manage Channel</Text>, click{' '}
          <Text type="primary">Discussion</Text> to find and add the freshly created group.{' '}
        </Text>
        <Text type="secondary">
          4. Go to{' '}
          <a href={botLink} target="_blank" rel="noreferrer">
            <Text type="link">{botLink}</Text>
          </a>{' '}
          to add the OnCall bot to your contacts. Then add the bot to your channel as an{' '}
          <Text type="primary">Admin</Text> and allow it to <Text type="primary">Post Messages</Text>.
        </Text>
        <Text type="secondary">5. Add the bot to the discussion group.</Text>
        <Text type="secondary">
          6. Send this verification code to the channel and wait for the confirmation message:
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
        </Text>
        <Text type="secondary">7. Start to manage alerts in your team Telegram workspace.</Text>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button variant="primary" onClick={onUpdate}>
            Done
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
};

export default TelegramIntegrationButton;
