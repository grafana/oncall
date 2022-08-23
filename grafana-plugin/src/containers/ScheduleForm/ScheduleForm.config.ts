import { ReactElement } from 'react';

import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { DEFAULT_USER_ROLES } from 'models/user/user.config';

const commonFields: FormItem[] = [
  {
    name: 'ical_url_overrides',
    label: 'Overrides schedule iCal URL ',
    type: FormItemType.TextArea,
    description:
      'You can use an override calendar to share with your team members. Users can add \n' +
      'events to this calendar, and they will override existing events in the primary \n' +
      'calendar. The iCal URL for your override calendar can be found in the calendar \n' +
      'integration settings of your calendar service.',
  },
  {
    name: 'slack_channel_id',
    label: 'Slack channel',
    type: FormItemType.GSelect,
    extra: {
      modelName: 'slackChannelStore',
      displayField: 'display_name',
      showSearch: true,
      allowClear: true,
      nullItemName: PRIVATE_CHANNEL_NAME,
    },
    description:
      'Calendar parsing errors and notifications about the new on-call shift will be published in this channel.',
  },
  {
    name: 'notify_oncall_shift_freq',
    label: 'Notification frequency',
    type: FormItemType.RemoteSelect,
    normalize: (value) => value,
    extra: {
      href: '/schedules/notify_oncall_shift_freq_options/',
      displayField: 'display_name',
      openMenuOnFocus: false,
    },
    description: 'Specify the frequency that shift notifications are sent to scheduled team members.',
  },
  {
    name: 'notify_empty_oncall',
    label: 'Action for slot when no one is on-call',
    type: FormItemType.RemoteSelect,
    normalize: (value) => value,
    extra: {
      href: '/schedules/notify_empty_oncall_options/',
      displayField: 'display_name',
      openMenuOnFocus: false,
    },
    description: 'Specify how to notify team members when there is no one scheduled for an on-call shift.',
  },
  {
    name: 'mention_oncall_start',
    label: 'Current shift notification settings',
    type: FormItemType.RemoteSelect,
    normalize: (value) => value,
    extra: {
      href: '/schedules/mention_options/',
      displayField: 'display_name',
      openMenuOnFocus: false,
    },
    description: 'Specify how to notify a team member when their on-call shift begins ',
  },
  {
    name: 'mention_oncall_next',
    label: 'Next shift notification settings',
    type: FormItemType.RemoteSelect,
    normalize: (value) => value,
    extra: {
      href: '/schedules/mention_options/',
      displayField: 'display_name',
      openMenuOnFocus: false,
    },
    description: 'Specify how to notify a team member when their shift is the next one scheduled',
  },
  {
    name: 'user_group',
    label: 'Slack user group',
    type: FormItemType.GSelect,
    extra: {
      modelName: 'userGroupStore',
      displayField: 'handle',
      showSearch: true,
      allowClear: true,
    },
    description:
      'Group members will be automatically updated with current on-call. In case you want to ping on-call with @group_name.',
  },
  // {
  //   name: 'send_empty_shifts_report',
  //   normalize: (value) => Boolean(value),
  //   label: 'Send reports about empty shifts to Slack',
  //   type: FormItemType.Switch,
  // },
  {
    name: 'team',
    label: 'Assign to team',
    type: FormItemType.GSelect,
    extra: {
      modelName: 'grafanaTeamStore',
      displayField: 'name',
      valueField: 'id',
      showSearch: true,
      allowClear: true,
    },
  },
];

export const iCalForm: { name: string; fields: FormItem[] } = {
  name: 'Schedule',
  fields: [
    {
      name: 'name',
      type: FormItemType.Input,
      validation: { required: true },
    },
    {
      name: 'ical_url_primary',
      label: 'Primary schedule iCal URL',
      type: FormItemType.TextArea,
      validation: { required: true },
      description:
        'You can use the primary scheduling calendar as a base schedule with restricted  \n' +
        'access. The iCal URL for your primary calendar can be found in the calendar \n' +
        'integration settings of your calendar service.',
    },
    ...commonFields,
  ],
};

export const calendarForm: { name: string; fields: FormItem[] } = {
  name: 'Schedule',
  fields: [
    {
      name: 'name',
      type: FormItemType.Input,
      validation: { required: true },
    },
    ...commonFields,
  ],
};
