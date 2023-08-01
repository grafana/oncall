import React, { useCallback, useState } from 'react';

import { Button, ConfirmModal, ConfirmModalProps, Drawer, HorizontalGroup, Tab, TabsBar } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { useHistory } from 'react-router-dom';

import GForm from 'components/GForm/GForm';
import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import Text from 'components/Text/Text';
import OutgoingWebhookStatus from 'containers/OutgoingWebhookStatus/OutgoingWebhookStatus';
import WebhooksTemplateEditor from 'containers/WebhooksTemplateEditor/WebhooksTemplateEditor';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { WebhookFormActionType } from 'pages/outgoing_webhooks/OutgoingWebhooks.types';
import { useStore } from 'state/useStore';
import { KeyValuePair } from 'utils';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import { form } from './OutgoingWebhookForm.config';

import styles from 'containers/OutgoingWebhookForm/OutgoingWebhookForm.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhookFormProps {
  id: OutgoingWebhook['id'] | 'new';
  action: WebhookFormActionType;
  onHide: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

export const WebhookTabs = {
  Settings: new KeyValuePair('Settings', 'Settings'),
  LastRun: new KeyValuePair('LastRun', 'Last Run'),
};

const OutgoingWebhookForm = observer((props: OutgoingWebhookFormProps) => {
  const history = useHistory();
  const { id, action, onUpdate, onHide, onDelete } = props;
  const [onFormChangeFn, setOnFormChangeFn] = useState<{ fn: (value: string) => void }>(undefined);
  const [templateToEdit, setTemplateToEdit] = useState(undefined);
  const [activeTab, setActiveTab] = useState<string>(
    action === WebhookFormActionType.EDIT_SETTINGS ? WebhookTabs.Settings.key : WebhookTabs.LastRun.key
  );

  const { outgoingWebhookStore } = useStore();
  const isNew = action === WebhookFormActionType.NEW;
  const isNewOrCopy = isNew || action === WebhookFormActionType.COPY;

  const handleSubmit = useCallback(
    (data: Partial<OutgoingWebhook>) => {
      (isNewOrCopy ? outgoingWebhookStore.create(data) : outgoingWebhookStore.update(id, data)).then(() => {
        onHide();
        onUpdate();
      });
    },
    [id]
  );

  const getTemplateEditClickHandler = (formItem: FormItem, values, setFormFieldValue) => {
    return () => {
      const formValue = values[formItem.name];
      setTemplateToEdit({ value: formValue, displayName: undefined, description: undefined, name: formItem.name });
      setOnFormChangeFn({ fn: (value) => setFormFieldValue(value) });
    };
  };

  const enrchField = (
    formItem: FormItem,
    disabled: boolean,
    renderedControl: React.ReactElement,
    values,
    setFormFieldValue
  ) => {
    if (formItem.type === FormItemType.Monaco) {
      return (
        <div className={cx('form-row')}>
          <div className={cx('form-field')}>{renderedControl}</div>
          <Button
            disabled={disabled}
            icon="edit"
            variant="secondary"
            onClick={getTemplateEditClickHandler(formItem, values, setFormFieldValue)}
          />
        </div>
      );
    }

    return renderedControl;
  };

  if (
    (action === WebhookFormActionType.EDIT_SETTINGS || action === WebhookFormActionType.VIEW_LAST_RUN) &&
    !outgoingWebhookStore.items[id]
  ) {
    return null;
  }

  let data:
    | OutgoingWebhook
    | {
        is_webhook_enabled: boolean;
        is_legacy: boolean;
      };

  if (isNew) {
    data = { is_webhook_enabled: true, is_legacy: false };
  } else if (isNewOrCopy) {
    data = { ...outgoingWebhookStore.items[id], is_legacy: false, name: '' };
  } else {
    data = outgoingWebhookStore.items[id];
  }

  if (
    (action === WebhookFormActionType.EDIT_SETTINGS || action === WebhookFormActionType.VIEW_LAST_RUN) &&
    !outgoingWebhookStore.items[id]
  ) {
    // nothing to show if we open invalid ID for edit/last_run
    return null;
  }

  const formElement = <GForm form={form} data={data} onSubmit={handleSubmit} onFieldRender={enrchField} />;

  if (action === WebhookFormActionType.NEW || action === WebhookFormActionType.COPY) {
    // show just the creation form, not the tabs
    return (
      <>
        <Drawer scrollableContent title={'Create Outgoing Webhook'} onClose={onHide} closeOnMaskClick={false}>
          <div className="webhooks__drawerContent">{renderWebhookForm()}</div>
        </Drawer>
        {templateToEdit && (
          <WebhooksTemplateEditor
            id={id}
            handleSubmit={(value) => {
              onFormChangeFn?.fn(value);
              setTemplateToEdit(undefined);
            }}
            onHide={() => setTemplateToEdit(undefined)}
            template={templateToEdit}
          />
        )}
      </>
    );
  }

  return (
    // show tabbed drawer (edit/live_run)
    <>
      <Drawer scrollableContent title={'Outgoing webhook details'} onClose={onHide} closeOnMaskClick={false}>
        <div className={cx('webhooks__drawerContent')}>
          <TabsBar>
            <Tab
              key={WebhookTabs.Settings.key}
              onChangeTab={() => {
                setActiveTab(WebhookTabs.Settings.key);
                history.push(`${PLUGIN_ROOT}/outgoing_webhooks/edit/${id}`);
              }}
              active={activeTab === WebhookTabs.Settings.key}
              label={WebhookTabs.Settings.value}
            />

            <Tab
              key={WebhookTabs.LastRun.key}
              onChangeTab={() => {
                setActiveTab(WebhookTabs.LastRun.key);
                history.push(`${PLUGIN_ROOT}/outgoing_webhooks/last_run/${id}`);
              }}
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
            onDelete={onDelete}
            onHide={onHide}
            onUpdate={onUpdate}
            formElement={formElement}
          />
        </div>
      </Drawer>
      {templateToEdit && (
        <WebhooksTemplateEditor
          id={id}
          handleSubmit={(value) => {
            onFormChangeFn?.fn(value);
            setTemplateToEdit(undefined);
          }}
          onHide={() => setTemplateToEdit(undefined)}
          template={templateToEdit}
        />
      )}
    </>
  );

  function renderWebhookForm() {
    return (
      <>
        <div className={cx('content')}>
          <GForm form={form} data={data} onSubmit={handleSubmit} onFieldRender={enrchField} />
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
  id: OutgoingWebhook['id'] | 'new';
  activeTab: string;
  action: WebhookFormActionType;
  data:
    | OutgoingWebhook
    | {
        is_webhook_enabled: boolean;
        is_legacy: boolean;
      };
  onHide: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  handleSubmit: (data: Partial<OutgoingWebhook>) => void;
  formElement: React.ReactElement;
}

const WebhookTabsContent: React.FC<WebhookTabsProps> = ({
  id,
  action,
  activeTab,
  data,
  onHide,
  onUpdate,
  onDelete,
  formElement,
}) => {
  const [confirmationModal, setConfirmationModal] = useState<ConfirmModalProps>(undefined);

  return (
    <div className={cx('tabs__content')}>
      {confirmationModal && (
        <ConfirmModal {...(confirmationModal as ConfirmModalProps)} onDismiss={() => setConfirmationModal(undefined)} />
      )}

      {activeTab === WebhookTabs.Settings.key && (
        <>
          <div className={cx('content')}>
            {formElement}
            <div className={cx('buttons')}>
              <HorizontalGroup justify={'flex-end'}>
                <Button variant="secondary" onClick={onHide}>
                  Cancel
                </Button>
                <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                  <Button
                    form={form.name}
                    variant="destructive"
                    type="button"
                    disabled={data.is_legacy}
                    onClick={() => {
                      setConfirmationModal({
                        isOpen: true,
                        body: 'The action cannot be undone.',
                        confirmText: 'Delete',
                        dismissText: 'Cancel',
                        onConfirm: onDelete,
                        title: `Are you sure you want to delete webhook?`,
                      } as ConfirmModalProps);
                    }}
                  >
                    Delete Webhook
                  </Button>
                </WithPermissionControlTooltip>
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
              <Text type="secondary">Legacy migrated webhooks are not editable. Make a copy to make changes.</Text>
            </div>
          ) : (
            ''
          )}
        </>
      )}
      {activeTab === WebhookTabs.LastRun.key && <OutgoingWebhookStatus id={id} onUpdate={onUpdate} />}
    </div>
  );
};

export default OutgoingWebhookForm;
