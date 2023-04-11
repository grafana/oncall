import React, { useCallback, useEffect, useState } from 'react';

import { Drawer, Tab, TabContent, TabsBar, Button, VerticalGroup, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';

import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import Text from 'components/Text/Text';
import AlertTemplatesFormContainer from 'containers/AlertTemplatesFormContainer/AlertTemplatesFormContainer';
import HeartbeatForm from 'containers/HeartbeatModal/HeartbeatForm';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';
import LocationHelper from 'utils/LocationHelper';

import { IntegrationSettingsTab } from './IntegrationSettings.types';
import Autoresolve from './parts/Autoresolve';

import styles from 'containers/IntegrationSettings/IntegrationSettings.module.css';

const cx = cn.bind(styles);

interface IntegrationSettingsProps {
  id: AlertReceiveChannel['id'];
  alertGroupId?: Alert['pk'];
  startTab?: IntegrationSettingsTab;
  onHide: () => void;
  onUpdate?: () => void;
  onUpdateTemplates?: () => void;
}

const IntegrationSettings = observer((props: IntegrationSettingsProps) => {
  const { id, onHide, onUpdate, onUpdateTemplates, startTab, alertGroupId } = props;
  const [activeTab, setActiveTab] = useState<IntegrationSettingsTab>(startTab || IntegrationSettingsTab.Templates);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const store = useStore();

  const { alertReceiveChannelStore } = store;

  const alertReceiveChannel = alertReceiveChannelStore.items[id];

  const getTabClickHandler = useCallback((tab: IntegrationSettingsTab) => {
    return () => {
      setActiveTab(tab);
      LocationHelper.update({ tab }, 'partial');
    };
  }, []);

  useEffect(() => {
    alertReceiveChannelStore.updateItem(id);
  }, []);

  const integration = alertReceiveChannelStore.getIntegration(alertReceiveChannel);

  const [expanded, _setExpanded] = useState(false);

  const handleSwitchToTemplate = (templateName: string) => {
    setActiveTab(IntegrationSettingsTab.Templates);
    setSelectedTemplate(templateName);
  };

  return (
    <Drawer
      scrollableContent
      expandable
      title={
        <div className={cx('title')}>
          {integration && <IntegrationLogo integration={integration} scale={0.2} />}
          <div className={cx('title-column')}>
            {alertReceiveChannel && (
              <Text.Title level={4}>
                <Emoji text={alertReceiveChannel.verbal_name} /> settings
              </Text.Title>
            )}
            {integration && <Text type="secondary">Type: {integration.display_name}</Text>}
          </div>
        </div>
      }
      width={expanded ? '100%' : '70%'}
      onClose={onHide}
    >
      <TabsBar>
        <Tab
          active={activeTab === IntegrationSettingsTab.HowToConnect}
          label="How to connect"
          key={IntegrationSettingsTab.HowToConnect}
          onChangeTab={getTabClickHandler(IntegrationSettingsTab.HowToConnect)}
        />
        <Tab
          active={activeTab === IntegrationSettingsTab.Templates}
          label="Alert Templates"
          key={IntegrationSettingsTab.Templates}
          onChangeTab={getTabClickHandler(IntegrationSettingsTab.Templates)}
        />
        {alertReceiveChannel?.is_available_for_integration_heartbeat && (
          <Tab
            active={activeTab === IntegrationSettingsTab.Heartbeat}
            label="Heartbeat"
            key={IntegrationSettingsTab.Heartbeat}
            onChangeTab={getTabClickHandler(IntegrationSettingsTab.Heartbeat)}
          />
        )}
        <Tab
          active={activeTab === IntegrationSettingsTab.Autoresolve}
          label="Settings"
          key={IntegrationSettingsTab.Autoresolve}
          onChangeTab={getTabClickHandler(IntegrationSettingsTab.Autoresolve)}
        />
      </TabsBar>
      <TabContent className={cx('content')}>
        {activeTab === IntegrationSettingsTab.Templates && (
          <AlertTemplatesFormContainer
            alertReceiveChannelId={id}
            alertGroupId={alertGroupId}
            onUpdate={onUpdate}
            onHide={onHide}
            onUpdateTemplates={onUpdateTemplates}
            selectedTemplateName={selectedTemplate}
          />
        )}
        {activeTab === IntegrationSettingsTab.Heartbeat && (
          <div className="container">
            <HeartbeatForm alertReceveChannelId={id} onUpdate={onUpdate} />
          </div>
        )}
        {activeTab === IntegrationSettingsTab.Autoresolve && (
          <Autoresolve
            alertReceiveChannelId={id}
            onSwitchToTemplate={handleSwitchToTemplate}
            alertGroupId={alertGroupId}
          />
        )}
        {activeTab === IntegrationSettingsTab.HowToConnect && (
          <div className="container">
            <VerticalGroup>
              {alertReceiveChannel.integration_url && (
                <div>
                  <h4>This is the unique webhook URL for the integration:</h4>
                  <div style={{ width: '70%' }}>
                    <Input
                      value={alertReceiveChannel.integration_url}
                      addonAfter={
                        <CopyToClipboard
                          text={alertReceiveChannel.integration_url}
                          onCopy={() => {
                            openNotification('Unique webhook URL copied');
                          }}
                        >
                          <Button icon="copy" variant="primary" />
                        </CopyToClipboard>
                      }
                    />
                  </div>
                </div>
              )}
              <div dangerouslySetInnerHTML={{ __html: alertReceiveChannel?.instructions }} />
              <Button variant="primary" onClick={onHide}>
                Open Escalations Settings
              </Button>
            </VerticalGroup>
          </div>
        )}
      </TabContent>
    </Drawer>
  );
});

export default IntegrationSettings;
