import { ChannelFilter } from 'models/channel_filter/channel_filter.types';

const CommonIntegrationHelper = {
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
      return 'If the alert payload does not match to the previous routes, it will go to this default route.';
    }
    return 'If Routing Template is True for incoming alert payload, it will be go only to this route. Alert will be grouped based on Grouping Template and escalated';
  },
};

export default CommonIntegrationHelper;
