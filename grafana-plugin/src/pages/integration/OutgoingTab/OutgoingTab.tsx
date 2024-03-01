import React from 'react';

import { useStyles2, Input, IconButton, Button, Drawer, Badge } from '@grafana/ui';
import { observer } from 'mobx-react';

import { CopyToClipboardIcon } from 'components/CopyToClipboardIcon/CopyToClipboardIcon';
import { IntegrationCollapsibleTreeView } from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { IntegrationTag } from 'components/Integrations/IntegrationTag';
import { useDrawer } from 'utils/hooks';

import { NewOutgoingWebhookDrawerContent } from './NewOutgoingWebhookDrawerContent';
import { OtherIntegrations } from './OtherIntegrations';
import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabDrawerKey } from './OutgoingTab.types';
import { OutgoingWebhookDetailsDrawerTabs } from './OutgoingWebhookDetailsDrawerTabs';
import { OutgoingWebhooksTable } from './OutgoingWebhooksTable';

export const OutgoingTab = () => {
  const { openDrawer, closeDrawer, getIsDrawerOpened } = useDrawer<OutgoingTabDrawerKey>();

  return (
    <>
      {getIsDrawerOpened('webhookDetails') && (
        <Drawer
          title="Outgoing webhook details"
          onClose={closeDrawer}
          width="640px"
          tabs={<OutgoingWebhookDetailsDrawerTabs closeDrawer={closeDrawer} />}
        >
          <div />
        </Drawer>
      )}
      {getIsDrawerOpened('newOutgoingWebhook') && (
        <Drawer title="New Outgoing Webhook" onClose={closeDrawer} width="640px">
          <NewOutgoingWebhookDrawerContent closeDrawer={closeDrawer} />
        </Drawer>
      )}
      <IntegrationCollapsibleTreeView
        configElements={[
          {
            customIcon: 'plug',
            startingElemPosition: '50%',
            expandedView: () => <Connection />,
          },
          {
            customIcon: 'plus',
            expandedView: () => (
              <>
                <Button onClick={() => openDrawer('newOutgoingWebhook')}>Add webhook</Button>
                <OutgoingWebhooksTable openDrawer={openDrawer} />
              </>
            ),
          },
          {
            customIcon: 'exchange-alt',
            startingElemPosition: '50%',
            expandedView: () => <OtherIntegrations />,
          },
        ]}
      />
    </>
  );
};

const Connection = observer(() => {
  const styles = useStyles2(getStyles);

  // TODO: bring back when backend ready
  // const integration = useCurrentIntegration();
  // const url = integration?.additional_settings?.instance_url;
  const url = 'https://example.com';

  return (
    <div>
      <IntegrationBlock
        noContent
        className={styles.urlIntegrationBlock}
        heading={
          <div className={styles.horizontalGroup}>
            <IntegrationTag>ServiceNow connection</IntegrationTag>
            <Badge text="OK" color="green" />
            <Input
              value={url}
              disabled
              className={styles.urlInput}
              suffix={
                <>
                  <CopyToClipboardIcon text={url} />
                  <IconButton
                    aria-label="Open in new tab"
                    name="external-link-alt"
                    onClick={() => window.open(url, '_blank')}
                  />
                </>
              }
            />
            <Button
              size="sm"
              icon="cog"
              tooltip="Open ServiceNow configuration"
              variant="secondary"
              name="cog"
              aria-label="Open ServiceNow configuration"
              className={styles.openConfigurationBtn}
            />
          </div>
        }
      />
      <h4>Outgoing webhooks</h4>
    </div>
  );
});
