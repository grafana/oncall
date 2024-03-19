import React, { useEffect, useState } from 'react';

import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, LoadingPlaceholder, VerticalGroup, useStyles2 } from '@grafana/ui';

import { IntegrationInputField } from 'components/IntegrationInputField/IntegrationInputField';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { useStore } from 'state/useStore';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';

interface ServiceNowTokenSectionProps {}

export const ServiceNowTokenSection: React.FC<ServiceNowTokenSectionProps> = () => {
  const styles = useStyles2(getStyles);
  const { id } = useCurrentIntegration();
  const { alertReceiveChannelStore } = useStore();
  const [isExistingToken, setIsExistingToken] = useState(undefined);
  const [currentToken, setCurrentToken] = useState(undefined);

  useEffect(() => {
    (async function () {
      const hasToken = await alertReceiveChannelStore.hasServiceNowToken({ id });
      console.log({ hasToken });
      setIsExistingToken(hasToken);
    })();
  }, []);

  console.log({ currentToken });

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
            inputClassName={styles.tokenInput}
            iconsClassName={styles.tokenIcons}
            value={currentToken}
            showExternal={false}
            showCopy={Boolean(currentToken)}
            showEye={false}
            isMasked={false}
          />
          <Button variant="secondary" onClick={onTokenGenerate}>
            {isExistingToken ? 'Regenerate' : 'Generate'}
          </Button>
        </div>
      </RenderConditionally>
    </VerticalGroup>
  );

  async function onTokenGenerate() {
    const result = await alertReceiveChannelStore.generateServiceNowToken({ id });
    setCurrentToken(result.token);
  }
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),
  };
};
