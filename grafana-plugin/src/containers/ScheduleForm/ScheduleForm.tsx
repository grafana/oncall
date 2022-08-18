import React, { useCallback, useMemo } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import GForm from 'components/GForm/GForm';
import Text from 'components/Text/Text';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';

import { calendarForm, iCalForm } from './ScheduleForm.config';
import { prepareForEdit } from './ScheduleForm.helpers';

import styles from './ScheduleForm.module.css';

const cx = cn.bind(styles);

interface ScheduleFormProps {
  id: Schedule['id'] | 'new';
  onHide: () => void;
  onUpdate: () => void;
}

const ScheduleForm = observer((props: ScheduleFormProps) => {
  const { id, onUpdate, onHide } = props;

  const store = useStore();

  const { scheduleStore, userStore } = store;

  const data = useMemo(() => {
    return id === 'new'
      ? { team: userStore.currentUser?.current_team, type: ScheduleType.Ical }
      : prepareForEdit(scheduleStore.items[id]);
  }, [id]);

  const handleSubmit = useCallback(
    (formData: Partial<Schedule>) => {
      (id === 'new'
        ? scheduleStore.create({ ...formData, type: data.type })
        : scheduleStore.update(id, { ...formData, type: data.type })
      ).then(() => {
        onHide();

        onUpdate();
      });
    },
    [id]
  );

  const formConfig = data.type === ScheduleType.Ical ? iCalForm : calendarForm;

  return (
    <Drawer
      scrollableContent
      title={
        <Text.Title className={cx('title')} level={4}>
          {id === 'new' ? 'New' : 'Edit'} Schedule
        </Text.Title>
      }
      onClose={onHide}
      closeOnMaskClick
    >
      <div className={cx('content')}>
        <VerticalGroup>
          <Text type="secondary">
            Manage on-call schedules using your favourite calendar app, such as Google Calendar or Microsoft Outlook. To
            schedule on-call shifts create a new calendar and use events with the teammates usernames
          </Text>
          <GForm form={formConfig} data={data} onSubmit={handleSubmit} />
          <WithPermissionControl userAction={UserAction.UpdateSchedules}>
            <Button form={formConfig.name} type="submit">
              {id === 'new' ? 'Create' : 'Update'} Schedule
            </Button>
          </WithPermissionControl>
        </VerticalGroup>
      </div>
    </Drawer>
  );
});

export default ScheduleForm;
