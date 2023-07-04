import React, { useCallback, useState } from 'react';

import { Button, Drawer, HorizontalGroup, Tab, TabsBar } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GForm from 'components/GForm/GForm';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import OutgoingWebhook2Status from 'containers/OutgoingWebhook2Status/OutgoingWebhook2Status';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { OutgoingWebhook2 } from 'models/outgoing_webhook_2/outgoing_webhook_2.types';
import { WebhookFormActionType } from 'pages/outgoing_webhooks_2/OutgoingWebhooks2.types';
import { useStore } from 'state/useStore';
import { KeyValuePair } from 'utils';
import { UserActions } from 'utils/authorization';

import { form } from './OutgoingWebhook2Form.config';

import styles from 'containers/OutgoingWebhook2Form/OutgoingWebhook2Form.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhook2FormProps {
  id: OutgoingWebhook2['id'] | 'new';
  action: WebhookFormActionType;
  onHide: () => void;
  onUpdate: () => void;
}

export const WebhookTabs = {
  Settings: new KeyValuePair('Settings', 'Settings'),
  LastRun: new KeyValuePair('LastRun', 'Last Run'),
};

const OutgoingWebhook2Form = observer((props: OutgoingWebhook2FormProps) => {
  const { id, action, onUpdate, onHide } = props;
  const [activeTab, setActiveTab] = useState<string>(
    action === WebhookFormActionType.EDIT_SETTINGS ? WebhookTabs.Settings.key : WebhookTabs.LastRun.key
  );

  const store = useStore();

  const { outgoingWebhook2Store } = store;
  const isNewOrCopy = action === WebhookFormActionType.NEW || action === WebhookFormActionType.COPY;

  const data =
    id === 'new'
      ? { is_webhook_enabled: true, is_legacy: false }
      : isNewOrCopy
      ? { ...outgoingWebhook2Store.items[id], is_legacy: false, name: '' }
      : outgoingWebhook2Store.items[id];

  const handleSubmit = useCallback(
    (data: Partial<OutgoingWebhook2>) => {
      (isNewOrCopy ? outgoingWebhook2Store.create(data) : outgoingWebhook2Store.update(id, data)).then(() => {
        onHide();

        onUpdate();
      });
    },
    [id]
  );

  if (action === WebhookFormActionType.NEW || action === WebhookFormActionType.COPY) {
    return (
      <Drawer scrollableContent title={'Create Outgoing Webhook'} onClose={onHide} closeOnMaskClick={false}>
        {renderWebhookForm()}
      </Drawer>
    );
  }

  return (
    <Drawer scrollableContent title={'Outgoing webhook details'} onClose={onHide} closeOnMaskClick={false}>
      <TabsBar>
        <Tab
          key={WebhookTabs.Settings.key}
          onChangeTab={() => setActiveTab(WebhookTabs.Settings.key)}
          active={activeTab === WebhookTabs.Settings.key}
          label={WebhookTabs.Settings.value}
        />

        <Tab
          key={WebhookTabs.LastRun.key}
          onChangeTab={() => setActiveTab(WebhookTabs.LastRun.key)}
          active={activeTab === WebhookTabs.LastRun.key}
          label={WebhookTabs.LastRun.value}
        />
      </TabsBar>

      <WebhookTabsContent
        id={id}
        action={action}
        activeTab={activeTab}
        data={data}
        handleSubmit={handleSubmit}
        onHide={onHide}
        onUpdate={onUpdate}
      />
    </Drawer>
  );

  function renderWebhookForm() {
    return (
      <>
        <div className={cx('content')} data-testid="test__outgoingWebhook2EditForm">
          <GForm form={form} data={data} onSubmit={handleSubmit} />
          <div className={cx('buttons')}>
            <HorizontalGroup justify={'flex-end'}>
              <Button variant="secondary" onClick={onHide}>
                Cancel
              </Button>
              <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                <Button form={form.name} type="submit" disabled={data.is_legacy}>
                  {isNewOrCopy ? 'Create' : 'Update'} Webhook
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </div>
        </div>
      </>
    );
  }
});

interface WebhookTabsProps {
  id: OutgoingWebhook2['id'] | 'new';
  activeTab: string;
  action: WebhookFormActionType;
  data:
    | OutgoingWebhook2
    | {
        is_webhook_enabled: boolean;
        is_legacy: boolean;
      };
  onHide: () => void;
  onUpdate: () => void;
  handleSubmit: (data: Partial<OutgoingWebhook2>) => void;
}

const WebhookTabsContent: React.FC<WebhookTabsProps> = ({
  id,
  action,
  activeTab,
  data,
  handleSubmit,
  onHide,
  onUpdate,
}) => {
  const store = useStore();
  const webhook = store.outgoingWebhook2Store.items[id];
  return (
    <div className={cx('tabs__content')}>
      {activeTab === WebhookTabs.Settings.key && (
        <>
          <div className={cx('content')} data-testid="test__outgoingWebhook2EditForm">
            <GForm form={form} data={data} onSubmit={handleSubmit} />
            <div className={cx('buttons')}>
              <HorizontalGroup justify={'flex-end'}>
                <Button variant="secondary" onClick={onHide}>
                  Cancel
                </Button>
                {
                  <WithConfirm title={`Are you sure you want to delete ${webhook.name}?`}>
                    <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                      <Button form={form.name} variant="destructive" type="button" disabled={data.is_legacy}>
                        Delete Webhook
                      </Button>
                    </WithPermissionControlTooltip>
                  </WithConfirm>
                }
                <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                  <Button form={form.name} type="submit" disabled={data.is_legacy}>
                    {action === WebhookFormActionType.NEW ? 'Create' : 'Update'} Webhook
                  </Button>
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </div>
          </div>
          {data.is_legacy ? (
            <div className={cx('content')}>
              <Text type="secondary">Legacy migrated webhooks are not editable.</Text>
            </div>
          ) : (
            ''
          )}
        </>
      )}
      {activeTab === WebhookTabs.LastRun.key && <OutgoingWebhook2Status id={id} onUpdate={onUpdate} />}
    </div>
  );
};

export default OutgoingWebhook2Form;
