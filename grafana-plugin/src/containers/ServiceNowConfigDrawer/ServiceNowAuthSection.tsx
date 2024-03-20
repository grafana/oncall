import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Icon, LoadingPlaceholder, useStyles2 } from '@grafana/ui';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';
import { Text } from 'components/Text/Text';
import React, { useState } from 'react';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { ServiceNowFormFields } from './ServiceNowStatusSection';
import { useFormContext } from 'react-hook-form';
import { useStore } from 'state/useStore';
import { observer } from 'mobx-react';

export const ServiceNowAuthSection: React.FC = observer(() => {
  const { getValues } = useFormContext<ServiceNowFormFields>();
  const { alertReceiveChannelStore } = useStore();

  const currentIntegration = useCurrentIntegration();
  const [isAuthTestRunning, setIsAuthTestRunning] = useState(false);
  const [authTestResult, setAuthTestResult] = useState(undefined);
  const styles = useStyles2(getStyles);

  return (
    <HorizontalGroup>
      <Button className={''} variant="secondary" onClick={onAuthTest}>
        Test
      </Button>
      <div>
        <RenderConditionally shouldRender={isAuthTestRunning}>
          <LoadingPlaceholder text="Loading" className={styles.loader} />
        </RenderConditionally>

        <RenderConditionally shouldRender={!isAuthTestRunning && authTestResult !== undefined}>
          <HorizontalGroup align="center" justify="center">
            <Text type="primary">{authTestResult ? 'Connection OK' : 'Connection failed'}</Text>
            <Icon name={authTestResult ? 'check-circle' : 'x'} />
          </HorizontalGroup>
        </RenderConditionally>
      </div>
    </HorizontalGroup>
  );

  async function onAuthTest() {
    const data: Partial<ApiSchemas['AlertReceiveChannel']> = {
      integration: currentIntegration.integration,
      ...getValues(),
    };

    setIsAuthTestRunning(true);
    const result = await alertReceiveChannelStore.testServiceNowAuthentication({ data });
    setAuthTestResult(result);
    setIsAuthTestRunning(false);
  }
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),
  };
};
