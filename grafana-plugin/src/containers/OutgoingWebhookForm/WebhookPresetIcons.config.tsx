import React from 'react';

import MachineLearningLogo from 'icons/MachineLearningLogo';
import { AppFeature } from 'state/features';

import { commonWebhookPresetIconsConfig } from './CommonWebhookPresetIcons.config';

export const additionalWebhookPresetIcons: { [id: string]: () => React.ReactElement } = {
  machine_learning: () => <MachineLearningLogo />,
};

export const getWebhookPresetIcons = (features: Record<string, boolean>) => {
  if (features?.[AppFeature.MsTeams]) {
    return { ...commonWebhookPresetIconsConfig, ...additionalWebhookPresetIcons };
  }

  return commonWebhookPresetIconsConfig;
};
