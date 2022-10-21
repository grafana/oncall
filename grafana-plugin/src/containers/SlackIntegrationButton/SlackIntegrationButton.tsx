import React, { useCallback, useState } from 'react';

import { Button, Modal } from '@grafana/ui';
import { observer } from 'mobx-react';

import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';

type Props = {
  className: string;
  disabled?: boolean;
};

const SlackIntegrationButton = observer(({ className, disabled }: Props) => {
  const [showModal, setShowModal] = useState<boolean>(false);

  const { slackStore, teamStore } = useStore();

  const onInstallModalCallback = useCallback(() => {
    setShowModal(true);
  }, []);

  const onInstallModalHideCallback = useCallback(() => {
    setShowModal(false);
  }, []);

  const onRemoveClickCallback = useCallback(() => {
    slackStore.removeSlackIntegration().then(() => {
      teamStore.loadCurrentTeam();
    });
  }, []);

  const onInstallClickCallback = useCallback(() => {
    slackStore.installSlackIntegration();
  }, []);

  if (teamStore.currentTeam?.slack_team_identity) {
    return (
      <WithPermissionControl userAction={UserAction.UpdateIntegrations}>
        <WithConfirm title="Are you sure to delete this Slack Integration?">
          <Button
            variant="destructive"
            size="md"
            icon="slack"
            className={className}
            disabled={disabled}
            onClick={onRemoveClickCallback}
          >
            Remove Slack Integration ({teamStore.currentTeam.slack_team_identity?.cached_name})
          </Button>
        </WithConfirm>
      </WithPermissionControl>
    );
  }

  return (
    <>
      <WithPermissionControl userAction={UserAction.UpdateIntegrations}>
        <Button
          size="lg"
          variant="primary"
          icon="slack"
          className={className}
          disabled={disabled}
          onClick={onInstallModalCallback}
        >
          Install Slack integration
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

const SlackModal = ({ onHide, onConfirm }: SlackModalProps) => (
  <Modal title="One more thing..." closeOnEscape isOpen onDismiss={onHide}>
    <div style={{ textAlign: 'center' }}>
      You can view your Slack Workspace at the top-right corner after you are redirected. It should be a Workspace with
      App Bot installed:
    </div>
    <img
      style={{ height: '350px', display: 'block', margin: '0 auto' }}
      src="public/plugins/grafana-oncall-app/img/slack_workspace_choose_attention.png"
    />
    <Button onClick={onConfirm}>I'll check! Proceed to Slack...</Button>
  </Modal>
);

export default SlackIntegrationButton;
