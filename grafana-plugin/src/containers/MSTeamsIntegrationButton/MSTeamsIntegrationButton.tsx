import React, { useCallback, useState, useEffect } from 'react';

import { css } from '@emotion/css';
import { Button, Modal, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { observer } from 'mobx-react';

import { MSTeamsInstructions } from 'containers/MSTeams/MSTeamsInstructions';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';

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
  const styles = useStyles2(getStyles);
  const store = useStore();
  useEffect(() => {
    (async () => {
      const res = await store.msteamsChannelStore.getMSTeamsChannelVerificationCode();
      setVerificationCode(res);
    })();
  }, []);

  return (
    <Modal className={styles.msteamsModal} title="Connect MS Teams workspace" closeOnEscape isOpen onDismiss={onUpdate}>
      <MSTeamsInstructions onHide={onHide} verificationCode={verificationCode} onCallisAdded />
    </Modal>
  );
};

const getStyles = () => {
  return {
    msteamsModal: css`
      min-width: 800px;
    `,
  };
};
