import React, { useCallback, useState } from 'react';

import { Button, Drawer, HorizontalGroup, Icon, InlineSwitch, Input, Label, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { LabelKey } from 'models/label/label.types';
import { useStore } from 'state/useStore';

import styles from './IntegrationLabelsForm.module.css';

const cx = cn.bind(styles);

interface IntegrationLabelsFormProps {
  id: AlertReceiveChannel['id'];
  onSubmit: () => void;
  onHide: () => void;
}

const IntegrationLabelsForm = observer((props: IntegrationLabelsFormProps) => {
  const { id, onHide, onSubmit } = props;

  const store = useStore();

  const { alertReceiveChannelStore } = store;

  const alertReceiveChannel = alertReceiveChannelStore.items[id];

  const [alertGroupLabels, setAlertGroupLabels] = useState(alertReceiveChannel.alert_group_labels);

  const handleSave = useCallback(() => {
    alertReceiveChannelStore.saveAlertReceiveChannel(id, { alert_group_labels: alertGroupLabels });

    onSubmit();

    onHide();
  }, [alertGroupLabels]);

  const getInheritanceChangeHandler = (keyId: LabelKey['id']) => {
    return (event: React.ChangeEvent<HTMLInputElement>) => {
      setAlertGroupLabels((alertGroupLabels) => ({
        ...alertGroupLabels,
        inherit: { ...alertGroupLabels.inherit, [keyId]: event.target.checked },
      }));
    };
  };

  return (
    <Drawer scrollableContent title="Alert group labels" onClose={onHide} closeOnMaskClick={false} width="640px">
      <div>
        <VerticalGroup>
          <HorizontalGroup spacing="xs" align="flex-start">
            <Label>Inherited labels</Label>
            <Tooltip content="Labels inherited from integration">
              <Icon name="info-circle" className={cx('extra-fields__icon')} />
            </Tooltip>
          </HorizontalGroup>
          <ul className={cx('labels-list')}>
            {alertReceiveChannel.labels.map((label) => (
              <li key={label.key.id}>
                <HorizontalGroup spacing="xs">
                  {/* @ts-ignore */}
                  <Input width="300px" value={label.key.name} disabled />
                  {/* @ts-ignore */}
                  <Input width="250px" value={label.value.name} disabled />
                  <InlineSwitch
                    value={alertGroupLabels.inherit[label.key.id]}
                    transparent
                    onChange={getInheritanceChangeHandler(label.key.id)}
                  />
                </HorizontalGroup>
              </li>
            ))}
          </ul>
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
      </div>
    </Drawer>
  );
});

export default IntegrationLabelsForm;
