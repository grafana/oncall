import { ReactElement } from 'react';

import { commonWebhookPresetIconsConfig } from './CommonWebhookPresetIcons.config';

export const webhookPresetIcons: { [id: string]: () => ReactElement } = commonWebhookPresetIconsConfig;
