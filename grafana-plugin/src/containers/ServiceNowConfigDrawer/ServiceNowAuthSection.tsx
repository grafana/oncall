import React, { useState } from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Icon, LoadingPlaceholder, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import { useFormContext } from 'react-hook-form';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { IntegrationFormFields } from 'containers/IntegrationForm/IntegrationForm';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { OmitReadonlyMembers } from 'utils/types';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';
import { ServiceNowFormFields } from './ServiceNowStatusSection';

export const ServiceNowAuthSection: React.FC = observer(() => {
  const { getValues } = useFormContext<ServiceNowFormFields | IntegrationFormFields>();

  const currentIntegration = useCurrentIntegration();
  const [isAuthTestRunning, setIsAuthTestRunning] = useState(false);
  const [authTestResult, setAuthTestResult] = useState<boolean>(undefined);
  const styles = useStyles2(getStyles);

  return (
    <div>
      <HorizontalGroup>
        <Button className={''} variant="secondary" onClick={onAuthTest}>
          Test
        </Button>
        <div>
          <RenderConditionally shouldRender={isAuthTestRunning}>
            <LoadingPlaceholder text="Loading..." className={styles.loader} />
          </RenderConditionally>

          <RenderConditionally shouldRender={!isAuthTestRunning && authTestResult !== undefined}>
            <HorizontalGroup align="center" justify="center">
              <Text type="primary">{authTestResult ? 'Connection OK' : 'Connection failed'}</Text>
              <Icon name={authTestResult ? 'check-circle' : 'x'} />
            </HorizontalGroup>
          </RenderConditionally>
        </div>
      </HorizontalGroup>
    </div>
  );

  async function onAuthTest() {
    const data: OmitReadonlyMembers<ApiSchemas['AlertReceiveChannel']> = {
      integration: currentIntegration ? currentIntegration.integration : 'servicenow',
      ...getValues(),
    };

    setIsAuthTestRunning(true);
    const result = await AlertReceiveChannelHelper.testServiceNowAuthentication({ data });
    setAuthTestResult(result);
    setIsAuthTestRunning(false);
  }
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),
  };
};
