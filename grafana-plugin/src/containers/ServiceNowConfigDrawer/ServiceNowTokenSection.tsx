import React, { useEffect, useState } from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, LoadingPlaceholder, VerticalGroup, useStyles2 } from '@grafana/ui';
import { observable } from 'mobx';

import { IntegrationInputField } from 'components/IntegrationInputField/IntegrationInputField';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { ActionKey } from 'models/loader/action-keys';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { useStore } from 'state/useStore';
import { useIsLoading } from 'utils/hooks';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';

export const ServiceNowTokenSection: React.FC = observable(() => {
  const styles = useStyles2(getStyles);
  const { id } = useCurrentIntegration();
  const { alertReceiveChannelStore } = useStore();
  const [isExistingToken, setIsExistingToken] = useState(undefined);
  const [currentToken, setCurrentToken] = useState(undefined);
  const isLoading = useIsLoading(ActionKey.UPDATE_SERVICENOW_TOKEN);

  useEffect(() => {
    (async function () {
      const hasToken = await alertReceiveChannelStore.hasServiceNowToken({ id });
      setIsExistingToken(hasToken);
    })();
  }, []);

  return (
    <VerticalGroup>
      <HorizontalGroup spacing="xs" align="center">
        <Text type="primary" strong>
          ServiceNow backsync API token
        </Text>
      </HorizontalGroup>

      <Text>
        Description for such object and{' '}
        <a href={'#'} target="_blank" rel="noreferrer">
          <Text type="link">link to documentation</Text>
        </a>
      </Text>

      <RenderConditionally shouldRender={isExistingToken === undefined}>
        <LoadingPlaceholder text="Loading..." />
      </RenderConditionally>

      <RenderConditionally shouldRender={isExistingToken !== undefined}>
        <div className={styles.tokenContainer}>
          <IntegrationInputField
            placeholder={
              currentToken
                ? ''
                : isExistingToken
                ? 'A token had already been generated'
                : 'Click Generate to create a token'
            }
            isButtonHeight
            inputClassName={styles.tokenInput}
            iconsClassName={styles.tokenIcons}
            value={currentToken}
            showExternal={false}
            showCopy={Boolean(currentToken)}
            showEye={false}
            isMasked={false}
          />
          <Button variant="secondary" onClick={onTokenGenerate} disabled={isLoading}>
            {isExistingToken ? 'Regenerate' : 'Generate'}
          </Button>
        </div>
      </RenderConditionally>
    </VerticalGroup>
  );

  async function onTokenGenerate() {
    const res = await alertReceiveChannelStore.generateServiceNowToken({ id });

    if (res?.token) {
      setCurrentToken(res.token);
    }
  }
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),
  };
};
