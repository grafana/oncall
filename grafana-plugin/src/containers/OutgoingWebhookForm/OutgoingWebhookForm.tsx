import React, { ChangeEvent, useCallback, useState } from 'react';

import {
  Button,
  ConfirmModal,
  ConfirmModalProps,
  Drawer,
  EmptySearchResult,
  HorizontalGroup,
  Input,
  Tab,
  TabsBar,
  VerticalGroup,
} from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { useHistory } from 'react-router-dom';

import { Block } from 'components/GBlock/Block';
import { GForm, CustomFieldSectionRendererProps } from 'components/GForm/GForm';
import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { IntegrationLogo } from 'components/IntegrationLogo/IntegrationLogo';
import { logoCoors } from 'components/IntegrationLogo/IntegrationLogo.config';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { Labels, LabelsProps } from 'containers/Labels/Labels';
import { getWebhookPresetIcons } from 'containers/OutgoingWebhookForm/WebhookPresetIcons.config';
import { OutgoingWebhookStatus } from 'containers/OutgoingWebhookStatus/OutgoingWebhookStatus';
import { WebhooksTemplateEditor } from 'containers/WebhooksTemplateEditor/WebhooksTemplateEditor';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { LabelKeyValue } from 'models/label/label.types';
import { OutgoingWebhook, OutgoingWebhookPreset } from 'models/outgoing_webhook/outgoing_webhook.types';
import { WebhookFormActionType } from 'pages/outgoing_webhooks/OutgoingWebhooks.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { PLUGIN_ROOT } from 'utils/consts';
import { KeyValuePair } from 'utils/utils';

import { createForm } from './OutgoingWebhookForm.config';
import { WebhookFormFieldName } from './OutgoingWebhookForm.types';

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
  LastRun: new KeyValuePair('LastRun', 'Last Event'),
};

const CustomFieldSectionRenderer: React.FC<CustomFieldSectionRendererProps> = observer(({ setValue, getValues }) => {
  const {
    hasFeature,
    outgoingWebhookStore: { labelsFormErrors },
  } = useStore();
  const onDataUpdate: LabelsProps['onDataUpdate'] = useCallback(
    (val) => setValue(WebhookFormFieldName.Labels, val),
    []
  );

  return (
    <RenderConditionally shouldRender={hasFeature(AppFeature.Labels)}>
      <Labels
        value={getValues<LabelKeyValue[]>(WebhookFormFieldName.Labels) || []}
        errors={labelsFormErrors}
        onDataUpdate={onDataUpdate}
        description="Labels applied to the webhook will be included in the webhook payload, along with alert group and integration labels."
      />
    </RenderConditionally>
  );
});

