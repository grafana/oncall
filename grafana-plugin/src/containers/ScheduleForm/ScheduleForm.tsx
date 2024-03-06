import React, { useCallback, useMemo } from 'react';

import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { GForm } from 'components/GForm/GForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { openWarningNotification } from 'utils/utils';

import { getApiForm, getCalendarForm, getICalForm } from './ScheduleForm.config';
import { prepareForEdit } from './ScheduleForm.helpers';

import styles from './ScheduleForm.module.css';

const cx = cn.bind(styles);

interface ScheduleFormProps {
  id: Schedule['id'] | 'new';
  onHide: () => void;
  onSubmit: (data: Schedule) => void;
  type?: ScheduleType;
}

export const ScheduleForm = observer((props: ScheduleFormProps) => {
  const { id, type, onSubmit, onHide } = props;
  const isNew = id === 'new';

  const store = useStore();

  const { scheduleStore, userStore } = store;

  const scheduleTypeToForm = {
    [ScheduleType.Calendar]: getCalendarForm(store),
    [ScheduleType.Ical]: getICalForm(store),
    [ScheduleType.API]: getApiForm(store),
  };

  const data = useMemo(() => {
    return isNew ? { team: userStore.currentUser?.current_team, type } : prepareForEdit(scheduleStore.items[id]);
  }, [id]);

  const handleSubmit = useCallback(
    async (formData: Partial<Schedule>): Promise<void> => {
      const apiData = { ...formData, type: data.type };

      let schedule: Schedule | void;
      if (isNew) {
        schedule = await scheduleStore.create<Schedule>(apiData);
      } else {
        schedule = await scheduleStore.update<Schedule>(id, apiData);
      }

      if (!schedule) {
        openWarningNotification(`There was an issue ${isNew ? 'creating' : 'updating'} the schedule. Please try again`);
        return;
      }

      onSubmit(schedule);
      onHide();
    },
    [id, isNew]
  );

  const formConfig = scheduleTypeToForm[data.type];

  return (
    <Drawer
      scrollableContent
      title={id === 'new' ? 'New Schedule' : 'Edit Schedule'}
      onClose={onHide}
      closeOnMaskClick={false}
    >
      <div className={cx('content')} data-testid="schedule-form">
        <VerticalGroup>
          <GForm form={formConfig} data={data} onSubmit={handleSubmit} />
          <div className="buttons">
            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={onHide}>
                Cancel
              </Button>
              <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                <Button form={formConfig.name} type="submit">
                  {id === 'new' ? 'Create' : 'Update'} Schedule
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </div>
        </VerticalGroup>
      </div>
    </Drawer>
  );
});
