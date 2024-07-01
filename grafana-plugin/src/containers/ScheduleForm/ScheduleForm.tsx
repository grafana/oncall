import React, { useCallback, useMemo } from 'react';

import { css } from '@emotion/css';
import {
  Button,
  Drawer,
  Field,
  HorizontalGroup,
  Input,
  Switch,
  TextArea,
  VerticalGroup,
  useStyles2,
} from '@grafana/ui';
import { observer } from 'mobx-react';
import { Controller, FormProvider, useForm, useFormContext } from 'react-hook-form';
import { getUtilStyles } from 'styles/utils.styles';

import { Collapse } from 'components/Collapse/Collapse';
import { GSelect } from 'containers/GSelect/GSelect';
import { RemoteSelect } from 'containers/RemoteSelect/RemoteSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { UserGroup } from 'models/user_group/user_group.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { openWarningNotification } from 'utils/utils';

import { prepareForEdit } from './ScheduleForm.helpers';

interface ScheduleFormProps {
  id: Schedule['id'] | 'new';
  onHide: () => void;
  onSubmit: (data: Schedule) => void;
  type?: ScheduleType;
}

interface FormFields extends Omit<Schedule, 'user_group'> {
  slack_channel_id: SlackChannel['id'];
  user_group: UserGroup['id'];
}

export const ScheduleForm = observer((props: ScheduleFormProps) => {
  const { id, type, onSubmit: propsOnSubmit, onHide } = props;
  const isNew = id === 'new';

  const store = useStore();

  const { scheduleStore, userStore } = store;

  const data = useMemo(() => {
    return isNew ? { team: userStore.currentUser?.current_team, type } : prepareForEdit(scheduleStore.items[id]);
  }, [id]);

  const onSubmit = useCallback(
    async (formData: FormFields): Promise<void> => {
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

      propsOnSubmit(schedule);
      onHide();
    },
    [id, isNew]
  );

  /*  ---------------- */

  const formMethods = useForm<FormFields>({
    mode: 'onChange',
    defaultValues: { ...data },
  });

  const { handleSubmit } = formMethods;

  const utils = useStyles2(getUtilStyles);

  return (
    <Drawer
      scrollableContent
      title={id === 'new' ? 'New Schedule' : 'Edit Schedule'}
      onClose={onHide}
      closeOnMaskClick={false}
    >
      <VerticalGroup>
        <FormProvider {...formMethods}>
          <form id="Schedule" data-testid="schedule-form" onSubmit={handleSubmit(onSubmit)} className={utils.width100}>
            <FormFields scheduleType={data.type} />
            <div className="buttons">
              <HorizontalGroup justify="flex-end">
                <Button variant="secondary" onClick={onHide}>
                  Cancel
                </Button>
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <Button type="submit">{id === 'new' ? 'Create' : 'Update'} Schedule</Button>
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </div>
          </form>
        </FormProvider>
      </VerticalGroup>
    </Drawer>
  );
});

const FormFields = ({ scheduleType }: { scheduleType: Schedule['type'] }) => {
  const { control, formState } = useFormContext<FormFields>();
  const { errors } = formState;

  switch (scheduleType) {
    case ScheduleType.Calendar:
      return (
        <>
          <ScheduleCommonFields />
          <Controller
            name="enable_web_overrides"
            control={control}
            render={({ field }) => (
              <Field
                label="Enable web interface overrides"
                invalid={Boolean(errors.enable_web_overrides)}
                error={errors.enable_web_overrides?.message}
              >
                <Switch value={field.value} onChange={field.onChange} />
              </Field>
            )}
          />
          <Controller
            name="ical_url_overrides"
            control={control}
            render={({ field }) => (
              <Field
                label="Overrides schedule iCal URL"
                invalid={Boolean(errors.ical_url_overrides)}
                error={errors.ical_url_overrides?.message}
              >
                <TextArea rows={2} value={field.value} onChange={field.onChange} />
              </Field>
            )}
          />
          <ScheduleNotificationSettingsFields />
        </>
      );
    case ScheduleType.Ical:
      return (
        <>
          <ScheduleCommonFields />
          <Controller
            name="ical_url_primary"
            rules={{ required: 'Primary schedule is required' }}
            control={control}
            render={({ field }) => (
              <Field
                label="Primary schedule iCal URL"
                invalid={Boolean(errors.ical_url_primary)}
                error={errors.ical_url_primary?.message}
              >
                <TextArea rows={2} value={field.value} onChange={field.onChange} />
              </Field>
            )}
          />
          <Controller
            name="ical_url_overrides"
            control={control}
            render={({ field }) => (
              <Field
                label="Overrides schedule iCal URL"
                invalid={Boolean(errors.ical_url_overrides)}
                error={errors.ical_url_overrides?.message}
              >
                <TextArea rows={2} value={field.value} onChange={field.onChange} />
              </Field>
            )}
          />
          <ScheduleNotificationSettingsFields />
        </>
      );
    case ScheduleType.API:
      return (
        <>
          <ScheduleCommonFields />
          <ScheduleNotificationSettingsFields />
        </>
      );
  }
};

