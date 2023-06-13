import React, { FC } from 'react';

import { Button } from '@grafana/ui';

import WithConfirm from 'components/WithConfirm/WithConfirm';

type Props = {
  disabled: boolean;
  onClick: () => void;
};

const RemoveCurrentConfigurationButton: FC<Props> = ({ disabled, onClick }) => (
  <WithConfirm title="Are you sure to delete the plugin configuration?" confirmText="Remove">
    <Button variant="destructive" onClick={onClick} size="md" disabled={disabled}>
      Remove current configuration
    </Button>
  </WithConfirm>
);

export default RemoveCurrentConfigurationButton;
