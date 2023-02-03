import React, { FC } from 'react';

import { Button } from '@grafana/ui';
import cn from 'classnames/bind';

import WithConfirm from 'components/WithConfirm/WithConfirm';

import styles from './DisconnectButton.module.scss';

const cx = cn.bind(styles);

type Props = {
  onClick: () => void;
};

const DisconnectButton: FC<Props> = ({ onClick }) => (
  <WithConfirm title="Are you sure to disconnect your mobile application?" confirmText="Remove">
    <Button
      variant="destructive"
      onClick={onClick}
      size="md"
      className={cx('disconnect-button')}
      data-testid="test__disconnect"
    >
      Disconnect
    </Button>
  </WithConfirm>
);

export default DisconnectButton;
