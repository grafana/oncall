import React, { FC } from 'react';

import { cx } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import { ActionMeta, HorizontalGroup, IconButton, useStyles2 } from '@grafana/ui';

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
      <HorizontalGroup justify="space-between">
        <HorizontalGroup>
          <div className={cx(styles.timelineIconBackground, { 'timeline-icon-background--green': true })}>
            <Avatar size="medium" src={avatar} />
          </div>
          <Text className={styles.responderName}>{username}</Text>
        </HorizontalGroup>
        <HorizontalGroup>
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
        </HorizontalGroup>
      </HorizontalGroup>
    </li>
  );
};
