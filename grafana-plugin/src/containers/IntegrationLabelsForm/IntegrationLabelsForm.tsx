import React, { ChangeEvent, useState } from 'react';

import { ServiceLabels } from '@grafana/labels';
import {
  Alert,
  Button,
  Drawer,
  Dropdown,
  HorizontalGroup,
  InlineSwitch,
  Input,
  Menu,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Collapse } from 'components/Collapse/Collapse';
import { MonacoEditor, MONACO_LANGUAGE } from 'components/MonacoEditor/MonacoEditor';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { IntegrationTemplate } from 'containers/IntegrationTemplate/IntegrationTemplate';
import { splitToGroups } from 'models/label/label.helpers';
import { LabelsErrors } from 'models/label/label.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { LabelTemplateOptions } from 'pages/integration/IntegrationCommon.config';
import { useStore } from 'state/useStore';
import { DOCS_ROOT, GENERIC_ERROR } from 'utils/consts';
import { openErrorNotification } from 'utils/utils';

import { getIsAddBtnDisabled, getIsTooManyLabelsWarningVisible } from './IntegrationLabelsForm.helpers';

import styles from './IntegrationLabelsForm.module.css';

const cx = cn.bind(styles);

const INPUT_WIDTH = 280;

interface IntegrationLabelsFormProps {
  id: ApiSchemas['AlertReceiveChannel']['id'];
  onSubmit: () => void;
  onHide: () => void;
  onOpenIntegrationSettings: (id: ApiSchemas['AlertReceiveChannel']['id']) => void;
}

