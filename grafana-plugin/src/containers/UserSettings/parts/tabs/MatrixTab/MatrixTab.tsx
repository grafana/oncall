import React, { HTMLAttributes, useCallback } from 'react';

import { HorizontalGroup, Icon, Input, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { useStore } from 'state/useStore';
import { User } from 'models/user/user.types';

import styles from './MatrixTab.module.css';

const cx = cn.bind(styles);

interface MatrixInfoProps extends HTMLAttributes<HTMLElement> {
  userPk?: User['pk'];
}

export const MatrixInfo = observer((props: MatrixInfoProps) => {

  const userPk = props.userPk
  const store = useStore();
  const { userStore } = store;
  const { matrixStore } = store;

  const user = userStore.items[userPk];
  const user_matrix_identity = user.matrix_user_identity

  // TODO: Try using `keyof typeof user_matrix_identity` here?
  const getMatrixIdentityGenericUpdateHandler = (id_type: 'user_id' | 'paging_room_id') => useCallback(
    // "Given an id-type, return a function that will update that id-type for the user"
    async (event) => {
      const updated_id = event.target.value;

      var matrixUserIdPrimaryKey = user.matrix_user_identity?.id;
      if (matrixUserIdPrimaryKey == null) {
        // User has no associated MatrixUserId - create one for them
        const createMatrixUserIdentityResponse = await userStore.createEmptyMatrixUserIdentity(user);
        matrixUserIdPrimaryKey = createMatrixUserIdentityResponse.id
      }

      var update_payload = {}
      update_payload[id_type] = updated_id
      await matrixStore.updateMatrixUserIdentity(matrixUserIdPrimaryKey, update_payload)
    },
    [user, userStore.createEmptyMatrixUserIdentity, matrixStore.updateMatrixUserIdentity]
  )


  return (
    <VerticalGroup>

      <HorizontalGroup>
        <Text>
          User ID:
        </Text>

        <Input
          autoFocus
          onChange={getMatrixIdentityGenericUpdateHandler('user_id')}
          placeholder={user_matrix_identity == null ? "@username:example.org" : user_matrix_identity.user_id }
        />

        <Tooltip
          placement="top"
          content="@username@example.org"
        >
          <Icon size="lg" className={cx('note-icon')} name="info-circle" style={{ color: '#1890ff' }} />
        </Tooltip>
      </HorizontalGroup>

      <HorizontalGroup>
        <Text>
          Matrix Room:
        </Text>

        <Input
          onChange={getMatrixIdentityGenericUpdateHandler('paging_room_id')}
          placeholder={user_matrix_identity == null ? "#room-alias:example.org" : user_matrix_identity.paging_room_id }
        />

        <Tooltip
          placement="top"
          content="!room-id@example.org OR #room-alias@example.org"
        >
          <Icon size="lg" className={cx('note-icon')} name="info-circle" style={{ color: '#1890ff' }} />
        </Tooltip>
      </HorizontalGroup>
    </VerticalGroup>
  );
});
