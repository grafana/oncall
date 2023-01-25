import React, { FC } from 'react';

import { Modal, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import { User } from 'models/user/user.types';

import styles from './UserWarning.module.css';

interface UserWarningProps {
  onHide: () => void;
  user?: User;
}

const cx = cn.bind(styles);

const UserWarning: FC<UserWarningProps> = (props) => {
  const { onHide, user } = props;

  //   const store = useStore();
  console.log('USER', user);
  return (
    <Modal isOpen title="This user is not on-call" onDismiss={onHide}>
      <VerticalGroup className={cx('user-warning')}>
        <Text type="secondary">{user?.username} is not currently on-call</Text>
      </VerticalGroup>
    </Modal>
  );
};

export default UserWarning;
