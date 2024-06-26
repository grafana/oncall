import React, { useCallback, useState, useEffect } from 'react';

import { Button, Modal, Icon, HorizontalGroup, VerticalGroup, Field, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { openNotification } from 'utils/utils';

import styles from './MattermostSetupButton.module.css'
const cx = cn.bind(styles)

interface MattermostSetupProps {
  disabled?: boolean;
  size?: 'md' | 'lg';
  onUpdate: () => void;
}

export const MattermostSetupButton = observer((props: MattermostSetupProps) => {
  const {disabled, size = 'md', onUpdate } = props;
  const [showModal, setShowModal] = useState<boolean>(false);
  const onSetupModalHideCallback = useCallback(() => {
    setShowModal(false);
  }, [])
  const onSetupModalCallback = useCallback(() => {
    setShowModal(true);
  }, [])
  const onModalUpdateCallback = useCallback(() => {
    setShowModal(false)
    onUpdate();
  }, [onUpdate]);

  return (
    <>
      <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
        <Button size={size} variant="primary" icon="plus" disabled={disabled} onClick={onSetupModalCallback}>
          Setup Mattermost
        </Button>
      </WithPermissionControlTooltip>
      {showModal && <MattermostModal onHide={onSetupModalHideCallback} onUpdate={onModalUpdateCallback} />}
    </>
    )
});

interface MattermostModalProps {
  onHide: () => void;
  onUpdate: () => void;
}

const MattermostModal = (props: MattermostModalProps) => {
  const { onHide, onUpdate } = props;
  const store = useStore();
  const { mattermostStore } = store

  const [manifestLink, setManifestLink] = useState<string>();

  useEffect(() => {
    (async () => {
      const res = await mattermostStore.getMattermostSetupDetails();
      setManifestLink(res.manifest_link);
    })();
  }, []);

  return (
    <Modal title="Setup Mattermost" closeOnEscape isOpen onDismiss={onUpdate}>
      <VerticalGroup spacing="md">
        <Text type="secondary">
          We need to install the Grafana OnCall app in our mattermost instance.
        </Text>
        <Text.Title level={5}>Install App</Text.Title>
        <Text type="secondary">
          1. Open Mattermost, Using Apps framework command type <Text type="primary">/apps install http [ManifestURL]</Text>
        </Text>
        <Text type="secondary">
          ManifestURL
          <Field className={cx('field-command')}>
            <Input
              id="mattermostManifestLink"
              value={manifestLink}
              suffix={
                <CopyToClipboard
                  text={manifestLink}
                  onCopy={() => {
                    openNotification('Link is copied')
                  }}
                >
                  <Icon name="copy"/>
                </CopyToClipboard>
              }
            />
          </Field>
        </Text>
        <Text type="secondary">
          2. Enable checkbox <Text type="primary">Agree to grant the app access to APIs and Locations</Text>
        </Text>
        <Text type="secondary">
          3. Choose <Text type="primary">Submit</Text>
        </Text>
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
