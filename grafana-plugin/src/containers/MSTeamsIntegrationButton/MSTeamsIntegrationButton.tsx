import React, { useCallback, useState, useEffect } from 'react';

import { Button, Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { MSTeamsInstructions } from 'containers/MSTeams/MSTeamsInstructions';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';

import styles from './MSTeamsIntegrationButton.module.css';

const cx = cn.bind(styles);

interface MSTeamsIntegrationProps {
  disabled?: boolean;
  size?: 'md' | 'lg';
  onUpdate: () => void;
}

export const MSTeamsIntegrationButton = observer((props: MSTeamsIntegrationProps) => {
  const { disabled, size = 'md', onUpdate } = props;

  const [showModal, setShowModal] = useState(false);

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
          Add MS Teams channel
        </Button>
      </WithPermissionControlTooltip>
      {showModal && <MSTeamsModal onHide={onInstallModalHideCallback} onUpdate={onModalUpdateCallback} />}
    </>
  );
});

interface MSTeamsModalProps {
  onHide: () => void;
  onUpdate: () => void;
}

const MSTeamsModal = (props: MSTeamsModalProps) => {
  const { onHide, onUpdate } = props;
  const [verificationCode, setVerificationCode] = useState<string>();
  const store = useStore();
  useEffect(() => {
    (async () => {
      const res = await store.msteamsChannelStore.getMSTeamsChannelVerificationCode();
      setVerificationCode(res);
    })();
  }, []);

  return (
    <Modal className={cx('msTeams-modal')} title="Connect MS Teams workspace" closeOnEscape isOpen onDismiss={onUpdate}>
      <MSTeamsInstructions onHide={onHide} verificationCode={verificationCode} onCallisAdded />
    </Modal>
  );
};
