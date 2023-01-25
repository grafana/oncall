import React, { FC, useCallback, useState } from 'react';

import { Button, Drawer, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import EscalationVariants from 'components/EscalationVariants/EscalationVariants';
import Block from 'components/GBlock/Block';
import GForm from 'components/GForm/GForm';
import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import Text from 'components/Text/Text';
import { useStore } from 'state/useStore';

import styles from './ManualAlertGroup.module.css';

interface ManualAlertGroupProps {
  onHide: () => void;
}

const cx = cn.bind(styles);

const manualAlertFormConfig: { name: string; fields: FormItem[] } = {
  name: 'Manual Alert Group',
  fields: [
    {
      name: 'title',
      type: FormItemType.Input,
      label: 'Title',
      validation: { required: true },
    },
    {
      name: 'description',
      type: FormItemType.TextArea,
      label: 'Describe what is going on',
    },
  ],
};

const ManualAlertGroup: FC<ManualAlertGroupProps> = (props) => {
  const store = useStore();
  const [usersIds, setUserIds] = useState([]);
  const [schedulesIds, setSchedulesIds] = useState([]);
  const { onHide } = props;
  const data = {};

  const handleFormSubmit = async (data) => {
    console.log('FINAL DATA', { ...data, users: usersIds, schedules: schedulesIds });
    await store.directPagingStore.createManualAlertRule({ ...data, users: usersIds, schedules: schedulesIds });
    onHide();
  };

  const onUpdateEscalationVariants = useCallback(
    (value) => {
      setUserIds(value.usersIds);

      setSchedulesIds(value.schedulesIds);
    },
    [schedulesIds, usersIds]
  );

  return (
    <>
      <Drawer scrollableContent title="Create an alert group" onClose={onHide} closeOnMaskClick>
        <div className={cx('content')}>
          <VerticalGroup>
            <EscalationVariants
              value={{ schedulesIds, usersIds }}
              onUpdateEscalationVariants={onUpdateEscalationVariants}
            />

            <GForm form={manualAlertFormConfig} data={data} onSubmit={handleFormSubmit} />
            <Block className={cx('info-block')}>
              <Icon name="info-circle" />{' '}
              <Text type="secondary">
                The alert group will also be posted to <Text type="link">#general</Text> Slack channel.
              </Text>
            </Block>
          </VerticalGroup>
        </div>
        <HorizontalGroup>
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button type="submit" form={manualAlertFormConfig.name}>
            Create
          </Button>
        </HorizontalGroup>
      </Drawer>
    </>
  );
};

export default ManualAlertGroup;
