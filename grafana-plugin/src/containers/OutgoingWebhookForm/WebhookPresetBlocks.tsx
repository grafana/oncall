import React from 'react';

import { EmptySearchResult, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { IntegrationLogo } from 'components/IntegrationLogo/IntegrationLogo';
import { logoCoors } from 'components/IntegrationLogo/IntegrationLogo.config';
import { Text } from 'components/Text/Text';
import { getWebhookPresetIcons } from 'containers/OutgoingWebhookForm/WebhookPresetIcons.config';
import { OutgoingWebhookPreset } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';

import styles from 'containers/OutgoingWebhookForm/OutgoingWebhookForm.module.css';

const cx = cn.bind(styles);

export const WebhookPresetBlocks: React.FC<{
  presets: OutgoingWebhookPreset[];
  onBlockClick: (preset: OutgoingWebhookPreset) => void;
}> = observer(({ presets, onBlockClick }) => {
  const store = useStore();

  const webhookPresetIcons = getWebhookPresetIcons(store.features);

  return (
    <div className={cx('cards')} data-testid="create-outgoing-webhook-modal">
      {presets.length ? (
        presets.map((preset) => {
          let logo = <IntegrationLogo integration={{ value: 'webhook', display_name: preset.name }} scale={0.2} />;
          if (preset.logo in logoCoors) {
            logo = <IntegrationLogo integration={{ value: preset.logo, display_name: preset.name }} scale={0.2} />;
          } else if (preset.logo in webhookPresetIcons) {
            logo = webhookPresetIcons[preset.logo]();
          }
          return (
            <Block bordered hover shadowed onClick={() => onBlockClick(preset)} key={preset.id} className={cx('card')}>
              <div className={cx('card-bg')}>{logo}</div>
              <div className={cx('title')}>
                <VerticalGroup spacing="xs">
                  <HorizontalGroup>
                    <Text strong data-testid="webhook-preset-display-name">
                      {preset.name}
                    </Text>
                  </HorizontalGroup>
                  <Text type="secondary" size="small">
                    {preset.description}
                  </Text>
                </VerticalGroup>
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