export const IntegrationLabelsForm = observer((props: IntegrationLabelsFormProps) => {
  const { id, onHide, onSubmit, onOpenIntegrationSettings } = props;

  const store = useStore();

  const [showTemplateEditor, setShowTemplateEditor] = useState<boolean>(false);
  const [customLabelsErrors, setCustomLabelsErrors] = useState<LabelsErrors>([]);
  const [customLabelIndexToShowTemplateEditor, setCustomLabelIndexToShowTemplateEditor] = useState<number>(undefined);

  const { alertReceiveChannelStore } = store;

  const alertReceiveChannel = alertReceiveChannelStore.items[id];
  const templates = alertReceiveChannelStore.templates[id];

  const [alertGroupLabels, setAlertGroupLabels] = useState(alertReceiveChannel.alert_group_labels);

  const handleSave = async () => {
    try {
      await alertReceiveChannelStore.saveAlertReceiveChannel(id, {
        alert_group_labels: alertGroupLabels,
      });
      onSubmit();
      onHide();
    } catch (err) {
      if (err.response?.data?.alert_group_labels?.custom) {
        setCustomLabelsErrors(err.response.data.alert_group_labels.custom);
      }
    }
  };

  const handleOpenIntegrationSettings = () => {
    onHide();

    onOpenIntegrationSettings(id);
  };

  const onInheritanceChange = (keyId: ApiSchemas['LabelKey']['id']) => {
    setAlertGroupLabels((alertGroupLabels) => ({
      ...alertGroupLabels,
      inheritable: { ...alertGroupLabels.inheritable, [keyId]: !alertGroupLabels.inheritable[keyId] },
    }));
  };

  return (
    <>
      <Drawer
        scrollableContent
        title="Alert group labeling"
        subtitle={
          <Text size="small" className="u-margin-top-xs">
            Combination of settings that manage the labeling of alert groups. More information in{' '}
            <a href={`${DOCS_ROOT}/integrations/#alert-group-labels`} target="_blank" rel="noreferrer">
              <Text type="link">documentation</Text>
            </a>
            .
          </Text>
        }
        onClose={onHide}
        closeOnMaskClick={false}
        width="640px"
      >
        <VerticalGroup spacing="lg">
          <RenderConditionally shouldRender={getIsTooManyLabelsWarningVisible(alertGroupLabels)}>
            <Alert title="More than 15 labels added" severity="warning">
              We support up to 15 labels per Alert group. Please remove extra labels.
              <br />
              Otherwise, only the first 15 labels (alphabetically sorted by keys) will be applied.
            </Alert>
          </RenderConditionally>
          <VerticalGroup>
            <Text>Integration labels</Text>
            {alertReceiveChannel.labels.length ? (
              <VerticalGroup spacing="xs">
                <Text type="secondary" size="small">
                  Labels inherited from <PluginLink onClick={handleOpenIntegrationSettings}>the integration</PluginLink>
                  . This behavior can be disabled using the toggle option.
                </Text>
                <ul className={cx('labels-list')}>
                  {alertReceiveChannel.labels.map((label) => (
                    <li key={label.key.id}>
                      <HorizontalGroup spacing="xs">
                        <Input width={INPUT_WIDTH / 8} value={label.key.name} disabled />
                        <Input width={INPUT_WIDTH / 8} value={label.value.name} disabled />
                        <InlineSwitch
                          value={alertGroupLabels.inheritable[label.key.id]}
                          transparent
                          onChange={() => onInheritanceChange(label.key.id)}
                        />
                      </HorizontalGroup>
                    </li>
                  ))}
                </ul>
              </VerticalGroup>
            ) : (
              <VerticalGroup>
                <Text type="secondary">There are no labels to inherit yet</Text>
                <Text type="link" onClick={handleOpenIntegrationSettings} clickable>
                  Add labels to the integration
                </Text>
              </VerticalGroup>
            )}
          </VerticalGroup>

          <CustomLabels
            alertGroupLabels={alertGroupLabels}
            onChange={(val) => {
              setCustomLabelsErrors([]);
              setAlertGroupLabels(val);
            }}
            onShowTemplateEditor={setCustomLabelIndexToShowTemplateEditor}
            customLabelsErrors={customLabelsErrors}
          />

          <Collapse isOpen={false} label="Multi-label extraction template" contentClassName="u-padding-top-none">
            <VerticalGroup>
              <HorizontalGroup justify="space-between" style={{ marginBottom: '10px' }} align="flex-end">
                <Text type="secondary" size="small" className="u-padding-left-lg">
                  Allows for the extraction and modification of multiple labels from the alert payload using a single
                  template. Supports not only dynamic values but also dynamic keys. The Jinja template must result in
                  valid JSON dictionary.
                </Text>
                <Button
                  variant="secondary"
                  icon="edit"
                  onClick={() => {
                    setShowTemplateEditor(true);
                  }}
                />
              </HorizontalGroup>
              <MonacoEditor
                value={alertGroupLabels.template}
                height="200px"
                data={{}}
                showLineNumbers={false}
                language={MONACO_LANGUAGE.jinja2}
                onChange={(value) => {
                  setAlertGroupLabels({ ...alertGroupLabels, template: value });
                }}
              />
            </VerticalGroup>
          </Collapse>

          <div className={cx('buttons')}>
            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={onHide}>
                Close
              </Button>
              <Button variant="primary" onClick={handleSave}>
                Save
              </Button>
            </HorizontalGroup>
          </div>
        </VerticalGroup>
      </Drawer>
      {customLabelIndexToShowTemplateEditor !== undefined && (
        <IntegrationTemplate
          id={id}
          template={{
            name: LabelTemplateOptions.AlertGroupDynamicLabel.key,
            displayName: LabelTemplateOptions.AlertGroupDynamicLabel.value,
          }}
          templates={templates}
          templateBody={alertGroupLabels.custom[customLabelIndexToShowTemplateEditor].value.name}
          onHide={() => setCustomLabelIndexToShowTemplateEditor(undefined)}
          onUpdateTemplates={(templates) => {
            const newCustom = [...alertGroupLabels.custom];
            newCustom[customLabelIndexToShowTemplateEditor].value.name =
              templates[LabelTemplateOptions.AlertGroupDynamicLabel.key];

            setAlertGroupLabels({
              ...alertGroupLabels,
              custom: newCustom,
            });

            setCustomLabelIndexToShowTemplateEditor(undefined);
          }}
        />
      )}
      {showTemplateEditor && (
        <IntegrationTemplate
          id={id}
          template={{
            name: LabelTemplateOptions.AlertGroupMultiLabel.key,
            displayName: LabelTemplateOptions.AlertGroupMultiLabel.value,
          }}
          templates={templates}
          templateBody={alertGroupLabels.template}
          onHide={() => setShowTemplateEditor(false)}
          onUpdateTemplates={(templates) => {
            setAlertGroupLabels({
              ...alertGroupLabels,
              template: templates[LabelTemplateOptions.AlertGroupMultiLabel.key],
            });

            setShowTemplateEditor(undefined);
          }}
        />
      )}
    </>
  );
});

