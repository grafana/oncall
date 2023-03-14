import React, { FC, useCallback, useState } from 'react';

import { Button, Drawer, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import GForm from 'components/GForm/GForm';
import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import Text from 'components/Text/Text';
import EscalationVariants from 'containers/EscalationVariants/EscalationVariants';
import { prepareForUpdate } from 'containers/EscalationVariants/EscalationVariants.helpers';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';

import styles from './ManualAlertGroup.module.css';

interface ManualAlertGroupProps {
  onHide: () => void;
  onCreate: (id: Alert['pk']) => void;
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
      name: 'message',
      type: FormItemType.TextArea,
      label: 'Describe what is going on',
    },
  ],
};

const ManualAlertGroup: FC<ManualAlertGroupProps> = (props) => {
  const store = useStore();
  const [userResponders, setUserResponders] = useState([]);
  const [scheduleResponders, setScheduleResponders] = useState([]);
  const { onHide, onCreate } = props;
  const data = {};

  const handleFormSubmit = async (data) => {
    store.directPagingStore
      .createManualAlertRule(prepareForUpdate(userResponders, scheduleResponders, data))
      .then(({ alert_group_id: id }: { alert_group_id: Alert['pk'] }) => {
        onCreate(id);
      })
      .finally(() => {
        onHide();
      });
  };

  const onUpdateEscalationVariants = useCallback(
    (value) => {
      setUserResponders(value.userResponders);

      setScheduleResponders(value.scheduleResponders);
    },
    [userResponders, scheduleResponders]
  );

  return (
    <>
      <Drawer scrollableContent title="Create manual alert group" onClose={onHide} closeOnMaskClick>
        <VerticalGroup spacing="lg">
          <EscalationVariants
            value={{ userResponders, scheduleResponders }}
            onUpdateEscalationVariants={onUpdateEscalationVariants}
          />
          <GForm form={manualAlertFormConfig} data={data} onSubmit={handleFormSubmit} />
          {store.teamStore.currentTeam.slack_team_identity && (
            <Block className={cx('info-block')}>
              <Icon name="info-circle" />{' '}
              <Text type="secondary">
                The alert group will also be posted to #{store.teamStore.currentTeam?.slack_channel?.display_name} Slack
                channel.
              </Text>
            </Block>
          )}
          <HorizontalGroup justify="flex-end">
            <Button variant="secondary" onClick={onHide}>
              Cancel
            </Button>
            <Button
              type="submit"
              form={manualAlertFormConfig.name}
              disabled={!userResponders.length && !scheduleResponders.length}
            >
              Create
            </Button>
          </HorizontalGroup>
        </VerticalGroup>
      </Drawer>
    </>
  );
};

export default ManualAlertGroup;
