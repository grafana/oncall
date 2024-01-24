import React, { FC, useEffect, useState } from 'react';

import { Icon, IconButton } from '@grafana/ui';
import CopyToClipboard from 'react-copy-to-clipboard';

interface CopyToClipboardProps {
  text: string;
  iconButtonProps?: Partial<Parameters<typeof IconButton>[0]>;
}

let timer: NodeJS.Timeout;

const CopyToClipboardIcon: FC<CopyToClipboardProps> = ({ text, iconButtonProps }) => {
  const [showConfirmation, setShowConfirmation] = useState(false);

  const onCopy = () => {
    setShowConfirmation(true);
    timer = setTimeout(() => {
      setShowConfirmation(false);
    }, 2000);
  };

  useEffect(() => () => clearTimeout(timer), []);

  return (
    <CopyToClipboard text={text} onCopy={onCopy}>
      {showConfirmation ? (
        <Icon aria-label="Copied" name="check" color="green" />
      ) : (
        <IconButton aria-label="Copy" name="copy" {...iconButtonProps} />
      )}
    </CopyToClipboard>
  );
};

export default CopyToClipboardIcon;
