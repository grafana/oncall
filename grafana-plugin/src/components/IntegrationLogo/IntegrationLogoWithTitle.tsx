import React, { FC } from 'react';

import { Stack } from '@grafana/ui';

import { Text } from 'components/Text/Text';
import { StackSize } from 'utils/consts';

import { IntegrationLogo, IntegrationLogoProps } from './IntegrationLogo';

interface IntegrationLogoWithTitleProps {
  integration: IntegrationLogoProps['integration'];
}

export const IntegrationLogoWithTitle: FC<IntegrationLogoWithTitleProps> = ({ integration }) => (
  <Stack gap={StackSize.xs}>
    <IntegrationLogo scale={0.08} integration={integration} />
    <Text type="primary">{integration?.display_name}</Text>
  </Stack>
);
