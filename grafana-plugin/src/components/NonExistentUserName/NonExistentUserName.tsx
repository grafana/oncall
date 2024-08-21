import React, { ComponentProps, FC } from 'react';

import { Icon, Stack, Tooltip } from '@grafana/ui';

interface NonExistentUserNameProps {
  justify?: ComponentProps<typeof Stack>['justifyContent'];
  userName?: string;
}

const NonExistentUserName: FC<NonExistentUserNameProps> = ({ justify = 'space-between', userName }) => (
  <Stack justifyContent={justify}>
    <span>Missing user</span>
    <Tooltip content={`${userName || 'User'} } is not found or doesn't have permission to participate in the rotation`}>
      <Icon name="exclamation-triangle" />
    </Tooltip>
  </Stack>
);

export default NonExistentUserName;
