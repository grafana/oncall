import React from 'react';

import { useStyles2, Input, IconButton, Button, Drawer, useTheme2, Badge } from '@grafana/ui';

import CopyToClipboardIcon from 'components/CopyToClipboardIcon/CopyToClipboardIcon';
import { HamburgerContextMenu } from 'components/HamburgerContextMenu/HamburgerContextMenu';
import { IntegrationCollapsibleTreeView } from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { IntegrationTag } from 'components/Integrations/IntegrationTag';
import { Text } from 'components/Text/Text';
import { UserActions } from 'utils/authorization/authorization';
import { useDrawer } from 'utils/hooks';

import { OutgoingWebhookDetailsDrawerContent } from './OutgoingWebhookDetailsDrawerContent';
import { OutgoingWebhooksTable } from './OutgoingWebhooksTable';
import { NewEventTriggerDrawerContent } from './NewEventTriggerDrawerContent';
import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabDrawerKey } from './OutgoingTab.types';
import { UrlSettingsDrawerContent } from './UrlSettingsDrawerContent';
import { OtherIntegrationsTable } from './OtherIntegrationsTable';

export const OutgoingTab = () => {
  const { openDrawer, closeDrawer, getIsDrawerOpened } = useDrawer<OutgoingTabDrawerKey>();

  return (
    <>
      {getIsDrawerOpened('urlSettings') && (
        <Drawer title="Outgoing URL Settings" onClose={closeDrawer} width="640px">
          <UrlSettingsDrawerContent closeDrawer={closeDrawer} />
        </Drawer>
      )}
      {getIsDrawerOpened('triggerDetails') && (
        <Drawer title="Outgoing webhook details" onClose={closeDrawer} width="640px">
          <OutgoingWebhookDetailsDrawerContent closeDrawer={closeDrawer} />
        </Drawer>
      )}
      {getIsDrawerOpened('newEventTrigger') && (
        <Drawer title="New event trigger" onClose={closeDrawer} width="640px">
          <NewEventTriggerDrawerContent closeDrawer={closeDrawer} />
        </Drawer>
      )}
      <IntegrationCollapsibleTreeView
        configElements={[
          {
            customIcon: 'plug',
            startingElemPosition: '50%',
            expandedView: () => <Connection openDrawer={openDrawer} />,
          },
          {
            customIcon: 'plus',
            expandedView: () => (
              <>
                <AddOutgoingWebhook openDrawer={openDrawer} />
                <OutgoingWebhooksTable openDrawer={openDrawer} />
              </>
            ),
          },
          {
            customIcon: 'exchange-alt',
            startingElemPosition: '50%',
            expandedView: () => <OtherIntegrationsTable openDrawer={openDrawer} />,
          },
        ]}
      />
    </>
  );
};

const Connection = ({ openDrawer }: { openDrawer: (key: OutgoingTabDrawerKey) => void }) => {
  const styles = useStyles2(getStyles);
  const FAKE_URL = 'https://example.com';

  const value = FAKE_URL;

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
              value={value}
              disabled
              className={styles.urlInput}
              suffix={
                <>
                  <CopyToClipboardIcon text={FAKE_URL} />
                  <IconButton
                    aria-label="Open in new tab"
                    name="external-link-alt"
                    onClick={() => window.open(value, '_blank')}
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
              onClick={() => openDrawer('triggerDetails')}
              className={styles.openConfigurationBtn}
            />
          </div>
        }
      />
      <h4>Outgoing webhooks</h4>
    </div>
  );
};

const AddOutgoingWebhook = ({ openDrawer }: { openDrawer: (key: OutgoingTabDrawerKey) => void }) => (
  <Button onClick={() => openDrawer('newEventTrigger')}>Add webhook</Button>
);
