import React, { ReactElement, useMemo } from 'react';

import { Tooltip } from '@grafana/ui';
import { observer } from 'mobx-react';

import { useStore } from 'state/useStore';
import { UserAction } from 'utils/authorization';

interface WithPermissionControlProps {
  userAction: UserAction;
  children: (disabled?: boolean) => ReactElement;
}

export const WithPermissionControl = observer((props: WithPermissionControlProps) => {
  const { userAction, children } = props;

  const store = useStore();

  const disabled = !store.isUserActionAllowed(userAction);

  const element = useMemo(() => children(disabled), [disabled]);

  return disabled ? (
    <Tooltip
      content="You do not have permission to perform this action. Ask an admin to upgrade your permissions."
      placement="top"
    >
      <span>{element}</span>
    </Tooltip>
  ) : (
    element
  );
});
