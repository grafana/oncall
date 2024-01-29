import React from 'react';

import { useStyles2, Input, IconButton, Button, Drawer } from '@grafana/ui';

import CopyToClipboardIcon from 'components/CopyToClipboardIcon/CopyToClipboardIcon';
import HamburgerContextMenu from 'components/HamburgerContextMenu/HamburgerContextMenu';
import IntegrationCollapsibleTreeView from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import IntegrationTag from 'components/Integrations/IntegrationTag';
import Text from 'components/Text/Text';
import { UserActions } from 'utils/authorization';
import { useDrawerState } from 'utils/hooks';

import { EventTriggerDetailsDrawerContent } from './EventTriggerDetailsDrawerContent';
import { EventTriggersTable } from './EventTriggersTable';
import { NewEventTriggerDrawerContent } from './NewEventTriggerDrawerContent';
import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabDrawerKey } from './OutgoingTab.types';
import { UrlSettingsDrawerContent } from './UrlSettingsDrawerContent';

const OutgoingTab = () => {
  const { openDrawer, closeDrawer, getIsDrawerOpened } = useDrawerState<OutgoingTabDrawerKey>();

  return (
    <>
      {getIsDrawerOpened('urlSettings') && (
        <Drawer title="Outgoing URL Settings" onClose={closeDrawer} width="640px">
          <UrlSettingsDrawerContent closeDrawer={closeDrawer} />
        </Drawer>
      )}
      {getIsDrawerOpened('triggerDetails') && (
        <Drawer title="Event trigger details" onClose={closeDrawer} width="640px">
          <EventTriggerDetailsDrawerContent closeDrawer={closeDrawer} />
        </Drawer>
      )}
      {getIsDrawerOpened('newEventTrigger') && (
        <Drawer title="New event trigger" onClose={closeDrawer} width="640px">
          <NewEventTriggerDrawerContent closeDrawer={closeDrawer} />
        </Drawer>
      )}
      <IntegrationCollapsibleTreeView
        configElements={[
          { customIcon: 'plug', expandedView: () => <Url openDrawer={openDrawer} /> },
          {
            customIcon: 'plus',
            expandedView: () => <AddEventTrigger openDrawer={openDrawer} />,
          },
        ]}
      />
      <EventTriggersTable openDrawer={openDrawer} />
    </>
  );
};

const Url = ({ openDrawer }: { openDrawer: (key: OutgoingTabDrawerKey) => void }) => {
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
            <IntegrationTag>ServiceNow URL</IntegrationTag>
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
            <HamburgerContextMenu
              items={[
                {
                  onClick: () => openDrawer('urlSettings'),
                  label: 'URL Settings',
                  requiredPermission: UserActions.IntegrationsWrite,
                },
              ]}
              hamburgerIconClassName={styles.hamburgerIcon}
            />
          </div>
        }
      />
      <h4>Outgoing events</h4>
      <div>
        <Text type="secondary">Webhooks managed by this integration.</Text>
      </div>
    </div>
  );
};

const AddEventTrigger = ({ openDrawer }: { openDrawer: (key: OutgoingTabDrawerKey) => void }) => {
  const styles = useStyles2(getStyles);

  return (
    <Button onClick={() => openDrawer('newEventTrigger')} className={styles.addEventTriggerBtn}>
      Add Event Trigger
    </Button>
  );
};

export default OutgoingTab;
