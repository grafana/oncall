import React, { useState } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2, Input, IconButton, Button } from '@grafana/ui';

import CopyToClipboardIcon from 'components/CopyToClipboardIcon/CopyToClipboardIcon';
import HamburgerContextMenu from 'components/HamburgerContextMenu/HamburgerContextMenu';
import IntegrationCollapsibleTreeView from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import IntegrationTag from 'components/Integrations/IntegrationTag';
import Text from 'components/Text/Text';

const OutgoingTab = () => {
  return (
    <IntegrationCollapsibleTreeView
      configElements={[
        { customIcon: 'plug', expandedView: () => <Url /> },
        {
          customIcon: 'plus',
          expandedView: () => <AddEventTrigger />,
        },
      ]}
    />
  );
};

const Url = () => {
  const styles = useStyles2(getStyles);
  const FAKE_URL = 'https://example.com';

  const [isInputMasked, setIsInputMasked] = useState(true);

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
              value={isInputMasked ? value?.replace(/./g, '*') : value}
              disabled
              className={styles.urlInput}
              suffix={
                <>
                  <IconButton
                    aria-label="Reveal"
                    name="eye"
                    onClick={() => setIsInputMasked((isMasked) => !isMasked)}
                  />
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
              items={[<div key="url">URL Settings</div>]}
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

const AddEventTrigger = () => {
  const styles = useStyles2(getStyles);

  return (
    <Button onClick={() => {}} className={styles.addEventTriggerBtn}>
      Add Event Trigger
    </Button>
  );
};

export const getStyles = (theme: GrafanaTheme2) => ({
  urlIntegrationBlock: css({
    marginBottom: '32px',
  }),
  urlInput: css({
    height: '25px',
    background: theme.colors.background.canvas,
    '& input': {
      height: '25px',
    },
  }),
  hamburgerIcon: css({
    background: theme.colors.secondary.shade,
  }),
  horizontalGroup: css({
    display: 'flex',
    gap: '8px',
  }),
  addEventTriggerBtn: css({
    marginTop: '16px',
  }),
});

export default OutgoingTab;
