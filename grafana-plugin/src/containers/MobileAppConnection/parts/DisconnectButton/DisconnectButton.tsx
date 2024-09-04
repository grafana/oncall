import React, { FC } from 'react';

import { Button } from '@grafana/ui';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';

import { css } from '@emotion/css';

type Props = {
  onClick: () => void;
};

export const DisconnectButton: FC<Props> = ({ onClick }) => (
  <WithConfirm title="Are you sure to disconnect your mobile application?" confirmText="Remove">
    <Button
      variant="destructive"
      onClick={onClick}
      size="md"
      className={css`
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
      `}
      data-testid="test__disconnect"
    >
      Disconnect
    </Button>
  </WithConfirm>
);
