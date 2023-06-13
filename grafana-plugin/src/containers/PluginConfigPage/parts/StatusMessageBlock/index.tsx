import React, { FC } from 'react';

import Text from 'components/Text/Text';

type Props = {
  text: string;
};

const StatusMessageBlock: FC<Props> = ({ text }) => (
  <pre data-testid="status-message-block">
    <Text>{text}</Text>
  </pre>
);

export default StatusMessageBlock;
