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
  WithContextMenu,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { LabelKey } from 'models/label/label.types';
import { useStore } from 'state/useStore';

import styles from './IntegrationLabelsForm.module.css';

import Collapse from 'components/Collapse/Collapse';

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

        <CustomLabels
          alertGroupLabels={alertGroupLabels}
          onChange={(value) => {
            setAlertGroupLabels((alertGroupLabels) => ({
              ...alertGroupLabels,
              custom: value,
            }));
          }}
        />

        <Collapse isOpen={false} label="Advanced label templating">
          <TextArea value={alertGroupLabels.template} rows={10} />
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
  );
});

interface CustomLabelsProps {
  alertGroupLabels: AlertReceiveChannel['alert_group_labels'];
  onChange: (value: AlertReceiveChannel['alert_group_labels']['custom']) => void;
}

type NewLabelType = 'plain' | 'templated';

const CustomLabels = (props: CustomLabelsProps) => {
  const { alertGroupLabels, onChange } = props;

  const { labelsStore } = useStore();

  const [newLabelType, setNewLabelType] = useState<NewLabelType>();
  const [newLabel, setNewLabel] = useState<Record<string, string>>();

  const loadKeys = () => {
    return labelsStore.loadKeys().then((data) => data.map(({ id, name }) => ({ label: name, value: name, keyId: id })));
  };

  const getOnChangeKeyFn = () => {};

  const getLoadOptionsFn = (keyId: LabelKey['id']) => {
    return () => {
      return labelsStore
        .loadValuesForKey(keyId)
        .then(({ values }) => values.map(({ name }) => ({ label: name, value: name })));
    };
  };

  const getOnChangeValueFn = () => {};

  const handlePlainLabelAdd = () => {
    setNewLabelType('plain');
    setNewLabel({});
  };
  const handleTemplatedLabelAdd = () => {
    setNewLabelType('templated');
    setNewLabel({});
  };

  console.log('newLabel', newLabel);

  return (
    <VerticalGroup>
      <HorizontalGroup spacing="xs" align="flex-start">
        <Label>Alert group labels</Label>
        <Tooltip content="Custom labels">
          <Icon name="info-circle" className={cx('extra-fields__icon')} />
        </Tooltip>
      </HorizontalGroup>
      {Object.keys(alertGroupLabels.custom).map((key) => (
        <HorizontalGroup key={key} spacing="xs" align="flex-start">
          <AsyncSelect value={key} loadOptions={loadKeys} onChange={getOnChangeKeyFn} />
          <AsyncSelect
            value={alertGroupLabels.custom[key]}
            loadOptions={getLoadOptionsFn(key)}
            onChange={getOnChangeValueFn}
          />
        </HorizontalGroup>
      ))}
      {newLabel ? (
        <HorizontalGroup key="new" spacing="xs" align="flex-start">
          <AsyncSelect
            width={38}
            placeholder="Select key"
            value={newLabel.key ? { label: newLabel.key, value: newLabel.key } : undefined}
            defaultOptions
            loadOptions={loadKeys}
            onChange={({ value, keyId }) => {
              setNewLabel({ key: value, keyId, value: undefined });
            }}
          />
          {newLabelType === 'plain' ? (
            <AsyncSelect
              key={newLabel.key}
              width={31}
              placeholder="Select value"
              value={newLabel.value ? { label: newLabel.value, value: newLabel.value } : undefined}
              disabled={!newLabel.key}
              defaultOptions
              loadOptions={getLoadOptionsFn(newLabel.keyId)}
              onChange={({ value }) => {
                setNewLabel((label) => ({ ...label, value }));
              }}
            />
          ) : (
            <Input width={31} addonAfter={<Button variant="secondary" icon="edit" />} />
          )}
          <Button
            icon="times"
            variant="secondary"
            onClick={() => {
              setNewLabelType(undefined);
              setNewLabel(undefined);
            }}
          ></Button>
        </HorizontalGroup>
      ) : (
        <Dropdown
          overlay={
            <Menu>
              <Menu.Item label="Plain label" onClick={handlePlainLabelAdd} />
              <Menu.Item label="Templated label" onClick={handleTemplatedLabelAdd} />
            </Menu>
          }
        >
          <Button icon="plus">Add</Button>
        </Dropdown>
      )}
    </VerticalGroup>
  );
};

export default IntegrationLabelsForm;
