import React, { ReactElement } from 'react';

import { Stack } from '@grafana/ui';
import { isUserActionAllowed, UserAction } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';

import { Text } from 'components/Text/Text';

interface WithPermissionControlDisplayProps {
  userAction: UserAction;
  children: ReactElement;
  message?: string;
  title?: string;
}

export const WithPermissionControlDisplay: React.FC<WithPermissionControlDisplayProps> = (props) => {
  const {
    userAction,
    children,
    title,
    message = 'You do not have permission to perform this action. Ask an admin to upgrade your permissions.',
  } = props;

  const hasPermission = isUserActionAllowed(userAction);

  return hasPermission ? (
    children
  ) : (
    <Stack direction="column" gap={StackSize.lg}>
      {title && <Text.Title level={3}>{title}</Text.Title>}
      <Text>{message}</Text>
    </Stack>
  );
};
