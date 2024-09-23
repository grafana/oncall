import React, { FC } from 'react';

import { Button, useStyles2 } from '@grafana/ui';
import { getUtilStyles } from 'styles/utils.styles';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';

type Props = {
  onClick: () => void;
};

export const DisconnectButton: FC<Props> = ({ onClick }) => {
  const utilStyles = useStyles2(getUtilStyles);

  return (
    <WithConfirm title="Are you sure to disconnect your mobile application?" confirmText="Remove">
      <Button
        variant="destructive"
        onClick={onClick}
        size="md"
        className={utilStyles.centeredAbsolute}
        data-testid="test__disconnect"
      >
        Disconnect
      </Button>
    </WithConfirm>
  );
};
