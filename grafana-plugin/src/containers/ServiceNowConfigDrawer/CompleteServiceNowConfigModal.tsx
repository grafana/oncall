import React, { useState } from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, LoadingPlaceholder, Modal, useStyles2 } from '@grafana/ui';
import { FormProvider, useForm } from 'react-hook-form';

import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { useStore } from 'state/useStore';
import { OmitReadonlyMembers } from 'utils/types';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';
import { ServiceNowStatusSection, ServiceNowStatusMapping } from './ServiceNowStatusSection';
import { ServiceNowTokenSection } from './ServiceNowTokenSection';

interface CompleteServiceNowConfigModalProps {
  onHide: () => void;
}

interface FormFields {
  additional_settings: ApiSchemas['AlertReceiveChannel']['additional_settings'];
}

export const CompleteServiceNowModal: React.FC<CompleteServiceNowConfigModalProps> = ({ onHide }) => {
  const formMethods = useForm<FormFields>();
  const { alertReceiveChannelStore } = useStore();
  const integration = useCurrentIntegration();

  const [statusMapping, setStatusMapping] = useState<ServiceNowStatusMapping>({});
  const [isFormActionsDisabled, setIsFormActionsDisabled] = useState(false);

  const styles = useStyles2(getStyles);
  const { handleSubmit } = formMethods;

  const { id } = integration;

  return (
    <Modal closeOnEscape={false} isOpen title={'Complete ServiceNow configuration'} onDismiss={onHide} className={''}>
      <FormProvider {...formMethods}>
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <div className={styles.border}>
            <ServiceNowStatusSection statusMapping={statusMapping} setStatusMapping={setStatusMapping} />
          </div>

          <div className={styles.border}>
            <ServiceNowTokenSection />
          </div>

          <div>
            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={onFormAcknowledge} disabled={isFormActionsDisabled}>
                Close
              </Button>
              <Button variant="primary" type="submit" disabled={isFormActionsDisabled}>
                {isFormActionsDisabled ? <LoadingPlaceholder className={styles.loader} text="Loading..." /> : 'Proceed'}
              </Button>
            </HorizontalGroup>
          </div>
        </form>
      </FormProvider>
    </Modal>
  );

  async function onFormAcknowledge() {
    setIsFormActionsDisabled(true);

    try {
      await alertReceiveChannelStore.update({
        id,
        data: {
          ...integration,
          additional_settings: {
            ...integration.additional_settings,
            is_configured: true,
          },
        },
      });

      onHide();
    } catch (ex) {
      setIsFormActionsDisabled(false);
    }
  }

  async function onFormSubmit(formData: FormFields) {
    const data: OmitReadonlyMembers<ApiSchemas['AlertReceiveChannel']> = {
      ...integration,
      ...formData,
    };

    await alertReceiveChannelStore.update({ id, data });
  }
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),
  };
};
