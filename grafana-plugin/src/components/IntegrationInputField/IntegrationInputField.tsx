import React, { useState } from 'react';

import { cx } from '@emotion/css';
import { IconButton, Input, Stack, useStyles2 } from '@grafana/ui';

import { CopyToClipboardIcon } from 'components/CopyToClipboardIcon/CopyToClipboardIcon';
import { StackSize } from 'utils/consts';

import { getIntegrationInputFieldStyles } from './IntegrationInputField.styles';

interface IntegrationInputFieldProps {
  value: string;
  isMasked?: boolean;
  showEye?: boolean;
  showCopy?: boolean;
  showExternal?: boolean;
  className?: string;
  inputClassName?: string;
  iconsClassName?: string;
  placeholder?: string;
}

export const IntegrationInputField: React.FC<IntegrationInputFieldProps> = ({
  isMasked = false,
  value,
  showEye = true,
  showCopy = true,
  showExternal = true,
  className,
  placeholder = '',
  inputClassName = '',
  iconsClassName = '',
}) => {
  const styles = useStyles2(getIntegrationInputFieldStyles);
  const [isInputMasked, setIsMasked] = useState(isMasked);

  return (
    <div className={cx(styles.root, { [className]: !!className })}>
      <div className={styles.inputContainer}>{renderInputField()}</div>

      <div className={cx(styles.icons, iconsClassName)}>
        <Stack gap={StackSize.xs}>
          {showEye && <IconButton aria-label="Reveal" name={'eye'} size={'xs'} onClick={onInputReveal} />}
          {showCopy && <CopyToClipboardIcon text={value} iconButtonProps={{ size: 'xs' }} />}
          {showExternal && <IconButton aria-label="Open" name={'external-link-alt'} size={'xs'} onClick={onOpen} />}
        </Stack>
      </div>
    </div>
  );

  function renderInputField() {
    return (
      <Input
        className={cx(inputClassName)}
        value={isInputMasked ? value?.replace(/./g, '*') : value}
        placeholder={placeholder}
        disabled
      />
    );
  }

  function onInputReveal() {
    setIsMasked(!isInputMasked);
  }

  function onOpen() {
    window.open(value, '_blank');
  }
};
