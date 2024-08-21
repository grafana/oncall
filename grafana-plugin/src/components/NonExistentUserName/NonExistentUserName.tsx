import React, { ComponentProps, FC } from 'react';

import { HorizontalGroup, Icon, Stack, Tooltip } from '@grafana/ui';

interface NonExistentUserNameProps {
  justify?: ComponentProps<typeof HorizontalGroup>['justify'];
  userName?: string;
}

const NonExistentUserName: FC<NonExistentUserNameProps> = ({ justify = 'space-between', userName }) => (
  <Stack justify={justify}>
    <span>Missing user</span>
    <Tooltip content={`${userName || 'User'} } is not found or doesn't have permission to participate in the rotation`}>
      <Icon name="exclamation-triangle" />
    </Tooltip>
  </Stack>
);

export default NonExistentUserName;
