/*
  [oncall-private]
  Any change to this file needs to be done in the oncall-private also
*/

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

  getRouteConditionTooltipWording(channelFilters: Array<ChannelFilter['id']>, routeIndex: number) {
    const totalCount = Object.keys(channelFilters).length;

    if (routeIndex === totalCount - 1) {
      return 'If the alert payload does not match to the previous routes, it will be directed to this default route.';
    }
    return 'If the alert payload evaluates the route template as True, it will be directed to this route. It will not be evaluated against the subsequent routes.';
  },

  getMaintenanceText(maintenanceUntill: number, mode: number = undefined) {
    const date = dayjs(new Date(maintenanceUntill * 1000));
    const now = dayjs();
    const hourDiff = date.diff(now, 'hours');
    const minDiff = date.diff(now, 'minutes');
    const totalMinDiff = minDiff - hourDiff * 60;
    const totalDiffString = `${hourDiff}h ${totalMinDiff}m left`;

    if (mode !== undefined) {
      return `${mode === MaintenanceMode.Debug ? 'Debug Maintenance' : 'Maintenance'}: ${totalDiffString}`;
    }

    return `${hourDiff}h left`;
  },

  getChatOpsChannels(channelFilter: ChannelFilter) {
    const channels = [];

    if (channelFilter.notify_in_slack && channelFilter.slack_channel?.display_name) {
      channels.push(channelFilter.slack_channel.display_name);
    }
    if (channelFilter.telegram_channel) {
      channels.push(channelFilter.telegram_channel);
    }

    return channels;
  },
};

export default IntegrationHelper;
