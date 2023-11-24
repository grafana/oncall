import React, { ChangeEvent, useCallback, useState } from 'react';

import {
  Button,
  Drawer,
  Dropdown,
  HorizontalGroup,
  Icon,
  InlineSwitch,
  Input,
  Label,
  Menu,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Collapse from 'components/Collapse/Collapse';
import MonacoEditor, { MONACO_LANGUAGE } from 'components/MonacoEditor/MonacoEditor';
import Text from 'components/Text/Text';
import IntegrationTemplate from 'containers/IntegrationTemplate/IntegrationTemplate';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { LabelKey } from 'models/label/label.types';
import { useStore } from 'state/useStore';
import { openErrorNotification } from 'utils';

import styles from './IntegrationLabelsForm.module.css';
import { ServiceLabels } from '@grafana/labels';

const cx = cn.bind(styles);

const INPUT_WIDTH = 280;

interface IntegrationLabelsFormProps {
  id: AlertReceiveChannel['id'];
  onSubmit: () => void;
  onHide: () => void;
  onOpenIntegraionSettings: (id: AlertReceiveChannel['id']) => void;
}

const IntegrationLabelsForm = observer((props: IntegrationLabelsFormProps) => {
  const { id, onHide, onSubmit, onOpenIntegraionSettings } = props;

  const store = useStore();

  const [showTemplateEditor, setShowTemplateEditor] = useState<boolean>(false);
  const [customLabelIndexToShowTemplateEditor, setCustomLabelIndexToShowTemplateEditor] = useState<number>(undefined);

  const { alertReceiveChannelStore } = store;

  const alertReceiveChannel = alertReceiveChannelStore.items[id];
  const templates = alertReceiveChannelStore.templates[id];

  const [alertGroupLabels, setAlertGroupLabels] = useState(alertReceiveChannel.alert_group_labels);

  const handleSave = () => {
    alertReceiveChannelStore.saveAlertReceiveChannel(id, { alert_group_labels: alertGroupLabels });

    onSubmit();

    onHide();
  };

  const handleOpenIntegrationSettings = () => {
    onHide();

    onOpenIntegraionSettings(id);
  };

  const getInheritanceChangeHandler = (keyId: LabelKey['id']) => {
    return (event: React.ChangeEvent<HTMLInputElement>) => {
      setAlertGroupLabels((alertGroupLabels) => ({
        ...alertGroupLabels,
        inheritable: { ...alertGroupLabels.inheritable, [keyId]: event.target.checked },
      }));
    };
  };

  return (
    <>
      <Drawer scrollableContent title="Alert group labels" onClose={onHide} closeOnMaskClick={false} width="640px">
        <VerticalGroup spacing="lg">
          <VerticalGroup>
            <HorizontalGroup spacing="xs" align="flex-start">
              <Label>Inherited labels</Label>
              <Tooltip content="Labels inherited from integration">
                <Icon name="info-circle" className={cx('extra-fields__icon')} />
              </Tooltip>
            </HorizontalGroup>
            {alertReceiveChannel.labels.length ? (
              <ul className={cx('labels-list')}>
                {alertReceiveChannel.labels.map((label) => (
                  <li key={label.key.id}>
                    <HorizontalGroup spacing="xs">
                      <Input width={INPUT_WIDTH / 8} value={label.key.name} disabled />
                      <Input width={INPUT_WIDTH / 8} value={label.value.name} disabled />
                      <InlineSwitch
                        value={alertGroupLabels.inheritable[label.key.id]}
                        transparent
                        onChange={getInheritanceChangeHandler(label.key.id)}
                      />
                    </HorizontalGroup>
                  </li>
                ))}
              </ul>
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
            onChange={setAlertGroupLabels}
            onShowTemplateEditor={setCustomLabelIndexToShowTemplateEditor}
          />

          <Collapse isOpen={false} label="Advanced label templating">
            <VerticalGroup>
              <HorizontalGroup justify="space-between" style={{ marginBottom: '10px' }}>
                <Text type="secondary">Jinja2 template to parse all labels at once</Text>
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
            name: 'alert_group_labels',
            displayName: ``,
          }}
          templates={templates}
          templateBody={alertGroupLabels.custom[customLabelIndexToShowTemplateEditor].value.name}
          onHide={() => setCustomLabelIndexToShowTemplateEditor(undefined)}
          onUpdateTemplates={({ alert_group_labels }) => {
            const newCustom = [...alertGroupLabels.custom];
            newCustom[customLabelIndexToShowTemplateEditor].value.name = alert_group_labels;

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
            name: 'alert_group_labels',
            displayName: ``,
          }}
          templates={templates}
          templateBody={alertGroupLabels.template}
          onHide={() => setShowTemplateEditor(false)}
          onUpdateTemplates={({ alert_group_labels }) => {
            setAlertGroupLabels({
              ...alertGroupLabels,
              template: alert_group_labels,
            });

            setShowTemplateEditor(undefined);
          }}
        />
      )}
    </>
  );
});

