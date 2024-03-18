import React, { useState } from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Icon, LoadingPlaceholder, Modal, VerticalGroup, useStyles2 } from '@grafana/ui';
import { FormProvider, useForm } from 'react-hook-form';

import { IntegrationInputField } from 'components/IntegrationInputField/IntegrationInputField';
import { Text } from 'components/Text/Text';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';
import { ServiceNowStatusSection, ServiceNowStatusMapping } from './ServiceNowStatusSection';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';

interface CompleteServiceNowConfigModalProps {
  onHide: () => void;
}

interface FormFields {
  additional_settings: ApiSchemas['AlertReceiveChannel']['additional_settings'];
}

export const CompleteServiceNowModal: React.FC<CompleteServiceNowConfigModalProps> = ({ onHide }) => {
  const formMethods = useForm<FormFields>();
  const { handleSubmit } = formMethods;
  const { alertReceiveChannelStore } = useStore();
  const integration = useCurrentIntegration();
  const [statusMapping, setStatusMapping] = useState<ServiceNowStatusMapping>({});
  const [isFormActionsDisabled, setIsFormActionsDisabled] = useState(false);

  const styles = useStyles2(getStyles);
  const serviceNowAPIToken = ''; // TODO
  const onTokenRegenerate = () => {}; // TODO

  return (
    <Modal closeOnEscape={false} isOpen title={'Complete ServiceNow configuration'} onDismiss={onHide} className={''}>
      <FormProvider {...formMethods}>
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <div className={styles.border}>
            <ServiceNowStatusSection statusMapping={statusMapping} setStatusMapping={setStatusMapping} />
          </div>

          <div className={styles.border}>
            <VerticalGroup>
              <HorizontalGroup spacing="xs" align="center">
                <Text type="primary" strong>
                  Generate backsync API token
                </Text>
              </HorizontalGroup>

              <Text>
                Description for such object and{' '}
                <a href={'#'} target="_blank" rel="noreferrer">
                  <Text type="link">link to documentation</Text>
                </a>
              </Text>

              <div className={styles.tokenContainer}>
                <IntegrationInputField
                  inputClassName={styles.tokenInput}
                  iconsClassName={styles.tokenIcons}
                  value={serviceNowAPIToken}
                  showExternal={false}
                  isMasked
                />
                <Button variant="secondary" onClick={onTokenRegenerate}>
                  {serviceNowAPIToken ? 'Regenerate' : 'Generate'}
                </Button>
              </div>
            </VerticalGroup>
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

  function onFormAcknowledge() {
    setIsFormActionsDisabled(true);

    try {
      alertReceiveChannelStore.update({
        id: integration.id,
        data: {
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

  function onFormSubmit(data: FormFields) {
    // alertReceiveChannelStore.update({ id, data, skipErrorHandling: false })
  }
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),
  };
};
