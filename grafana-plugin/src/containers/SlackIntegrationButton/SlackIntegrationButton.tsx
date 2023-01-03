import React, { useCallback, useState } from 'react';

import { Button, Modal } from '@grafana/ui';
import { observer } from 'mobx-react';

import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

const SlackIntegrationButton = observer((props: { className: string; disabled?: boolean }) => {
  const { className, disabled } = props;

  const [showModal, setShowModal] = useState<boolean>(false);

  const store = useStore();

  const onInstallModalCallback = useCallback(() => {
    setShowModal(true);
  }, []);

  const onInstallModalHideCallback = useCallback(() => {
    setShowModal(false);
  }, []);

  const onRemoveClickCallback = useCallback(() => {
    store.slackStore.removeSlackIntegration().then(() => {
      store.teamStore.loadCurrentTeam();
    });
  }, []);

  const onInstallClickCallback = useCallback(() => {
    store.slackStore.installSlackIntegration();
  }, []);

  if (store.teamStore.currentTeam?.slack_team_identity) {
    return (
      <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
        <WithConfirm title="Are you sure to delete this Slack Integration?">
          <Button
            variant="destructive"
            size="md"
            icon="slack"
            className={className}
            disabled={disabled}
            onClick={onRemoveClickCallback}
          >
            Remove Slack Integration ({store.teamStore.currentTeam.slack_team_identity?.cached_name})
          </Button>
        </WithConfirm>
      </WithPermissionControl>
    );
  }

  return (
    <>
      <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
        <Button
          size="lg"
          variant="primary"
          icon="slack"
          className={className}
          disabled={disabled}
          onClick={onInstallModalCallback}
        >
          Connect Slack
        </Button>
      </WithPermissionControl>
      {showModal && <SlackModal onHide={onInstallModalHideCallback} onConfirm={onInstallClickCallback} />}
    </>
  );
});

interface SlackModalProps {
  onHide: () => void;
  onConfirm: () => void;
}

const SlackModal = (props: SlackModalProps) => {
  const { onHide, onConfirm } = props;

  return (
    <Modal title="Slack connection" closeOnEscape isOpen onDismiss={onHide}>
      <div style={{ textAlign: 'left' }}>
        You can view your Slack Workspace at the top-right corner after you are redirected. It should be a Workspace
        with App Bot installed:
      </div>
      <img
        style={{ height: '350px', display: 'block', margin: '0 auto' }}
        src="public/plugins/grafana-oncall-app/img/slack_workspace_choose_attention.png"
      />
      <Button onClick={onConfirm}>I'll check! Proceed to Slack...</Button>
    </Modal>
  );
};

export default SlackIntegrationButton;