interface CustomLabelsProps {
  alertGroupLabels: AlertReceiveChannel['alert_group_labels'];
  onChange: (value: AlertReceiveChannel['alert_group_labels']) => void;
  onShowTemplateEditor: (index: number) => void;
}

const CustomLabels = (props: CustomLabelsProps) => {
  const { alertGroupLabels, onChange, onShowTemplateEditor } = props;

  const { labelsStore } = useStore();

  const handlePlainLabelAdd = () => {
    onChange({
      ...alertGroupLabels,
      custom: [
        ...alertGroupLabels.custom,
        {
          key: { id: undefined, name: undefined },
          value: { id: undefined, name: undefined },
        },
      ],
    });
  };
  const handleTemplatedLabelAdd = () => {
    onChange({
      ...alertGroupLabels,
      custom: [
        ...alertGroupLabels.custom,
        {
          key: { id: undefined, name: undefined },
          value: { id: null, name: undefined }, // id = null means it's a templated value
        },
      ],
    });
  };

  const cachedOnLoadKeys = useCallback(() => {
    let result = undefined;
    return async (search?: string) => {
      if (!result) {
        try {
          result = await labelsStore.loadKeys();
        } catch (error) {
          openErrorNotification('There was an error processing your request. Please try again');
        }
      }

      return result.filter((k) => k.name.toLowerCase().includes(search.toLowerCase()));
    };
  }, []);

  const cachedOnLoadValuesForKey = useCallback(() => {
    let result = undefined;
    return async (key: string, search?: string) => {
      if (!result) {
        try {
          const { values } = await labelsStore.loadValuesForKey(key, search);
          result = values;
        } catch (error) {
          openErrorNotification('There was an error processing your request. Please try again');
        }
      }

      return result.filter((k) => k.name.toLowerCase().includes(search.toLowerCase()));
    };
  }, []);

  return (
    <VerticalGroup>
      <HorizontalGroup spacing="xs" align="flex-start">
        <Label>Custom labels</Label>
      </HorizontalGroup>
      <ServiceLabels
        isAddingDisabled
        loadById
        inputWidth={INPUT_WIDTH}
        value={alertGroupLabels.custom}
        onLoadKeys={cachedOnLoadKeys()}
        onLoadValuesForKey={cachedOnLoadValuesForKey()}
        onCreateKey={labelsStore.createKey.bind(labelsStore)}
        onUpdateKey={labelsStore.updateKey.bind(labelsStore)}
        onCreateValue={labelsStore.createValue.bind(labelsStore)}
        onUpdateValue={labelsStore.updateKeyValue.bind(labelsStore)}
        onUpdateError={(res) => {
          if (res?.response?.status === 409) {
            openErrorNotification(`Duplicate values are not allowed`);
          } else {
            openErrorNotification('An error has occurred. Please try again');
          }
        }}
        // errors={isValid() ? {} : { ...propsErrors }}
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
      />
      <Dropdown
        overlay={
          <Menu>
            <Menu.Item label="Plain label" onClick={handlePlainLabelAdd} />
            <Menu.Item label="Templated label" onClick={handleTemplatedLabelAdd} />
          </Menu>
        }
      >
        <Button variant="secondary" icon="plus">
          Add
        </Button>
      </Dropdown>
    </VerticalGroup>
  );
};

export default IntegrationLabelsForm;
