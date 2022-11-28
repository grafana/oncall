import React, { FC } from 'react';

import { Button } from '@grafana/ui';

import WithConfirm from 'components/WithConfirm/WithConfirm';

type Props = {
  onClick: () => void;
};

// TODO: right now this shows a confirmation pop-up modal on top of the user settings modal, do we want to maybe change this?
const DisconnectButton: FC<Props> = ({ onClick }) => (
  <WithConfirm title="Are you sure to disconnect your mobile application?" confirmText="Remove">
    <Button variant="destructive" onClick={onClick} size="md">
      Disconnect
    </Button>
  </WithConfirm>
);

export default DisconnectButton;
