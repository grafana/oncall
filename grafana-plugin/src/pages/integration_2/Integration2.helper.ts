import dayjs from 'dayjs';

import { MaintenanceMode } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter } from 'models/channel_filter';

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

  getRouteConditionWording(channelFilters: ChannelFilter['id'][], routeIndex: number) {
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
    const totalDiffString = `${hourDiff}h ${totalMinDiff}m left`;

    if (mode !== undefined) {
      return `${mode === MaintenanceMode.Debug ? 'Debug Maintenance' : 'Maintenance'}: ${totalDiffString}`;
    }

    return `${hourDiff}h left`;
  },
};

export default IntegrationHelper;
