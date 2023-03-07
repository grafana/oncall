import React, { ReactElement } from 'react';

import { VerticalGroup } from '@grafana/ui';

import Text from 'components/Text/Text';
import { isUserActionAllowed, UserAction } from 'utils/authorization';

interface WithPermissionControlDisplayProps {
  userAction: UserAction;
  children: ReactElement;
  message: string;
  title?: string;
}

export const WithPermissionControlDisplay: React.FC<WithPermissionControlDisplayProps> = (props) => {
  const { userAction, children, title, message } = props;

  const hasPermission = isUserActionAllowed(userAction);

  return hasPermission ? (
    children
  ) : (
    <VerticalGroup spacing="lg">
      {title && <Text.Title level={3}>{title}</Text.Title>}
      <Text>{message}</Text>
    </VerticalGroup>
  );
};
