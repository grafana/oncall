import React, { useCallback, useState } from 'react';

import {
  AsyncSelect,
  Button,
  Drawer,
  Dropdown,
  HorizontalGroup,
  Icon,
  InlineSwitch,
  Input,
  Label,
  Menu,
  TextArea,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { LabelKey } from 'models/label/label.types';
import { useStore } from 'state/useStore';

import styles from './IntegrationLabelsForm.module.css';

import Collapse from 'components/Collapse/Collapse';
import MonacoEditor, { MONACO_LANGUAGE } from 'components/MonacoEditor/MonacoEditor';
import IntegrationTemplate from 'containers/IntegrationTemplate/IntegrationTemplate';

const cx = cn.bind(styles);

interface IntegrationLabelsFormProps {
  id: AlertReceiveChannel['id'];
  onSubmit: () => void;
  onHide: () => void;
  onOpenIntegraionSettings: (id: AlertReceiveChannel['id']) => void;
}

const IntegrationLabelsForm = observer((props: IntegrationLabelsFormProps) => {
  const { id, onHide, onSubmit, onOpenIntegraionSettings } = props;

  const store = useStore();

  const [customLabelIndexToShowTemplateEditor, setCustomLabelIndexToShowTemplateEditor] = useState<number>(1);

  const { alertReceiveChannelStore, labelsStore } = store;

  const alertReceiveChannel = alertReceiveChannelStore.items[id];

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
                      <Input width={38} value={label.key.name} disabled />
                      <Input width={31} value={label.value.name} disabled />
                      <InlineSwitch
                        value={alertGroupLabels.inheritable[label.key.id]}
                        transparent
                        onChange={getInheritanceChangeHandler(label.key.id)}
                      />
                    </HorizontalGroup>
                  </li>
                ))}{' '}
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

          {/* <CustomLabels alertGroupLabels={alertGroupLabels} onChange={setAlertGroupLabels} /> */}

          <Collapse isOpen={false} label="Advanced label templating">
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
          template={{ name: 'alert_group_labels', displayName: 'alert_group_labels' }}
          templateBody="asdfasdf"
          onHide={() => setCustomLabelIndexToShowTemplateEditor(undefined)}
        />
      )}
    </>
  );
});

interface CustomLabelsProps {
  alertGroupLabels: AlertReceiveChannel['alert_group_labels'];
  onChange: (value: AlertReceiveChannel['alert_group_labels']) => void;
}

const CustomLabels = (props: CustomLabelsProps) => {
  const { alertGroupLabels, onChange } = props;

  const handlePlainLabelAdd = () => {
    onChange({ ...alertGroupLabels, custom: [...alertGroupLabels.custom, { key: '', value: '', template: false }] });
  };
  const handleTemplatedLabelAdd = () => {
    onChange({ ...alertGroupLabels, custom: [...alertGroupLabels.custom, { key: '', value: '', template: false }] });
  };

  return (
    <VerticalGroup>
      <HorizontalGroup spacing="xs" align="flex-start">
        <Label>Alert group labels</Label>
        <Tooltip content="Custom labels">
          <Icon name="info-circle" className={cx('extra-fields__icon')} />
        </Tooltip>
      </HorizontalGroup>
      {alertGroupLabels.custom.map(({ key, value, template }, index) => (
        <HorizontalGroup key={key} spacing="xs" align="flex-start">
          <Input width={38} value={key} />

          <Input
            width={31}
            value={value}
            addonAfter={template ? <Button variant="secondary" icon="edit" /> : undefined}
          />
          <Button
            icon="times"
            variant="secondary"
            onClick={() => {
              const newValue = { ...alertGroupLabels, custom: alertGroupLabels.custom.toSpliced(index, 1) };

              onChange(newValue);
            }}
          />
        </HorizontalGroup>
      ))}
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