interface CustomLabelsProps {
  alertGroupLabels: ApiSchemas['AlertReceiveChannel']['alert_group_labels'];
  customLabelsErrors: LabelsErrors;
  onChange: (value: ApiSchemas['AlertReceiveChannel']['alert_group_labels']) => void;
  onShowTemplateEditor: (index: number) => void;
}

const CustomLabels = (props: CustomLabelsProps) => {
  const { alertGroupLabels, onChange, onShowTemplateEditor, customLabelsErrors } = props;

  const { labelsStore } = useStore();

  const handleStaticLabelAdd = () => {
    onChange({
      ...alertGroupLabels,
      custom: [
        ...alertGroupLabels.custom,
        {
          key: { id: undefined, name: undefined, prescribed: false },
          value: { id: undefined, name: undefined, prescribed: false },
        },
      ],
    });
  };
  const handleDynamicLabelAdd = () => {
    onChange({
      ...alertGroupLabels,
      custom: [
        ...alertGroupLabels.custom,
        {
          key: { id: undefined, name: undefined, prescribed: false },
          value: { id: null, name: undefined, prescribed: false }, // id = null means it's a templated value
        },
      ],
    });
  };

  const onLoadKeys = async (search?: string) => {
    let result = undefined;

    try {
      result = await labelsStore.loadKeys(search);
    } catch (error) {
      openErrorNotification('There was an error processing your request. Please try again');
    }

    const groups = splitToGroups(result);

    return groups;
  };

  const onLoadValuesForKey = async (key: string, search?: string) => {
    let result = undefined;

    try {
      const { values } = await labelsStore.loadValuesForKey(key, search);
      result = values;
    } catch (error) {
      openErrorNotification('There was an error processing your request. Please try again');
    }

    const groups = splitToGroups(result);

    return groups;
  };

  return (
    <VerticalGroup>
      <Text>Dynamic & Static labels</Text>
      <Text type="secondary" size="small">
        Dynamic: label values are extracted from the alert payload using Jinja. Keys remain static.
        <br />
        Static: these are not derived from the payload; both key and value are static.
        <br />
        These labels will not be attached to the integration.
      </Text>
      <ServiceLabels
        isAddingDisabled
        loadById
        inputWidth={INPUT_WIDTH}
        errors={customLabelsErrors}
        value={alertGroupLabels.custom}
        onLoadKeys={onLoadKeys}
        onLoadValuesForKey={onLoadValuesForKey}
        onCreateKey={labelsStore.createKey}
        onUpdateKey={labelsStore.updateKey}
        onCreateValue={labelsStore.createValue}
        onUpdateValue={labelsStore.updateKeyValue}
        onUpdateError={(res) => {
          if (res?.response?.status === 409) {
            openErrorNotification(`Duplicate values are not allowed`);
          } else {
            openErrorNotification(GENERIC_ERROR);
          }
        }}
        renderValue={(option, index, renderValueDefault) => {
          if (option.value.id === null) {
            return (
              <Input
                placeholder="Jinja2 template"
                autoFocus
                disabled={!alertGroupLabels.custom[index].key.id}
                width={INPUT_WIDTH / 8}
                value={option.value.name}
                addonAfter={
                  <Button
                    variant="secondary"
                    icon="edit"
                    onClick={() => {
                      onShowTemplateEditor(index);
                    }}
                  />
                }
                onChange={(e: ChangeEvent<HTMLInputElement>) => {
                  const newCustom = [...alertGroupLabels.custom];
                  newCustom[index].value.name = e.currentTarget.value;

                  onChange({ ...alertGroupLabels, custom: newCustom });
                }}
              />
            );
          } else {
            return renderValueDefault(option, index);
          }
        }}
        onDataUpdate={(value) => {
          onChange({
            ...alertGroupLabels,
            custom: value,
          });
        }}
        getIsKeyEditable={(option) => !option.prescribed}
        getIsValueEditable={(option) => !option.prescribed}
      />
      <Dropdown
        overlay={
          <Menu>
            <Menu.Item label="Static label" onClick={handleStaticLabelAdd} />
            <Menu.Item label="Dynamic label" onClick={handleDynamicLabelAdd} />
          </Menu>
        }
      >
        <Button variant="secondary" icon="plus" disabled={getIsAddBtnDisabled(alertGroupLabels)}>
          Add label
        </Button>
      </Dropdown>
    </VerticalGroup>
  );
};
