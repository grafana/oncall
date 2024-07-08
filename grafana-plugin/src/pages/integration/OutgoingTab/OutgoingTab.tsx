import React from 'react';

import { useStyles2, Input, IconButton, Drawer, HorizontalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';

import { Button } from 'components/Button/Button';
import { CopyToClipboardIcon } from 'components/CopyToClipboardIcon/CopyToClipboardIcon';
import { IntegrationCollapsibleTreeView } from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { IntegrationTag } from 'components/Integrations/IntegrationTag';
import { Text } from 'components/Text/Text';
import { useDrawer } from 'utils/hooks';

import { NewOutgoingWebhookDrawerContent } from './NewOutgoingWebhookDrawerContent';
import { OtherIntegrations } from './OtherIntegrations';
import { useCurrentIntegration } from './OutgoingTab.hooks';
import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabDrawerKey } from './OutgoingTab.types';
import { OutgoingWebhookDetailsDrawerTabs } from './OutgoingWebhookDetailsDrawerTabs';
import { OutgoingWebhooksTable } from './OutgoingWebhooksTable';

export const OutgoingTab = ({ openSnowConfigurationDrawer }: { openSnowConfigurationDrawer: () => void }) => {
  const { openDrawer, closeDrawer, getIsDrawerOpened } = useDrawer<OutgoingTabDrawerKey>();
  const styles = useStyles2(getStyles);

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
            expandedView: () => <Connection openSnowConfigurationDrawer={openSnowConfigurationDrawer} />,
          },
          {
            customIcon: 'plus',
            expandedView: () => (
              <>
                <Button onClick={() => openDrawer('newOutgoingWebhook')}>Add webhook</Button>
                <OutgoingWebhooksTable
                  openDrawer={openDrawer}
                  noItemsInfo={
                    <div className={styles.noWebhooksInfo}>
                      <HorizontalGroup>
                        <Text type="secondary">There are no webhooks.</Text>
                        <Button variant="primary" showAsLink onClick={() => openDrawer('newOutgoingWebhook')}>
                          Add one
                        </Button>
                      </HorizontalGroup>
                    </div>
                  }
                />
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

const Connection = observer(({ openSnowConfigurationDrawer }: { openSnowConfigurationDrawer: () => void }) => {
  const styles = useStyles2(getStyles);
  const integration = useCurrentIntegration();
  // TODO: remove casting once backend narrows down the types
  const url = integration?.additional_settings?.instance_url as string;

  return (
    <div>
      <IntegrationBlock
        noContent
        className={styles.urlIntegrationBlock}
        heading={
          <div className={styles.horizontalGroup}>
            <IntegrationTag>ServiceNow connection</IntegrationTag>
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
              onClick={openSnowConfigurationDrawer}
            />
          </div>
        }
      />
      <h4>Outgoing webhooks</h4>
    </div>
  );
});
