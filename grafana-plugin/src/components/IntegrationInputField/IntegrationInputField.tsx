import React, { useState } from 'react';

import { HorizontalGroup, IconButton, Input } from '@grafana/ui';
import cn from 'classnames/bind';

import { CopyToClipboardIcon } from 'components/CopyToClipboardIcon/CopyToClipboardIcon';

import styles from './IntegrationInputField.module.scss';

interface IntegrationInputFieldProps {
  value: string;
  isMasked?: boolean;
  showEye?: boolean;
  showCopy?: boolean;
  showExternal?: boolean;
  className?: string;
  inputClassName?: string;
  iconsClassName?: string;
}

const cx = cn.bind(styles);

export const IntegrationInputField: React.FC<IntegrationInputFieldProps> = ({
  isMasked = false,
  value,
  showEye = true,
  showCopy = true,
  showExternal = true,
  className,
  inputClassName = '',
  iconsClassName = '',
}) => {
  const [isInputMasked, setIsMasked] = useState(isMasked);

  return (
    <div className={cx('root', { [className]: !!className })}>
      <div className={cx('input-container')}>{renderInputField()}</div>

      <div className={cx('icons', iconsClassName)}>
        <HorizontalGroup spacing={'xs'}>
          {showEye && <IconButton aria-label="Reveal" name={'eye'} size={'xs'} onClick={onInputReveal} />}
          {showCopy && <CopyToClipboardIcon text={value} iconButtonProps={{ size: 'xs' }} />}
          {showExternal && <IconButton aria-label="Open" name={'external-link-alt'} size={'xs'} onClick={onOpen} />}
        </HorizontalGroup>
      </div>
    </div>
  );

  function renderInputField() {
    return <Input className={inputClassName} value={isInputMasked ? value?.replace(/./g, '*') : value} disabled />;
  }

  function onInputReveal() {
    setIsMasked(!isInputMasked);
  }

  function onOpen() {
    window.open(value, '_blank');
  }
};
