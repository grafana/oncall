import React, { forwardRef, useImperativeHandle, useState } from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { Alert, Button, HorizontalGroup, LoadingPlaceholder, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import { useFormContext } from 'react-hook-form';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { IntegrationFormFields } from 'containers/IntegrationForm/IntegrationForm';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { INTEGRATION_SERVICENOW } from 'utils/consts';
import { OmitReadonlyMembers } from 'utils/types';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';
import { ServiceNowFormFields } from './ServiceNowStatusSection';

export const ServiceNowAuthSection = observer(
  forwardRef(function ServiceNowAuthRef(_props, ref) {
    const { getValues } = useFormContext<ServiceNowFormFields | IntegrationFormFields>();

    const currentIntegration = useCurrentIntegration();
    const [isAuthTestRunning, setIsAuthTestRunning] = useState(false);
    const [authTestResult, setAuthTestResult] = useState<boolean>(undefined);
    const styles = useStyles2(getStyles);

    useImperativeHandle(ref, () => ({
      testConnection: onAuthTest,
    }));

    return (
      <div>
        <RenderConditionally shouldRender={!isAuthTestRunning && authTestResult !== undefined}>
          <Alert
            severity={authTestResult ? 'success' : 'error'}
            title={
              (
                <Text type="primary">{authTestResult ? 'Connection OK' : 'Connection failed'}</Text>
              ) as unknown as string
            }
          />
        </RenderConditionally>

        <HorizontalGroup>
          <Button className={''} variant="secondary" onClick={onAuthTest} disabled={isAuthTestRunning}>
            Test Connection
          </Button>
          <div>
            <RenderConditionally shouldRender={isAuthTestRunning}>
              <LoadingPlaceholder text="Loading..." className={styles.loader} />
            </RenderConditionally>
          </div>
        </HorizontalGroup>
      </div>
    );

    async function onAuthTest(): Promise<boolean> {
      const data: OmitReadonlyMembers<ApiSchemas['AlertReceiveChannel']> = {
        integration: currentIntegration ? currentIntegration.integration : INTEGRATION_SERVICENOW,
        ...getValues(),
      };

      setIsAuthTestRunning(true);
      const result = await AlertReceiveChannelHelper.testServiceNowAuthentication({ id: currentIntegration?.id, data });
      setAuthTestResult(result);
      setIsAuthTestRunning(false);

      return result;
    }
  })
);

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),
  };
};
