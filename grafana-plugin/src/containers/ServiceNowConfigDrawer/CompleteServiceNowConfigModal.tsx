import React, { useState } from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Modal, useStyles2 } from '@grafana/ui';
import { FormProvider, useForm } from 'react-hook-form';

import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { useStore } from 'state/useStore';
import { OmitReadonlyMembers } from 'utils/types';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';
import { ServiceNowStatusSection } from './ServiceNowStatusSection';
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

  const [isFormActionsDisabled, setIsFormActionsDisabled] = useState(false);

  const styles = useStyles2(getStyles);
  const { handleSubmit } = formMethods;

  const { id } = integration;

  return (
    <Modal
      closeOnEscape={false}
      isOpen
      title={'Complete ServiceNow configuration'}
      onDismiss={() =>
        onFormAcknowledge().finally(() => {
          // onHide
        })
      }
    >
      <FormProvider {...formMethods}>
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <div className={styles.border}>
            <ServiceNowStatusSection />
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
                Proceed
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
            // use existing fields
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
    setIsFormActionsDisabled(true);

    const data: OmitReadonlyMembers<ApiSchemas['AlertReceiveChannel']> = {
      ...integration,
      ...formData,

      additional_settings: {
        ...integration.additional_settings,
        ...formData.additional_settings,
      },
    };

    try {
      await alertReceiveChannelStore.update({ id, data });
    } finally {
      setIsFormActionsDisabled(false);
    }
  }
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),
  };
};
