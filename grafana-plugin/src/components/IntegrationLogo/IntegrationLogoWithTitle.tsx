import React, { FC } from 'react';

import { HorizontalGroup } from '@grafana/ui';

import { Text } from 'components/Text/Text';

import { IntegrationLogo, IntegrationLogoProps } from './IntegrationLogo';

interface IntegrationLogoWithTitleProps {
  integration: IntegrationLogoProps['integration'];
}

export const IntegrationLogoWithTitle: FC<IntegrationLogoWithTitleProps> = ({ integration }) => (
  <HorizontalGroup spacing="xs">
    <IntegrationLogo scale={0.08} integration={integration} />
    <Text type="primary">{integration?.display_name}</Text>
  </HorizontalGroup>
);
