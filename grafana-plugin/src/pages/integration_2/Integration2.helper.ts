import { ChannelFilter } from 'models/channel_filter';
import { MAX_CHARACTERS_COUNT, TEXTAREA_ROWS_COUNT } from './Integration2.config';

const IntegrationHelper = {
  getFilteredTemplate: (template: string, isTextArea: boolean): string => {
    if (!template) return '';

    const lines = template.split('\n');
    if (isTextArea) {
      return lines
        .slice(0, TEXTAREA_ROWS_COUNT + 1)
        .map((line) => IntegrationHelper.truncateLine(line))
        .join('\n');
    }

    return IntegrationHelper.truncateLine(lines[0]);
  },

  truncateLine: (line: string): string => {
    const slice = line.substring(0, MAX_CHARACTERS_COUNT);
    return slice.length === line.length ? slice : `${slice} ...`;
  },

  getRouteConditionWording(channelFilters: { [id: string]: ChannelFilter }, routeIndex) {
    const totalCount = Object.keys(channelFilters).length;
    if (routeIndex === totalCount - 1) {
      return 'Default';
    }
    return routeIndex ? 'Else' : 'If';
  }
};

export default IntegrationHelper;
