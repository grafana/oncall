import React, { useState } from 'react';
import { Drawer } from '@grafana/ui';
import { useForm } from 'react-hook-form';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { CommonServiceNowConfig, ServiceNowStatusMapping } from './CommonServiceNowConfig';

interface CompleteServiceNowConfigDrawerProps {
  onHide: () => void;
}

interface FormFields {
  additional_settings: ApiSchemas['AlertReceiveChannel']['additional_settings'];
}

export const CompleteServiceNowConfigDrawer: React.FC<CompleteServiceNowConfigDrawerProps> = ({ onHide }) => {
  const { handleSubmit } = useForm<FormFields>();
  const [statusMapping, setStatusMapping] = useState<ServiceNowStatusMapping>({});

  return (
    <Drawer title="Complete ServiceNow configuration" onClose={onHide} closeOnMaskClick={false} size="md">
      <form onSubmit={handleSubmit(onFormSubmit)}>
        <CommonServiceNowConfig statusMapping={statusMapping} setStatusMapping={setStatusMapping} />

        <div className={styles.border}>
          <VerticalGroup>
            <HorizontalGroup spacing="xs" align="center">
              <Text type="primary" size="small">
                ServiceNow API Token
              </Text>
              <Icon name="info-circle" />
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
                Regenerate
              </Button>
            </div>
          </VerticalGroup>
        </div>
      </form>
    </Drawer>
  );

  function onFormSubmit(data: FormFields) {}
};
