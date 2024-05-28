import React, { ChangeEvent, useCallback, useEffect, useMemo, useState } from 'react';

import {
  Button,
  ConfirmModal,
  ConfirmModalProps,
  Drawer,
  HorizontalGroup,
  Input,
  Tab,
  TabsBar,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { FormProvider, useForm, useFormContext } from 'react-hook-form';
import { useHistory } from 'react-router-dom';

import { Text } from 'components/Text/Text';
import { OutgoingWebhookStatus } from 'containers/OutgoingWebhookStatus/OutgoingWebhookStatus';
import { WebhooksTemplateEditor } from 'containers/WebhooksTemplateEditor/WebhooksTemplateEditor';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { OutgoingWebhookPreset } from 'models/outgoing_webhook/outgoing_webhook.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { WebhookFormActionType } from 'pages/outgoing_webhooks/OutgoingWebhooks.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { PLUGIN_ROOT } from 'utils/consts';
import { KeyValuePair } from 'utils/utils';

import { TemplateParams, WebhookFormFieldName } from './OutgoingWebhookForm.types';
import { OutgoingWebhookFormFields } from './OutgoingWebhookFormFields';
import { WebhookPresetBlocks } from './WebhookPresetBlocks';

import styles from './OutgoingWebhookForm.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhookFormProps {
  id: ApiSchemas['Webhook']['id'] | 'new';
  action: WebhookFormActionType;
  onHide: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

export const WebhookTabs = {
  Settings: new KeyValuePair('Settings', 'Settings'),
  LastRun: new KeyValuePair('LastRun', 'Last Event'),
};

function prepareDataForEdit(
  action: WebhookFormActionType,
  item: ApiSchemas['Webhook'],
  selectedPreset: OutgoingWebhookPreset
) {
  if (action === WebhookFormActionType.NEW) {
    return {
      is_webhook_enabled: true,
      is_legacy: false,
      trigger_type: null,
      preset: selectedPreset?.id,
      http_method: 'POST',
      forward_all: true,
      labels: [],
    };
  } else if (action === WebhookFormActionType.COPY) {
    return { ...item, is_legacy: false, name: '' };
  } else {
    return { ...item };
  }
}

function prepareForSave(rawData: Partial<ApiSchemas['Webhook']>, selectedPreset: OutgoingWebhookPreset) {
  const data = { ...rawData };
  selectedPreset?.controlled_fields.forEach((field) => {
    delete data[field];
  });

  return data;
}

export const OutgoingWebhookForm = observer((props: OutgoingWebhookFormProps) => {
  const { id, action, onUpdate, onHide, onDelete } = props;

  const [selectedPreset, setSelectedPreset] = useState<OutgoingWebhookPreset>(undefined);
  const [templateToEdit, setTemplateToEdit] = useState<TemplateParams>(undefined);

  const { outgoingWebhookStore } = useStore();

  const item = outgoingWebhookStore.items[id];
  const data = prepareDataForEdit(action, item, selectedPreset);

  useEffect(() => {
    if (item) {
      const preset = outgoingWebhookStore.outgoingWebhookPresets.find((item) => item.id === data.preset);
      setSelectedPreset(preset);
    }
  }, [item]);

  useEffect(() => {
    if (selectedPreset) {
      reset(data);
    }
  }, [selectedPreset]);

  const formMethods = useForm<ApiSchemas['Webhook']>({
    mode: 'onChange',
    defaultValues: data,
  });

  const { setValue, reset, setError } = formMethods;

  const onSubmit = useCallback(
    async (rawData: Partial<ApiSchemas['Webhook']>) => {
      const data = prepareForSave(rawData, selectedPreset);

      try {
        if (action === WebhookFormActionType.NEW || action === WebhookFormActionType.COPY) {
          await outgoingWebhookStore.create(data);
        } else {
          await outgoingWebhookStore.update(id, data);
        }
        onHide();
        onUpdate();
      } catch (error) {
        Object.keys(error.response.data).forEach((key) => {
          setError(key as WebhookFormFieldName, { message: error.response.data[key][0] });
        });
      }
    },
    [id, selectedPreset]
  );

  const mainContent = useMemo(() => {
    if (action === WebhookFormActionType.NEW && !selectedPreset) {
      return <Presets onHide={onHide} onSelect={setSelectedPreset} />;
    }

    if (action === WebhookFormActionType.NEW || action === WebhookFormActionType.COPY) {
      return (
        <NewWebhook
          action={action}
          data={data}
          preset={selectedPreset}
          onBack={() => setSelectedPreset(undefined)}
          onHide={onHide}
          onTemplateEditClick={setTemplateToEdit}
          onSubmit={onSubmit}
        />
      );
    }

    return (
      <EditWebhookTabs
        action={action}
        data={data}
        id={id}
        onDelete={onDelete}
        onHide={onHide}
        onUpdate={onUpdate}
        onSubmit={onSubmit}
        onTemplateEditClick={setTemplateToEdit}
        preset={selectedPreset}
      />
    );
  }, [action, selectedPreset]);

  if ((action === WebhookFormActionType.EDIT_SETTINGS || action === WebhookFormActionType.VIEW_LAST_RUN) && !item) {
    return null;
  }

  return (
    <>
      <FormProvider {...formMethods}>{mainContent}</FormProvider>
      {templateToEdit && (
        <WebhooksTemplateEditor
          id={id}
          handleSubmit={(value) => {
            setValue(templateToEdit.name, value);
            setTemplateToEdit(undefined);
          }}
          onHide={() => setTemplateToEdit(undefined)}
          template={templateToEdit}
        />
      )}
    </>
  );
});

interface PresetsProps {
  onHide: () => void;
  onSelect: (preset: OutgoingWebhookPreset) => void;
}

const Presets = (props: PresetsProps) => {
  const { onHide, onSelect } = props;

  const [filterValue, setFilterValue] = useState('');

  const { outgoingWebhookStore } = useStore();

  const presets = outgoingWebhookStore.outgoingWebhookPresets.filter((preset: OutgoingWebhookPreset) =>
    preset.name.toLowerCase().includes(filterValue.toLowerCase())
  );

  return (
    <Drawer scrollableContent title="New Outgoing Webhook" onClose={onHide} closeOnMaskClick={false} width="640px">
      <div className={cx('content')}>
        <VerticalGroup>
          <Text type="secondary">
            Outgoing webhooks can send alert data to other systems. They can be triggered by various conditions and can
            use templates to transform data to fit the recipient system. Presets listed below provide a starting point
            to customize these connections.
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

          <WebhookPresetBlocks presets={presets} onBlockClick={onSelect} />
        </VerticalGroup>
      </div>
    </Drawer>
  );
};

interface NewWebhookProps {
  data: Partial<ApiSchemas['Webhook']>;
  preset: OutgoingWebhookPreset;
  onHide: () => void;
  onBack: () => void;
  action: WebhookFormActionType;
  onTemplateEditClick: (params: TemplateParams) => void;
  onSubmit: (data: Partial<ApiSchemas['Webhook']>) => void;
}

const NewWebhook = (props: NewWebhookProps) => {
  const { data, preset, onHide, action, onBack, onTemplateEditClick, onSubmit } = props;

  const { hasFeature } = useStore();

  const { handleSubmit } = useFormContext();

  return (
    <Drawer scrollableContent title={'New Outgoing Webhook'} onClose={onHide} closeOnMaskClick={false}>
      <div className="webhooks__drawerContent">
        <div className={cx('content')}>
          <form id="OutgoingWebhook" onSubmit={handleSubmit(onSubmit)} className={styles.form}>
            <OutgoingWebhookFormFields
              preset={preset}
              hasLabelsFeature={hasFeature(AppFeature.Labels)}
              onTemplateEditClick={onTemplateEditClick}
            />
            <div className={cx('buttons')}>
              <HorizontalGroup justify="flex-end">
                {action === WebhookFormActionType.NEW ? (
                  <Button variant="secondary" onClick={onBack}>
                    Back
                  </Button>
                ) : (
                  <Button variant="secondary" onClick={onHide}>
                    Cancel
                  </Button>
                )}
                <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                  <Button type="submit" onClick={handleSubmit(onSubmit)} disabled={data.is_legacy}>
                    Create
                  </Button>
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </div>
          </form>
        </div>
      </div>
    </Drawer>
  );
};

interface EditWebhookTabsProps {
  id: OutgoingWebhookFormProps['id'];
  data: Partial<ApiSchemas['Webhook']>;
  action: WebhookFormActionType;
  onHide: OutgoingWebhookFormProps['onHide'];
  onUpdate: OutgoingWebhookFormProps['onUpdate'];
  onDelete: OutgoingWebhookFormProps['onDelete'];
  onSubmit: (data: Partial<ApiSchemas['Webhook']>) => void;
  onTemplateEditClick: (params: TemplateParams) => void;
  preset: OutgoingWebhookPreset;
}

const EditWebhookTabs = (props: EditWebhookTabsProps) => {
  const { id, data, action, onHide, onUpdate, onDelete, onSubmit, onTemplateEditClick, preset } = props;

  const history = useHistory();

  const [activeTab, setActiveTab] = useState(
    action === WebhookFormActionType.EDIT_SETTINGS ? WebhookTabs.Settings.key : WebhookTabs.LastRun.key
  );

  return (
    <Drawer
      scrollableContent
      title="Outgoing webhook details"
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
          onDelete={onDelete}
          onHide={onHide}
          onUpdate={onUpdate}
          onSubmit={onSubmit}
          onTemplateEditClick={onTemplateEditClick}
          preset={preset}
        />
      </div>
    </Drawer>
  );
};

interface WebhookTabsProps {
  id: OutgoingWebhookFormProps['id'];
  activeTab: string;
  action: WebhookFormActionType;
  data: Partial<ApiSchemas['Webhook']>;
  onHide: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  preset: OutgoingWebhookPreset;
  onTemplateEditClick: (params: TemplateParams) => void;
  onSubmit: (data: Partial<ApiSchemas['Webhook']>) => void;
}

const WebhookTabsContent: React.FC<WebhookTabsProps> = observer(
  ({ id, action, activeTab, data, onHide, onDelete, onSubmit, onTemplateEditClick, preset }) => {
    const [confirmationModal, setConfirmationModal] = useState<ConfirmModalProps>(undefined);

    const { hasFeature } = useStore();

    const { handleSubmit } = useFormContext();

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
              <form id="OutgoingWebhook" onSubmit={handleSubmit(onSubmit)} className={styles.form}>
                <OutgoingWebhookFormFields
                  preset={preset}
                  hasLabelsFeature={hasFeature(AppFeature.Labels)}
                  onTemplateEditClick={onTemplateEditClick}
                />
                <div className={cx('buttons')}>
                  <HorizontalGroup justify={'flex-end'}>
                    <Button variant="secondary" onClick={onHide}>
                      Cancel
                    </Button>
                    <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                      <Button
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
                      <Button type="submit" onClick={handleSubmit(onSubmit)} disabled={data.is_legacy}>
                        {action === WebhookFormActionType.NEW ? 'Create' : 'Update'}
                      </Button>
                    </WithPermissionControlTooltip>
                  </HorizontalGroup>
                </div>
              </form>
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
