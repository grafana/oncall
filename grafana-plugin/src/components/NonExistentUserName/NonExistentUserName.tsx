import React, { ComponentProps, FC } from 'react';

import { HorizontalGroup, Icon, Tooltip } from '@grafana/ui';

interface NonExistentUserNameProps {
  justify?: ComponentProps<typeof HorizontalGroup>['justify'];
  userName?: string;
}

const NonExistentUserName: FC<NonExistentUserNameProps> = ({ justify = 'space-between', userName }) => (
  <HorizontalGroup justify={justify}>
    <span>Missing user</span>
    <Tooltip content={`${userName || 'User'} } is not found or doesn't have permission to participate in the rotation`}>
      <Icon name="exclamation-triangle" />
    </Tooltip>
  </HorizontalGroup>
);

export default NonExistentUserName;
