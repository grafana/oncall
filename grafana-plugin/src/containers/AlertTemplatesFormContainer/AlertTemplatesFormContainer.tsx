import React, { useCallback, useEffect, useState } from 'react';

import { observer } from 'mobx-react';

import AlertTemplatesForm from 'components/AlertTemplates/AlertTemplatesForm';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';

interface TeamEditContainerProps {
  onHide: () => void;
  alertReceiveChannelId: AlertReceiveChannel['id'];
  alertGroupId?: Alert['pk'];
  onUpdate?: () => void;
  onUpdateTemplates?: () => void;
  visible?: boolean;
  selectedTemplateName?: string;
}

const AlertTemplatesFormContainer = observer(
  ({ alertReceiveChannelId, alertGroupId, onUpdateTemplates, selectedTemplateName }: TeamEditContainerProps) => {
    const { alertReceiveChannelStore } = useStore();

    const [templatesRefreshing, setTemplatesRefreshing] = useState<boolean>(false);
    const [errors, setErrors] = useState({});

    useEffect(() => {
      alertReceiveChannelStore.updateItem(alertReceiveChannelId);
      alertReceiveChannelStore.updateTemplates(alertReceiveChannelId, alertGroupId);
    }, [alertGroupId, alertReceiveChannelId, alertReceiveChannelStore]);

    const onUpdateTemplatesCallback = useCallback(
      (data) => {
        alertReceiveChannelStore
          .saveTemplates(alertReceiveChannelId, data)
          .then(() => {
            openNotification('Alert templates are successfully updated');
            if (onUpdateTemplates) {
              onUpdateTemplates();
            }
          })
          .catch((data) => {
            setErrors(data.response.data);
          });
      },
      [alertReceiveChannelId, onUpdateTemplates, alertReceiveChannelStore]
    );

    const handleSendDemoAlertClickCallback = useCallback(() => {
      alertReceiveChannelStore.sendDemoAlert(alertReceiveChannelId).then(() => {
        setTemplatesRefreshing(true);
        alertReceiveChannelStore.updateTemplates(alertReceiveChannelId).then(() => {
          setTemplatesRefreshing(false);
        });
      });
    }, []);

    const templates = alertReceiveChannelStore.templates[alertReceiveChannelId];
    const alertReceiveChannel = alertReceiveChannelStore.items[alertReceiveChannelId];

    return (
      <AlertTemplatesForm
        alertReceiveChannelId={alertReceiveChannelId}
        alertGroupId={alertGroupId}
        errors={errors}
        templates={templates}
        onUpdateTemplates={onUpdateTemplatesCallback}
        demoAlertEnabled={alertReceiveChannel?.demo_alert_enabled}
        handleSendDemoAlertClick={handleSendDemoAlertClickCallback}
        templatesRefreshing={templatesRefreshing}
        selectedTemplateName={selectedTemplateName}
      />
    );
  }
);

export default AlertTemplatesFormContainer;
