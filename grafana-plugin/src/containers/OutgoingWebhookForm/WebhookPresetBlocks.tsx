import React from 'react';

import { EmptySearchResult, Stack, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { IntegrationLogo } from 'components/IntegrationLogo/IntegrationLogo';
import { logoColors } from 'components/IntegrationLogo/IntegrationLogo.config';
import { Text } from 'components/Text/Text';
import { getWebhookPresetIcons } from 'containers/OutgoingWebhookForm/WebhookPresetIcons.config';
import { OutgoingWebhookPreset } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';

import { getWebhookFormStyles } from './OutgoingWebhookForm';

export const WebhookPresetBlocks: React.FC<{
  presets: OutgoingWebhookPreset[];
  onBlockClick: (preset: OutgoingWebhookPreset) => void;
}> = observer(({ presets, onBlockClick }) => {
  const store = useStore();
  const styles = useStyles2(getWebhookFormStyles);

  const webhookPresetIcons = getWebhookPresetIcons(store.features);

  return (
    <div className={styles.cards} data-testid="create-outgoing-webhook-modal">
      {presets.length ? (
        presets.map((preset) => {
          let logo = <IntegrationLogo integration={{ value: 'webhook', display_name: preset.name }} scale={0.2} />;
          if (preset.logo in logoColors) {
            logo = <IntegrationLogo integration={{ value: preset.logo, display_name: preset.name }} scale={0.2} />;
          } else if (preset.logo in webhookPresetIcons) {
            logo = webhookPresetIcons[preset.logo]();
          }
          return (
            <Block bordered hover shadowed onClick={() => onBlockClick(preset)} key={preset.id} className={styles.card}>
              <div>{logo}</div>
              <div className={styles.title}>
                <Stack direction="column" gap={StackSize.xs}>
                  <Stack>
                    <Text strong data-testid="webhook-preset-display-name">
                      {preset.name}
                    </Text>
                  </Stack>
                  <Text type="secondary" size="small">
                    {preset.description}
                  </Text>
                </Stack>
              </div>
            </Block>
          );
        })
      ) : (
        <EmptySearchResult>Could not find anything matching your query</EmptySearchResult>
      )}
    </div>
  );
});
