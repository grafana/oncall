import React, { FC } from 'react';

import { IconButton } from '@grafana/ui';
import { openNotification } from 'helpers/helpers';
import CopyToClipboard from 'react-copy-to-clipboard';

interface CopyToClipboardProps {
  text: string;
  iconButtonProps?: Partial<Parameters<typeof IconButton>[0]>;
}

export const CopyToClipboardIcon: FC<CopyToClipboardProps> = ({ text, iconButtonProps }) => {
  const onCopy = () => {
    openNotification('Copied to clipboard');
  };

  return (
    <CopyToClipboard text={text} onCopy={onCopy}>
      <IconButton aria-label="Copy" name="copy" {...iconButtonProps} />
    </CopyToClipboard>
  );
};
