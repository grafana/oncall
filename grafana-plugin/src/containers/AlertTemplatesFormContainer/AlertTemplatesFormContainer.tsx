import React, { useCallback, useEffect, useState } from 'react';

import { observer } from 'mobx-react';

import AlertTemplatesForm from 'components/AlertTemplates/AlertTemplatesForm';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils';

interface TeamEditContainerProps {
  onHide: () => void;
  alertReceiveChannelId: AlertReceiveChannel['id'];
  alertGroupId?: Alert['pk'];
  onUpdate?: () => void;
  onUpdateTemplates?: () => void;
  visible?: boolean;
  selectedTemplateName?: string;
}

const AlertTemplatesFormContainer = observer((props: TeamEditContainerProps) => {
  const { alertReceiveChannelId, alertGroupId, onUpdateTemplates, selectedTemplateName } = props;

  const store = useStore();

  const [templatesRefreshing, setTemplatesRefreshing] = useState<boolean>(false);

  useEffect(() => {
    store.alertReceiveChannelStore.updateItem(alertReceiveChannelId);
    store.alertReceiveChannelStore.updateTemplates(alertReceiveChannelId, alertGroupId);
  }, [alertGroupId, alertReceiveChannelId, store]);

  const onUpdateTemplatesCallback = useCallback(
    (data) => {
      store.alertReceiveChannelStore
        .saveTemplates(alertReceiveChannelId, data)
        .then(() => {
          openNotification('Alert templates are successfully updated');
          if (onUpdateTemplates) {
            onUpdateTemplates();
          }
        })
        .catch((err) => {
          if (err.response?.data?.length > 0) {
            openErrorNotification(err.response.data);
          } else {
            openErrorNotification(err.message);
          }
        });
    },
    [alertReceiveChannelId, onUpdateTemplates, store.alertReceiveChannelStore]
  );

  const handleSendDemoAlertClickCallback = useCallback(() => {
    store.alertReceiveChannelStore.sendDemoAlert(alertReceiveChannelId).then(() => {
      setTemplatesRefreshing(true);
      store.alertReceiveChannelStore.updateTemplates(alertReceiveChannelId).then(() => {
        setTemplatesRefreshing(false);
      });
    });
  }, []);

  const templates = store.alertReceiveChannelStore.templates[alertReceiveChannelId];
  const alertReceiveChannel = store.alertReceiveChannelStore.items[alertReceiveChannelId];

  return (
    <AlertTemplatesForm
      alertReceiveChannelId={alertReceiveChannelId}
      alertGroupId={alertGroupId}
      templates={templates}
      onUpdateTemplates={onUpdateTemplatesCallback}
      demoAlertEnabled={alertReceiveChannel?.demo_alert_enabled}
      handleSendDemoAlertClick={handleSendDemoAlertClickCallback}
      templatesRefreshing={templatesRefreshing}
      selectedTemplateName={selectedTemplateName}
    />
  );
});

export default AlertTemplatesFormContainer;
