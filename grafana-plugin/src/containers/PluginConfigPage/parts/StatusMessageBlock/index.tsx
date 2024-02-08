import React, { FC } from 'react';

import { Text } from 'components/Text/Text';

type Props = {
  text: string;
};

export const StatusMessageBlock: FC<Props> = ({ text }) => (
  <pre data-testid="status-message-block">
    <Text>{text}</Text>
  </pre>
);
