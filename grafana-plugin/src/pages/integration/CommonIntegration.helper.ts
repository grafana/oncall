import { ChannelFilter, FilteringTermType } from 'models/channel_filter/channel_filter.types';

export const CommonIntegrationHelper = {
  getRouteConditionWording(channelFilters: Array<ChannelFilter['id']>, routeIndex: number): 'Default' | 'Else' | 'If' {
    const totalCount = Object.keys(channelFilters).length;

    if (routeIndex === totalCount - 1) {
      return 'Default';
    }
    return routeIndex ? 'Else' : 'If';
  },

  getRouteConditionTooltipWording(
    channelFilters: Array<ChannelFilter['id']>,
    routeIndex: number,
    filteringTermType: FilteringTermType
  ) {
    const totalCount = Object.keys(channelFilters).length;

    if (routeIndex === totalCount - 1) {
      return 'If the alert payload does not match any of the previous routes, it will stick to the default route.';
    }

    if (filteringTermType === FilteringTermType.labels) {
      return 'Alerts will be grouped if they match these labels and then escalated';
    }

    // Templating
    return 'Alerts will be grouped based on the evaluation of the route template and then escalated';
  },
};
