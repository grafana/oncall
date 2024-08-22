import React, { FC } from 'react';

import { cx } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import { ActionMeta, IconButton, Stack, useStyles2 } from '@grafana/ui';

import { Avatar } from 'components/Avatar/Avatar';
import { Text } from 'components/Text/Text';
import { getAddRespondersStyles } from 'containers/AddResponders/AddResponders.styles';
import { UserResponder as UserResponderType } from 'containers/AddResponders/AddResponders.types';
import { NotificationPoliciesSelect } from 'containers/AddResponders/parts/NotificationPoliciesSelect/NotificationPoliciesSelect';

type Props = UserResponderType & {
  onImportantChange: (value: SelectableValue<number>, actionMeta: ActionMeta) => void | {};
  handleDelete: React.MouseEventHandler<HTMLButtonElement>;
  disableNotificationPolicySelect?: boolean;
};

export const UserResponder: FC<Props> = ({
  important,
  data: { avatar, username },
  onImportantChange,
  handleDelete,
  disableNotificationPolicySelect = false,
}) => {
  const styles = useStyles2(getAddRespondersStyles);

  return (
    <li>
      <Stack justifyContent="space-between">
        <Stack>
          <div className={cx(styles.timelineIconBackground, { 'timeline-icon-background--green': true })}>
            <Avatar size="medium" src={avatar} />
          </div>
          <Text className={styles.responderName}>{username}</Text>
        </Stack>
        <Stack>
          <NotificationPoliciesSelect
            disabled={disableNotificationPolicySelect}
            important={important}
            onChange={onImportantChange}
          />
          <IconButton
            data-testid="user-responder-delete-icon"
            tooltip="Remove responder"
            name="trash-alt"
            onClick={handleDelete}
          />
        </Stack>
      </Stack>
    </li>
  );
};
