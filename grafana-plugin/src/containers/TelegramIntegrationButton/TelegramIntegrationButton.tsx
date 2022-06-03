import React, { useCallback, useState, useEffect } from 'react';

import { Button, Modal, Icon, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';
import { openNotification } from 'utils';

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

  const store = useStore();

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
      <WithPermissionControl userAction={UserAction.UpdateIntegrations}>
        <Button size={size} variant="primary" icon="plus" disabled={disabled} onClick={onInstallModalCallback}>
          Connect Telegram channel
        </Button>
      </WithPermissionControl>
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
  const { telegramChannelStore, userStore } = store;

  const [verificationCode, setVerificationCode] = useState<string>();
  const [botLink, setBotLink] = useState<string>();

  useEffect(() => {
    telegramChannelStore.getTelegramVerificationCode().then((res) => {
      setVerificationCode(res.telegram_code);
      setBotLink(res.bot_link);
    });
  }, []);

  return (
    <Modal title="Connect Telegram Channel" closeOnEscape isOpen onDismiss={onUpdate}>
      <div className={cx('telegram-instruction-container')}>
        <Text.Title level={5}>Follow these steps to create and connect to a dedicated OnCall channel.</Text.Title>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>
          If you already have a dedicated channel to use with OnCall, you can use the following activation code:{' '}
          <Text className={cx('verification-code')}>{verificationCode}</Text>
          <span className={cx('copy-icon')}>
            <CopyToClipboard
              text={verificationCode}
              onCopy={() => {
                openNotification('Verification code copied');
              }}
            >
              <Icon name="copy" />
            </CopyToClipboard>
          </span>
        </Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>1. Create a New Channel, and set it to Private.</Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>
          2. In <b>Manage Channel</b>, make sure <b>Sign messages</b> is enabled.
        </Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>3. Create a new discussion group. This group handles alert actions and comments.</Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>
          4. Add the discussion group to the channel. In <b>Manage Channel</b>, click <b>Discussion</b> to find and add
          the new group.
        </Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>
          5. Click{' '}
          <a className={cx('telegram-bot')} href={botLink} target="_blank">
            {botLink}
          </a>{' '}
          to add the OnCall bot to your contacts. Add the bot to your channel as an Admin. Allow it to{' '}
          <b>Post Messages</b>.
        </Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>6. Add the bot to the discussion group.</Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>
          7. Send the verification code, <Text className={cx('verification-code')}>{verificationCode}</Text>
          <span className={cx('copy-icon')}>
            <CopyToClipboard
              text={verificationCode}
              onCopy={() => {
                openNotification('Verification code copied');
              }}
            >
              <Icon name="copy" />
            </CopyToClipboard>
          </span>{' '}
          , to the channel.
        </Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>8. Make sure users connect to Telegram in their OnCall user profile.</Text>
      </div>

      <div className={cx('telegram-instruction-container')}>
        <Text>
          Each alert group notification is assigned a dedicated discussion. Users can perform notification actions
          (acknowledge, resolve, silence) and discuss alerts in the comments section of the discussions.
        </Text>
        <img
          style={{ height: '350px', display: 'block', margin: '20px auto' }}
          src="public/plugins/grafana-oncall-app/img/telegram_discussion.png"
        />
      </div>

      <div className={cx('telegram-instruction-cancel')}>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button variant="primary" onClick={onUpdate}>
            Done
          </Button>
        </HorizontalGroup>
      </div>
    </Modal>
  );
};

export default TelegramIntegrationButton;
