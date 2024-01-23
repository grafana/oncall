import IntegrationCollapsibleTreeView from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import React, { FC, useState } from 'react';
import { css } from '@emotion/css';
import { Tab, TabsBar, TabContent, useStyles2, Input, Icon, IconButton, HorizontalGroup } from '@grafana/ui';
import LocationHelper from 'utils/LocationHelper';
import cn from 'classnames';
import CopyToClipboard from 'react-copy-to-clipboard';
import CopyToClipboardIcon from 'components/CopyToClipboardIcon/CopyToClipboardIcon';
import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import IntegrationTag from 'components/Integrations/IntegrationTag';

interface OutgoingTabProps {}

const OutgoingTab: FC<OutgoingTabProps> = (props) => {
  const styles = useStyles2(getStyles);

  return (
    <>
      <IntegrationCollapsibleTreeView
        configElements={[
          { customIcon: 'plug', expandedView: () => <Url /> },
          { customIcon: 'plus', expandedView: () => <div>sss</div> },
        ]}
      />
      outgoing tabsssa
    </>
  );
};

const Url = () => {
  const FAKE_URL = 'https://example.com';

  const [isInputMasked, setIsInputMasked] = useState(true);

  const value = FAKE_URL;

  return (
    <div>
      <IntegrationBlock
        noContent
        heading={
          <HorizontalGroup>
            <IntegrationTag>ServiceNow URL</IntegrationTag>
            <Input
              value={isInputMasked ? value?.replace(/./g, '*') : value}
              disabled
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
          </HorizontalGroup>
        }
      />
    </div>
  );
};

export const getStyles = () => ({
  url: css({
    paddingBottom: '46px',
  }),
});

export default OutgoingTab;
