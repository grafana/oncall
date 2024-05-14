import React, { useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Input, LoadingPlaceholder, VerticalGroup, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { SourceCode } from 'components/SourceCode/SourceCode';
import { Text } from 'components/Text/Text';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ActionKey } from 'models/loader/action-keys';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { DOCS_ROOT } from 'utils/consts';
import { useIsLoading } from 'utils/hooks';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';

interface TokenData {
  token: string;
  usage: string;
}

interface ServiceNowTokenSectionProps {
  isDrawer?: boolean;
}

export const ServiceNowTokenSection: React.FC<ServiceNowTokenSectionProps> = observer(({ isDrawer }) => {
  const styles = useStyles2(getStyles);
  const { id } = useCurrentIntegration();
  const [isExistingToken, setIsExistingToken] = useState(undefined);
  const [tokenData, setTokenData] = useState<TokenData>(undefined);
  const isLoading = useIsLoading(ActionKey.UPDATE_SERVICENOW_TOKEN);

  useEffect(() => {
    (async function () {
      const hasToken = await AlertReceiveChannelHelper.checkIfServiceNowHasToken({ id });
      setIsExistingToken(hasToken);
    })();
  }, []);

  return (
    <VerticalGroup>
      <HorizontalGroup spacing="xs" align="center">
        <Text type="primary" strong>
          Generate ServiceNow Business Rule
        </Text>
      </HorizontalGroup>

      <Text>
        Copy and paste the following script to ServiceNow to allow communication between ServiceNow and OnCall{' '}
        <a
          href={`${DOCS_ROOT}/integrations/servicenow/#generate-business-rule-script`}
          target="_blank"
          rel="noreferrer"
        >
          <Text type="link">Read more</Text>
        </a>
      </Text>

      <RenderConditionally shouldRender={isExistingToken === undefined}>
        <LoadingPlaceholder text="Loading..." />
      </RenderConditionally>

      <RenderConditionally shouldRender={isExistingToken !== undefined}>
        <VerticalGroup>
          <div className={styles.tokenContainer}>
            <RenderConditionally shouldRender={!tokenData}>
              <Input
                disabled
                placeholder={isExistingToken ? 'A script had already been generated' : 'Click to generate script'}
              />
            </RenderConditionally>

            <RenderConditionally shouldRender={tokenData !== undefined}>
              <SourceCode rootClassName={styles.sourceCodeEl} noMaxHeight={!isDrawer} showClipboardIconOnly>
                {tokenData?.usage}
              </SourceCode>
            </RenderConditionally>
          </div>

          {renderGenerateButton()}
        </VerticalGroup>
      </RenderConditionally>
    </VerticalGroup>
  );

  function renderGenerateButton() {
    return (
      <Button variant="secondary" onClick={onTokenGenerate} disabled={isLoading} className={'aaaa'}>
        {isExistingToken ? 'Regenerate' : 'Generate'}
      </Button>
    );
  }

  async function onTokenGenerate() {
    const res = await AlertReceiveChannelHelper.generateServiceNowToken({ id });

    if (res?.token) {
      setTokenData(res);
    }
  }
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),

    sourceCodeEl: css`
      pre {
        max-height: 200px;
        padding-top: 0;
        margin-bottom: 0;
      }
    `,
  };
};
