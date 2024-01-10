import { AppFeature } from 'state/features';
import { KeyValuePair } from 'utils';

import { BASE_INTEGRATION_TEMPLATES_LIST, BaseTemplateOptions } from './IntegrationCommon.config';

export const MsTeamsTemplateOptions = {
  MSTeams: new KeyValuePair('Microsoft Teams', 'Microsoft Teams'),
  MSTeamsTitle: new KeyValuePair('MSTeams Title', 'Title'),
  MSTeamsMessage: new KeyValuePair('MSTeams Message', 'Message'),
  MSTeamsImage: new KeyValuePair('MSTeams Image', 'Image'),
};

export const getTemplateOptions = (features: Record<string, boolean>) => {
  if (features[AppFeature.MsTeams]) {
    return {
      ...BaseTemplateOptions,
      ...MsTeamsTemplateOptions,
    };
  }
  return BaseTemplateOptions;
};

export const getIntegrationTemplatesList = (features: Record<string, boolean>) => {
  if (features[AppFeature.MsTeams]) {
    return [
      ...BASE_INTEGRATION_TEMPLATES_LIST,

      {
        label: MsTeamsTemplateOptions.MSTeams.value,
        value: MsTeamsTemplateOptions.MSTeams.key,
        children: [
          {
            label: MsTeamsTemplateOptions.MSTeamsTitle.value,
            value: MsTeamsTemplateOptions.MSTeamsTitle.key,
          },
          {
            label: MsTeamsTemplateOptions.MSTeamsMessage.value,
            value: MsTeamsTemplateOptions.MSTeamsMessage.key,
          },
          {
            label: MsTeamsTemplateOptions.MSTeamsImage.value,
            value: MsTeamsTemplateOptions.MSTeamsImage.key,
          },
        ],
      },
    ];
  }

  return BASE_INTEGRATION_TEMPLATES_LIST;
};