export const OutgoingWebhookForm = observer((props: OutgoingWebhookFormProps) => {
  const history = useHistory();
  const { id, action, onUpdate, onHide, onDelete } = props;
  const [onFormChangeFn, setOnFormChangeFn] = useState<{ fn: (value: string) => void }>(undefined);
  const [templateToEdit, setTemplateToEdit] = useState(undefined);
  const [activeTab, setActiveTab] = useState<string>(
    action === WebhookFormActionType.EDIT_SETTINGS ? WebhookTabs.Settings.key : WebhookTabs.LastRun.key
  );
  const [showPresetsListDrawer, setShowPresetsListDrawer] = useState(id === 'new');
  const [showCreateWebhookDrawer, setShowCreateWebhookDrawer] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<OutgoingWebhookPreset>(undefined);
  const [filterValue, setFilterValue] = useState('');

  const { outgoingWebhookStore, hasFeature, grafanaTeamStore, alertReceiveChannelStore } = useStore();
  const isNew = action === WebhookFormActionType.NEW;
  const isNewOrCopy = isNew || action === WebhookFormActionType.COPY;
  const form = createForm({
    presets: outgoingWebhookStore.outgoingWebhookPresets,
    grafanaTeamStore,
    alertReceiveChannelStore,
    hasLabelsFeature: hasFeature(AppFeature.Labels),
  });

  const handleSubmit = useCallback(
    async (data: Partial<OutgoingWebhook>) => {
      try {
        if (isNewOrCopy) {
          await outgoingWebhookStore.create(data);
        } else {
          await outgoingWebhookStore.update(id, data);
        }
        outgoingWebhookStore.setLabelsFormErrors(undefined);
        onHide();
        onUpdate();
      } catch (err) {
        if (err.response?.data?.labels) {
          outgoingWebhookStore.setLabelsFormErrors(err.response.data.labels);
        }
      }
    },
    [id]
  );

  const getTemplateEditClickHandler = (formItem: FormItem, values, setFormFieldValue) => {
    return () => {
      const formValue = values[formItem.name];
      setTemplateToEdit({
        value: formValue,
        displayName: `Webhook ${capitalCase(formItem.name)}`,
        description: undefined,
        name: formItem.name,
      });
      setOnFormChangeFn({ fn: (value) => setFormFieldValue(value) });
    };
  };

  const enrichField = (
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
        preset: string;
      };

  if (isNew) {
    data = {
      is_webhook_enabled: true,
      is_legacy: false,
      preset: selectedPreset?.id,
      trigger_type: null,
      http_method: 'POST',
      forward_all: true,
    };
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

  const formElement = (
    <GForm
      form={form}
      data={data}
      onSubmit={handleSubmit}
      onFieldRender={enrichField}
      customFieldSectionRenderer={CustomFieldSectionRenderer}
    />
  );
  const createWebhookParameters = (
    <>
      <Drawer scrollableContent title={'New Outgoing Webhook'} onClose={onHide} closeOnMaskClick={false}>
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

  const presets = outgoingWebhookStore.outgoingWebhookPresets.filter((preset: OutgoingWebhookPreset) =>
    preset.name.toLowerCase().includes(filterValue.toLowerCase())
  );

  if (action === WebhookFormActionType.NEW) {
    return (
      <>
        {showPresetsListDrawer && (
          <Drawer
            scrollableContent
            title="New Outgoing Webhook"
            onClose={onHide}
            closeOnMaskClick={false}
            width="640px"
          >
            <div className={cx('content')}>
              <VerticalGroup>
                <Text type="secondary">
                  Outgoing webhooks can send alert data to other systems. They can be triggered by various conditions
                  and can use templates to transform data to fit the recipient system. Presets listed below provide a
                  starting point to customize these connections.
                </Text>

                {presets.length > 8 && (
                  <div className={cx('search-integration')}>
                    <Input
                      autoFocus
                      value={filterValue}
                      placeholder="Search webhook presets ..."
                      onChange={(e: ChangeEvent<HTMLInputElement>) => setFilterValue(e.currentTarget.value)}
                    />
                  </div>
                )}

                <WebhookPresetBlocks presets={presets} onBlockClick={onBlockClick} />
              </VerticalGroup>
            </div>
          </Drawer>
        )}
        {(showCreateWebhookDrawer || !showPresetsListDrawer) && createWebhookParameters}
      </>
    );
  } else if (action === WebhookFormActionType.COPY) {
    return createWebhookParameters;
  }

  return (
    // show tabbed drawer (edit/live_run)
    <>
      <Drawer
        scrollableContent
        title={'Outgoing webhook details'}
        onClose={onHide}
        closeOnMaskClick={false}
        tabs={
          <div className={cx('tabsWrapper')}>
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
          </div>
        }
      >
        <div className={cx('webhooks__drawerContent')}>
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

  function onBlockClick(preset: OutgoingWebhookPreset) {
    setSelectedPreset(preset);
    setShowCreateWebhookDrawer(true);
    setShowPresetsListDrawer(false);
  }

  function renderWebhookForm() {
    return (
      <>
        <div className={cx('content')}>
          <GForm
            form={form}
            data={data}
            onSubmit={handleSubmit}
            onFieldRender={enrichField}
            customFieldSectionRenderer={CustomFieldSectionRenderer}
          />
          <div className={cx('buttons')}>
            <HorizontalGroup justify={'flex-end'}>
              {id === 'new' ? (
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowCreateWebhookDrawer(false);
                    setShowPresetsListDrawer(true);
                  }}
                >
                  Back
                </Button>
              ) : (
                <Button variant="secondary" onClick={onHide}>
                  Cancel
                </Button>
              )}
              <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                <Button form={form.name} type="submit" disabled={data.is_legacy}>
                  {isNewOrCopy ? 'Create' : 'Update'}
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
        preset: string;
      };
  onHide: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  handleSubmit: (data: Partial<OutgoingWebhook>) => void;
  formElement: React.ReactElement;
}

const WebhookTabsContent: React.FC<WebhookTabsProps> = observer(
  ({ id, action, activeTab, data, onHide, onDelete, formElement }) => {
    const [confirmationModal, setConfirmationModal] = useState<ConfirmModalProps>(undefined);
    const { outgoingWebhookStore, hasFeature, grafanaTeamStore, alertReceiveChannelStore } = useStore();
    const form = createForm({
      presets: outgoingWebhookStore.outgoingWebhookPresets,
      grafanaTeamStore,
      alertReceiveChannelStore,
      hasLabelsFeature: hasFeature(AppFeature.Labels),
    });
    return (
      <div className={cx('tabs__content')}>
        {confirmationModal && (
          <ConfirmModal
            {...(confirmationModal as ConfirmModalProps)}
            onDismiss={() => setConfirmationModal(undefined)}
          />
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
                      {action === WebhookFormActionType.NEW ? 'Create' : 'Update'}
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
        {activeTab === WebhookTabs.LastRun.key && <OutgoingWebhookStatus id={id} closeDrawer={onHide} />}
      </div>
    );
  }
);

const WebhookPresetBlocks: React.FC<{
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
