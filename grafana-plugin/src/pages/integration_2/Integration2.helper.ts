/*
  [oncall-private]
  Any change to this file needs to be done in the oncall-private also
*/

import { IconName } from '@grafana/ui';
import dayjs from 'dayjs';

import { MaintenanceMode } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';

import { MAX_CHARACTERS_COUNT, TEXTAREA_ROWS_COUNT } from './Integration2.config';

const IntegrationHelper = {
  getFilteredTemplate: (template: string, isTextArea: boolean): string => {
    if (!template) {
      return '';
    }

    const lines = template.split('\n');
    if (isTextArea) {
      return lines
        .slice(0, TEXTAREA_ROWS_COUNT + 1)
        .map((line) => IntegrationHelper.truncateLine(line))
        .join('\n');
    }

    return IntegrationHelper.truncateLine(lines[0]);
  },

  truncateLine: (line: string, maxCharacterCount: number = MAX_CHARACTERS_COUNT): string => {
    if (!line || !line.trim()) {
      return '';
    }

    const slice = line.substring(0, maxCharacterCount);
    return slice.length === line.length ? slice : `${slice} ...`;
  },

  getRouteConditionWording(channelFilters: Array<ChannelFilter['id']>, routeIndex: number): 'Default' | 'Else' | 'If' {
    const totalCount = Object.keys(channelFilters).length;

    if (routeIndex === totalCount - 1) {
      return 'Default';
    }
    return routeIndex ? 'Else' : 'If';
  },

  getMaintenanceText(maintenanceUntill: number, mode: number = undefined) {
    const date = dayjs(new Date(maintenanceUntill * 1000));
    const now = dayjs();
    const hourDiff = date.diff(now, 'hours');
    const minDiff = date.diff(now, 'minutes');
    const totalMinDiff = minDiff - hourDiff * 60;
    const totalDiffString = hourDiff > 0 ? `${hourDiff}h ${totalMinDiff}m left` : `${totalMinDiff}m left`;

    if (mode !== undefined) {
      return `${mode === MaintenanceMode.Debug ? 'Debug Maintenance' : 'Maintenance'}: ${totalDiffString}`;
    }

    return totalDiffString;
  },

  getChatOpsChannels(channelFilter: ChannelFilter): Array<{ name: string; icon: IconName }> {
    const channels: Array<{ name: string; icon: IconName }> = [];

    if (channelFilter.notify_in_slack && channelFilter.slack_channel?.display_name) {
      channels.push({ name: channelFilter.slack_channel.display_name, icon: 'slack' });
    }
    if (channelFilter.telegram_channel) {
      channels.push({ name: channelFilter.telegram_channel, icon: 'telegram-alt' });
    }

    return channels;
  },
};

export default IntegrationHelper;