const ScheduleCommonFields = () => {
  const { grafanaTeamStore } = useStore();

  const { control, formState } = useFormContext<FormFields>();
  const { errors } = formState;

  return (
    <>
      <Controller
        name="name"
        control={control}
        rules={{ required: 'Name is required' }}
        render={({ field }) => (
          <Field label="Name" invalid={Boolean(errors.name)} error={errors.name?.message}>
            <Input name="name" value={field.value} onChange={field.onChange} />
          </Field>
        )}
      />
      <Controller
        name="team"
        control={control}
        render={({ field }) => (
          <Field label="Assign to team" invalid={!!errors.team} error={errors.team?.message}>
            <GSelect<GrafanaTeam>
              items={grafanaTeamStore.items}
              fetchItemsFn={grafanaTeamStore.updateItems}
              fetchItemFn={grafanaTeamStore.fetchItemById}
              getSearchResult={grafanaTeamStore.getSearchResult}
              displayField="name"
              valueField="id"
              placeholder="Select Team"
              value={field.value}
              onChange={field.onChange}
            />
          </Field>
        )}
      />
    </>
  );
};

const ScheduleNotificationSettingsFields = () => {
  const store = useStore();

  const styles = useStyles2(getStyles);

  const { slackChannelStore, userGroupStore } = store;

  const {
    control,
    formState: { errors },
  } = useFormContext<FormFields>();

  return (
    <Collapse isOpen={false} label="Notification settings" className={styles.collapse}>
      <Controller
        name="slack_channel_id"
        control={control}
        render={({ field }) => (
          <Field
            label="Slack channel"
            description="Calendar parsing errors and notifications about the new on-call shift will be published in this channel."
            invalid={!!errors.slack_channel_id}
            error={errors.slack_channel_id?.message}
          >
            <GSelect<SlackChannel>
              allowClear
              items={slackChannelStore.items}
              fetchItemsFn={slackChannelStore.updateItems}
              fetchItemFn={slackChannelStore.updateItem}
              getSearchResult={slackChannelStore.getSearchResult}
              displayField="display_name"
              valueField="id"
              placeholder="Select Slack Channel"
              value={field.value}
              onChange={field.onChange}
              nullItemName={PRIVATE_CHANNEL_NAME}
            />
          </Field>
        )}
      />
      <Controller
        name="user_group"
        control={control}
        render={({ field }) => (
          <Field
            label="Slack user group"
            description="Group members will be automatically updated with current on-call. In case you want to ping on-call with @group_name."
            invalid={!!errors.user_group}
            error={errors.user_group?.message}
          >
            <GSelect<UserGroup>
              allowClear
              items={userGroupStore.items}
              fetchItemsFn={userGroupStore.updateItems}
              fetchItemFn={userGroupStore.fetchItemById}
              getSearchResult={userGroupStore.getSearchResult}
              displayField="handle"
              placeholder="Select User Group"
              value={field.value}
              onChange={field.onChange}
            />
          </Field>
        )}
      />
      <Controller
        name="notify_oncall_shift_freq"
        control={control}
        render={({ field }) => (
          <Field
            label="Notification frequency"
            description="Specify the frequency that shift notifications are sent to scheduled team members."
            invalid={!!errors.notify_oncall_shift_freq}
            error={errors.notify_oncall_shift_freq?.message}
          >
            <RemoteSelect
              showSearch
              openMenuOnFocus={false}
              fieldToShow="display_name"
              href="/schedules/notify_oncall_shift_freq_options/"
              value={field.value}
              onChange={field.onChange}
            />
          </Field>
        )}
      />
      <Controller
        name="notify_empty_oncall"
        control={control}
        render={({ field }) => (
          <Field
            label="Action for slot when no one is on-call"
            description="Specify how to notify team members when there is no one scheduled for an on-call shift."
            invalid={!!errors.notify_oncall_shift_freq}
            error={errors.notify_oncall_shift_freq?.message}
          >
            <RemoteSelect
              showSearch
              openMenuOnFocus={false}
              fieldToShow="display_name"
              href="/schedules/notify_empty_oncall_options/"
              value={field.value}
              onChange={(value) => {
                field.onChange(value);
              }}
            />
          </Field>
        )}
      />
      <Controller
        name="mention_oncall_start"
        control={control}
        render={({ field }) => (
          <Field
            label="Current shift notification settings"
            description="Specify how to notify a team member when their on-call shift begins."
            invalid={!!errors.notify_oncall_shift_freq}
            error={errors.notify_oncall_shift_freq?.message}
          >
            <RemoteSelect
              showSearch
              openMenuOnFocus={false}
              fieldToShow="display_name"
              href="/schedules/mention_options/"
              value={field.value}
              onChange={(value) => {
                field.onChange(value);
              }}
            />
          </Field>
        )}
      />
      <Controller
        name="mention_oncall_next"
        control={control}
        render={({ field }) => (
          <Field
            label="Next shift notification settings"
            description="Specify how to notify a team member when their shift is the next one scheduled."
            invalid={!!errors.notify_oncall_shift_freq}
            error={errors.notify_oncall_shift_freq?.message}
          >
            <RemoteSelect
              showSearch
              openMenuOnFocus={false}
              fieldToShow="display_name"
              href="/schedules/mention_options/"
              value={field.value}
              onChange={(value) => {
                field.onChange(value);
              }}
            />
          </Field>
        )}
      />
    </Collapse>
  );
};

export const getStyles = () => ({
  collapse: css`
    margin-bottom: 16px;
  `,
});
