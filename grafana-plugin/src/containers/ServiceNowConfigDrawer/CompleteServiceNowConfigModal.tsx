import React, { useState } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Modal, useStyles2 } from '@grafana/ui';
import { FormProvider, useForm } from 'react-hook-form';

import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { useStore } from 'state/useStore';
import { OmitReadonlyMembers } from 'utils/types';
import { openNotification } from 'utils/utils';

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
  const { alertReceiveChannelStore } = useStore();
  const integration = useCurrentIntegration();

  const formMethods = useForm<FormFields>({
    values: {
      additional_settings: {
        ...integration.additional_settings,
      },
    },
  });

  const [isFormActionsDisabled, setIsFormActionsDisabled] = useState(false);

  const styles = useStyles2(getStyles);
  const { handleSubmit } = formMethods;

  const { id } = integration;

  return (
    <Modal
      closeOnEscape={false}
      closeOnBackdropClick={false}
      isOpen
      title={'Complete ServiceNow configuration'}
      onDismiss={onFormAcknowledge}
    >
      <FormProvider {...formMethods}>
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <div className={styles.scrollableContainer}>
            <div className={styles.border}>
              <ServiceNowStatusSection />
            </div>

            <div className={styles.border}>
              <ServiceNowTokenSection />
            </div>
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
        state_mapping: {
          ...formData.additional_settings.state_mapping,
        },
        is_configured: true,
      },
    };

    try {
      await alertReceiveChannelStore.update({ id, data });
      openNotification('You successfully completed your ServiceNow configuration');
      onHide();
    } finally {
      setIsFormActionsDisabled(false);
    }
  }
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),

    scrollableContainer: css`
      max-height: 60vh;
      overflow-y: auto;
      margin-bottom: 16px;

      @media (max-height: 764px) {
        max-height: 40vh;
      }
    `,
  };
};
